"""
用户相关路由
提供用户个人页面所需的所有功能
"""
from __future__ import annotations
import os
from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_, or_
from sqlalchemy.sql import text

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user_dependency
from app.models.user import User
from app.models.contract import Contract, ContractStatus, ContractType, ContractReview
from app.schemas.contract import (
    ContractResponse,
    ContractListResponse,
    ContractStatsResponse,
)

router = APIRouter()


@router.get("/contracts/stats", response_model=ContractStatsResponse)
async def get_user_contract_stats(
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户合同统计信息
    """
    try:
        from datetime import datetime, timedelta
        
        # 查询用户合同总数
        total_query = select(func.count()).select_from(Contract).where(Contract.user_id == current_user.id)
        total_result = await db.execute(total_query)
        total_contracts = total_result.scalar() or 0

        # 待审核合同数：状态为 pending 或 reviewing 的合同（根据前端映射）
        # 后端状态包括：uploaded, parsing, parsed, ai_pending, ai_reviewed, manual_pending, reviewed, archived, error
        # 映射到前端 pending: uploaded, parsing, parsed, ai_pending
        # 映射到前端 reviewing: ai_reviewed, manual_pending
        # 这里计算前端意义上的“待审核”（pending + reviewing）
        pending_statuses = ['uploaded', 'parsing', 'parsed', 'ai_pending', 'ai_reviewed', 'manual_pending']
        pending_query = select(func.count()).select_from(Contract).where(
            Contract.user_id == current_user.id,
            Contract.status.in_(pending_statuses)
        )
        pending_result = await db.execute(pending_query)
        pending_reviews = pending_result.scalar() or 0

        # 已通过合同数：状态为 reviewed 或 archived
        approved_statuses = ['reviewed', 'archived']
        approved_query = select(func.count()).select_from(Contract).where(
            Contract.user_id == current_user.id,
            Contract.status.in_(approved_statuses)
        )
        approved_result = await db.execute(approved_query)
        approved_contracts = approved_result.scalar() or 0

        # 高风险合同数：风险等级为 high
        high_risk_query = select(func.count()).select_from(Contract).where(
            Contract.user_id == current_user.id,
            Contract.risk_level == 'high'
        )
        high_risk_result = await db.execute(high_risk_query)
        high_risk_contracts = high_risk_result.scalar() or 0

        # 平均风险评分
        avg_risk_query = select(func.avg(Contract.risk_score)).where(
            Contract.user_id == current_user.id,
            Contract.risk_score.isnot(None)
        )
        avg_risk_result = await db.execute(avg_risk_query)
        avg_risk_score = float(avg_risk_result.scalar() or 0.0)

        # 近期合同数（最近7天）
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_query = select(func.count()).select_from(Contract).where(
            Contract.user_id == current_user.id,
            Contract.uploaded_at >= seven_days_ago
        )
        recent_result = await db.execute(recent_query)
        recent_contracts = recent_result.scalar() or 0

        # 调试日志
        print(f"[DEBUG] User {current_user.id} stats: total={total_contracts}, pending={pending_reviews}, approved={approved_contracts}, high_risk={high_risk_contracts}, avg_risk={avg_risk_score}, recent={recent_contracts}")

        return ContractStatsResponse(
            total_contracts=total_contracts,
            pending_reviews=pending_reviews,
            approved_contracts=approved_contracts,
            high_risk_contracts=high_risk_contracts,
            avg_risk_score=avg_risk_score,
            recent_contracts=recent_contracts
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户合同统计失败: {str(e)}"
        )




@router.get("/contracts/{contract_id}")
async def get_user_contract_detail(
    contract_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户合同详情
    """
    try:
        query = select(Contract).where(
            and_(
                Contract.id == contract_id,
                Contract.user_id == current_user.id
            )
        )
        result = await db.execute(query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="合同不存在或无权访问"
            )
        
        return ContractResponse.from_orm(contract)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取合同详情失败: {str(e)}"
        )


@router.delete("/contracts/{contract_id}")
async def delete_user_contract(
    contract_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    删除用户合同
    """
    try:
        # 查找合同
        query = select(Contract).where(
            and_(
                Contract.id == contract_id,
                Contract.user_id == current_user.id
            )
        )
        result = await db.execute(query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="合同不存在或无权删除"
            )
        
        # 删除文件（这里需要实现文件服务）
        # file_service = FileService()
        # await file_service.delete_contract_file(contract.file_path)
        
        # 删除数据库记录
        await db.delete(contract)
        await db.commit()
        
        return {"success": True, "message": "合同删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除合同失败: {str(e)}"
        )


@router.get("/contracts/{contract_id}/review-progress")
async def get_contract_review_progress(
    contract_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    获取合同审核进度
    """
    try:
        # 验证合同所有权
        contract_query = select(Contract).where(
            and_(
                Contract.id == contract_id,
                Contract.user_id == current_user.id
            )
        )
        contract_result = await db.execute(contract_query)
        contract = contract_result.scalar_one_or_none()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="合同不存在或无权访问"
            )
        
        # 获取审核记录
        review_query = select(ContractReview).where(
            ContractReview.contract_id == contract_id
        ).order_by(desc(ContractReview.created_at))
        
        review_result = await db.execute(review_query)
        reviews = review_result.scalars().all()
        
        # 构建审核进度
        steps = []
        status_map = {
            "pending": "待审核",
            "reviewing": "审核中",
            "approved": "已通过",
            "revision": "需修改",
            "rejected": "已拒绝"
        }
        
        # 基础步骤
        steps.append({
            "name": "合同上传",
            "status": "completed",
            "completed_at": contract.uploaded_at.isoformat() if contract.uploaded_at else None,
            "details": "合同文件已成功上传"
        })
        
        if contract.parsed_at:
            steps.append({
                "name": "AI解析",
                "status": "completed",
                "completed_at": contract.parsed_at.isoformat(),
                "details": "AI已完成合同内容解析"
            })
        
        if contract.risk_score is not None:
            steps.append({
                "name": "风险评估",
                "status": "completed",
                "completed_at": contract.parsed_at.isoformat() if contract.parsed_at else None,
                "details": f"风险评估完成，得分: {contract.risk_score}/10"
            })
        
        # 审核步骤
        if reviews:
            for review in reviews:
                steps.append({
                    "name": f"审核员审核 ({review.reviewer_name or '系统'})",
                    "status": "completed" if review.status == "completed" else "in_progress",
                    "completed_at": review.completed_at.isoformat() if review.completed_at else None,
                    "details": review.comments[:100] if review.comments else "审核中"
                })
        
        # 最终状态
        if contract.status in ["approved", "rejected", "revision"]:
            steps.append({
                "name": "审核完成",
                "status": "completed",
                "completed_at": contract.updated_at.isoformat() if contract.updated_at else None,
                "details": f"合同状态: {status_map.get(contract.status, contract.status)}"
            })
        else:
            steps.append({
                "name": "审核完成",
                "status": "pending",
                "details": "等待审核完成"
            })
        
        # 计算进度百分比
        completed_steps = sum(1 for step in steps if step["status"] == "completed")
        total_steps = len(steps)
        progress_percentage = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0
        
        return {
            "status": contract.status,
            "current_step": steps[-1]["name"] if steps else "未知",
            "progress_percentage": progress_percentage,
            "estimated_completion": None,  # 可以基于历史数据估算
            "reviewer": reviews[0].reviewer_name if reviews else None,
            "last_update": contract.updated_at.isoformat() if contract.updated_at else contract.uploaded_at.isoformat(),
            "steps": steps
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取审核进度失败: {str(e)}"
        )


@router.get("/contracts/{contract_id}/notifications")
async def get_contract_notifications(
    contract_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    获取合同相关通知
    """
    try:
        # 验证合同所有权
        contract_query = select(Contract).where(
            and_(
                Contract.id == contract_id,
                Contract.user_id == current_user.id
            )
        )
        contract_result = await db.execute(contract_query)
        contract = contract_result.scalar_one_or_none()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="合同不存在或无权访问"
            )
        
        # 这里应该从通知表中获取数据，暂时返回模拟数据
        notifications = [
            {
                "id": 1,
                "type": "status_change",
                "title": "合同状态更新",
                "message": f"合同 '{contract.title}' 的状态已更新为 '{contract.status}'",
                "created_at": contract.updated_at.isoformat() if contract.updated_at else contract.uploaded_at.isoformat(),
                "read": False,
                "action_url": f"/contracts/{contract_id}"
            }
        ]
        
        # 如果有审核记录，添加审核通知
        review_query = select(ContractReview).where(
            ContractReview.contract_id == contract_id
        ).order_by(desc(ContractReview.created_at))
        
        review_result = await db.execute(review_query)
        reviews = review_result.scalars().all()
        
        for i, review in enumerate(reviews[:3]):  # 只取最近3条
            if review.comments:
                notifications.append({
                    "id": i + 2,
                    "type": "comment",
                    "title": "审核员评论",
                    "message": f"审核员对合同 '{contract.title}' 发表了评论: {review.comments[:50]}...",
                    "created_at": review.created_at.isoformat(),
                    "read": False,
                    "action_url": f"/contracts/{contract_id}/review"
                })
        
        return {"data": notifications}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取通知失败: {str(e)}"
        )


@router.get("/contracts/export")
async def export_user_contracts(
    format: str = Query("excel", regex="^(excel|csv|pdf)$"),
    include_fields: List[str] = Query(["title", "status", "risk_score", "uploaded_at"]),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    导出用户合同数据
    """
    try:
        # 这里应该实现实际的导出逻辑
        # 暂时返回模拟数据
        
        return {
            "data": {
                "download_url": f"/api/user/contracts/export/download?token=temp_token",
                "format": format,
                "record_count": 0,  # 实际应该从查询中获取
                "generated_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出合同失败: {str(e)}"
        )


@router.post("/contracts/batch")
async def batch_user_contract_action(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    批量操作用户合同
    """
    try:
        contract_ids = data.get("contract_ids", [])
        action = data.get("action", "")
        parameters = data.get("parameters", {})
        
        if not contract_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请选择要操作的合同"
            )
        
        # 验证合同所有权
        query = select(Contract).where(
            and_(
                Contract.id.in_(contract_ids),
                Contract.user_id == current_user.id
            )
        )
        result = await db.execute(query)
        user_contracts = result.scalars().all()
        
        if len(user_contracts) != len(contract_ids):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="部分合同不存在或无权操作"
            )
        
        success_count = 0
        failed_contracts = []
        
        if action == "delete":
            for contract in user_contracts:
                try:
                    # 删除文件（这里需要实现文件服务）
                    # file_service = FileService()
                    # await file_service.delete_contract_file(contract.file_path)
                    
                    # 删除数据库记录
                    await db.delete(contract)
                    success_count += 1
                except Exception as e:
                    failed_contracts.append({
                        "contract_id": contract.id,
                        "title": contract.title,
                        "error": str(e)
                    })
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"成功删除 {success_count} 个合同",
                "data": {
                    "success_count": success_count,
                    "failed_count": len(failed_contracts),
                    "failed_contracts": failed_contracts
                }
            }
        
        elif action == "export":
            # 导出逻辑
            return {
                "success": True,
                "message": "批量导出请求已接收，请稍后查看导出结果",
                "data": {
                    "export_id": "temp_export_id",
                    "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
                }
            }
        
        elif action == "archive":
            # 归档逻辑
            for contract in user_contracts:
                contract.is_archived = True
                contract.archived_at = datetime.utcnow()
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"成功归档 {len(user_contracts)} 个合同",
                "data": {
                    "archived_count": len(user_contracts)
                }
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的操作类型: {action}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量操作失败: {str(e)}"
        )


@router.post("/contracts/{contract_id}/share")
async def create_share_link(
    contract_id: int,
    options: Dict[str, Any],
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    创建合同分享链接
    """
    try:
        # 验证合同所有权
        contract_query = select(Contract).where(
            and_(
                Contract.id == contract_id,
                Contract.user_id == current_user.id
            )
        )
        contract_result = await db.execute(contract_query)
        contract = contract_result.scalar_one_or_none()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="合同不存在或无权分享"
            )
        
        expires_in = options.get("expires_in", 24)  # 默认24小时
        password_protected = options.get("password_protected", False)
        view_only = options.get("view_only", True)
        
        # 生成分享链接（这里应该使用安全的token生成）
        import secrets
        share_token = secrets.token_urlsafe(32)
        
        # 计算过期时间
        expires_at = datetime.utcnow() + timedelta(hours=expires_in)
        
        # 这里应该将分享信息保存到数据库
        # 暂时返回模拟数据
        
        return {
            "data": {
                "share_url": f"{settings.FRONTEND_URL}/shared/{share_token}",
                "expires_at": expires_at.isoformat(),
                "access_code": secrets.token_hex(4) if password_protected else None,
                "view_only": view_only
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建分享链接失败: {str(e)}"
        )


@router.delete("/contracts/{contract_id}/share/{share_id}")
async def revoke_share_link(
    contract_id: int,
    share_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    撤销合同分享链接
    """
    try:
        # 验证合同所有权
        contract_query = select(Contract).where(
            and_(
                Contract.id == contract_id,
                Contract.user_id == current_user.id
            )
        )
        contract_result = await db.execute(contract_query)
        contract = contract_result.scalar_one_or_none()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="合同不存在或无权操作"
            )
        
        # 这里应该从数据库中删除分享记录
        # 暂时返回成功
        
        return {
            "data": {
                "success": True,
                "message": "分享链接已撤销"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"撤销分享链接失败: {str(e)}"
        )


@router.get("/contracts/{contract_id}/comments")
async def get_contract_comments(
    contract_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    获取合同评论
    """
    try:
        # 验证合同所有权
        contract_query = select(Contract).where(
            and_(
                Contract.id == contract_id,
                Contract.user_id == current_user.id
            )
        )
        contract_result = await db.execute(contract_query)
        contract = contract_result.scalar_one_or_none()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="合同不存在或无权访问"
            )
        
        # 这里应该从评论表中获取数据
        # 暂时返回模拟数据
        
        comments = [
            {
                "id": 1,
                "user_id": current_user.id,
                "username": current_user.username,
                "avatar": None,
                "content": "这是我对合同的评论",
                "created_at": datetime.utcnow().isoformat(),
                "is_owner": True,
                "replies": []
            }
        ]
        
        return {"data": comments}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取评论失败: {str(e)}"
        )


@router.post("/contracts/{contract_id}/comments")
async def add_contract_comment(
    contract_id: int,
    comment_data: Dict[str, Any],
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    添加合同评论
    """
    try:
        # 验证合同所有权
        contract_query = select(Contract).where(
            and_(
                Contract.id == contract_id,
                Contract.user_id == current_user.id
            )
        )
        contract_result = await db.execute(contract_query)
        contract = contract_result.scalar_one_or_none()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="合同不存在或无权评论"
            )
        
        content = comment_data.get("content", "").strip()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="评论内容不能为空"
            )
        
        # 这里应该将评论保存到数据库
        # 暂时返回模拟数据
        
        return {
            "data": {
                "id": 999,
                "content": content,
                "created_at": datetime.utcnow().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加评论失败: {str(e)}"
        )


@router.delete("/contracts/{contract_id}/comments/{comment_id}")
async def delete_contract_comment(
    contract_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    删除合同评论
    """
    try:
        # 验证合同所有权
        contract_query = select(Contract).where(
            and_(
                Contract.id == contract_id,
                Contract.user_id == current_user.id
            )
        )
        contract_result = await db.execute(contract_query)
        contract = contract_result.scalar_one_or_none()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="合同不存在或无权操作"
            )
        
        # 这里应该从数据库中删除评论
        # 暂时返回成功
        
        return {
            "data": {
                "success": True,
                "message": "评论删除成功"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除评论失败: {str(e)}"
        )


@router.get("/contracts/{contract_id}/versions")
async def get_contract_versions(
    contract_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    获取合同版本历史
    """
    try:
        # 验证合同所有权
        contract_query = select(Contract).where(
            and_(
                Contract.id == contract_id,
                Contract.user_id == current_user.id
            )
        )
        contract_result = await db.execute(contract_query)
        contract = contract_result.scalar_one_or_none()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="合同不存在或无权访问"
            )
        
        # 这里应该从版本历史表中获取数据
        # 暂时返回模拟数据
        
        versions = [
            {
                "version": 1,
                "created_at": contract.uploaded_at.isoformat(),
                "file_size": contract.file_size or 0,
                "changes": ["初始版本"],
                "uploaded_by": current_user.username,
                "download_url": f"/api/user/contracts/{contract_id}/download"
            }
        ]
        
        return {"data": versions}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取版本历史失败: {str(e)}"
        )


@router.post("/contracts/{contract_id}/versions/{version}/restore")
async def restore_contract_version(
    contract_id: int,
    version: int,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    恢复到指定合同版本
    """
    try:
        # 验证合同所有权
        contract_query = select(Contract).where(
            and_(
                Contract.id == contract_id,
                Contract.user_id == current_user.id
            )
        )
        contract_result = await db.execute(contract_query)
        contract = contract_result.scalar_one_or_none()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="合同不存在或无权操作"
            )
        
        # 这里应该实现版本恢复逻辑
        # 暂时返回成功
        
        return {
            "data": {
                "success": True,
                "message": f"已成功恢复到版本 {version}"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢复版本失败: {str(e)}"
        )