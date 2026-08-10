"""
统计和仪表板相关路由
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, and_, or_

from app.core.database import get_db
from app.core.security import get_current_user_dependency
from app.models.user import User
from app.models.contract import Contract, ContractStatus, ContractType, ContractReview

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    获取仪表板统计信息
    """
    # 根据用户角色决定查询范围
    if current_user.role in ["admin", "reviewer"]:
        user_filter = None  # 管理员和审核员可以查看所有数据
    else:
        user_filter = Contract.user_id == current_user.id
    
    try:
        # 合同总数统计
        total_query = select(func.count()).select_from(Contract)
        if user_filter:
            total_query = total_query.where(user_filter)
        
        total_result = await db.execute(total_query)
        total_contracts = total_result.scalar() or 0
        
        # 按状态统计
        status_stats = {}
        for status in ContractStatus:
            status_query = select(func.count()).select_from(Contract).where(Contract.status == status)
            if user_filter:
                status_query = status_query.where(user_filter)
            
            status_result = await db.execute(status_query)
            status_stats[status.value] = status_result.scalar() or 0
        
        # 按类型统计
        type_stats = {}
        for contract_type in ContractType:
            type_query = select(func.count()).select_from(Contract).where(Contract.contract_type == contract_type)
            if user_filter:
                type_query = type_query.where(user_filter)
            
            type_result = await db.execute(type_query)
            type_stats[contract_type.value] = type_result.scalar() or 0
        
        # 风险统计
        risk_query = select(
            Contract.risk_level,
            func.count().label('count'),
            func.avg(Contract.risk_score).label('avg_score')
        ).group_by(Contract.risk_level)
        
        if user_filter:
            risk_query = risk_query.where(user_filter)
        
        risk_result = await db.execute(risk_query)
        risk_stats = []
        for row in risk_result:
            if row.risk_level:
                risk_stats.append({
                    "risk_level": row.risk_level,
                    "count": row.count,
                    "avg_score": float(row.avg_score) if row.avg_score else 0
                })
        
        # 最近上传的合同
        recent_query = select(Contract).order_by(Contract.uploaded_at.desc()).limit(5)
        if user_filter:
            recent_query = recent_query.where(user_filter)
        
        recent_result = await db.execute(recent_query)
        recent_contracts = recent_result.scalars().all()
        
        # 高风险合同
        high_risk_query = select(Contract).where(
            Contract.risk_level == "high"
        ).order_by(Contract.risk_score.desc()).limit(5)
        
        if user_filter:
            high_risk_query = high_risk_query.where(user_filter)
        
        high_risk_result = await db.execute(high_risk_query)
        high_risk_contracts = high_risk_result.scalars().all()
        
        # 审核统计
        review_stats_query = select(
            func.count().label('total_reviews'),
            func.sum(func.cast(ContractReview.is_ai_reviewed, Integer)).label('ai_reviews'),
            func.sum(func.cast(ContractReview.is_manual_reviewed, Integer)).label('manual_reviews'),
            func.sum(func.cast(ContractReview.is_finalized, Integer)).label('finalized_reviews')
        ).select_from(ContractReview)
        
        if user_filter:
            # 对于普通用户，只统计他们自己的审核
            review_stats_query = review_stats_query.where(ContractReview.user_id == current_user.id)
        
        review_stats_result = await db.execute(review_stats_query)
        review_stats_row = review_stats_result.first()
        
        review_stats = {
            "total_reviews": review_stats_row.total_reviews or 0,
            "ai_reviews": review_stats_row.ai_reviews or 0,
            "manual_reviews": review_stats_row.manual_reviews or 0,
            "finalized_reviews": review_stats_row.finalized_reviews or 0
        }
        
        # 月度趋势（简化版，按月份统计）
        monthly_trend_query = text("""
            SELECT 
                DATE_FORMAT(uploaded_at, '%Y-%m') as month,
                COUNT(*) as count,
                AVG(risk_score) as avg_risk_score
            FROM contracts
            WHERE uploaded_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(uploaded_at, '%Y-%m')
            ORDER BY month
        """)
        
        monthly_result = await db.execute(monthly_trend_query)
        monthly_trend = []
        for row in monthly_result:
            monthly_trend.append({
                "month": row.month,
                "count": row.count,
                "avg_risk_score": float(row.avg_risk_score) if row.avg_risk_score else 0
            })
        
        return {
            "summary": {
                "total_contracts": total_contracts,
                "total_reviews": review_stats["total_reviews"],
                "avg_risk_score": sum(item["avg_score"] * item["count"] for item in risk_stats) / sum(item["count"] for item in risk_stats) if risk_stats else 0,
                "high_risk_count": sum(1 for item in risk_stats if item["risk_level"] == "high")
            },
            "status_distribution": status_stats,
            "type_distribution": type_stats,
            "risk_distribution": risk_stats,
            "review_stats": review_stats,
            "recent_contracts": [
                {
                    "id": contract.id,
                    "title": contract.title,
                    "status": contract.status.value,
                    "risk_level": contract.risk_level,
                    "uploaded_at": contract.uploaded_at.isoformat() if contract.uploaded_at else None
                }
                for contract in recent_contracts
            ],
            "high_risk_contracts": [
                {
                    "id": contract.id,
                    "title": contract.title,
                    "risk_score": contract.risk_score,
                    "risk_level": contract.risk_level,
                    "uploaded_at": contract.uploaded_at.isoformat() if contract.uploaded_at else None
                }
                for contract in high_risk_contracts
            ],
            "monthly_trend": monthly_trend
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取仪表板统计失败: {str(e)}"
        )


@router.get("/user-stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    获取用户个人统计信息
    """
    try:
        # 用户合同统计
        contract_stats_query = select(
            func.count().label('total'),
            func.sum(func.cast(Contract.status == ContractStatus.REVIEWED, Integer)).label('reviewed'),
            func.sum(func.cast(Contract.status == ContractStatus.PARSED, Integer)).label('parsed'),
            func.sum(func.cast(Contract.status == ContractStatus.ERROR, Integer)).label('error'),
            func.avg(Contract.risk_score).label('avg_risk_score')
        ).where(Contract.user_id == current_user.id)
        
        contract_stats_result = await db.execute(contract_stats_query)
        contract_stats_row = contract_stats_result.first()
        
        # 用户审核统计
        review_stats_query = select(
            func.count().label('total_reviews'),
            func.sum(func.cast(ContractReview.is_ai_reviewed, Integer)).label('ai_reviews'),
            func.sum(func.cast(ContractReview.is_manual_reviewed, Integer)).label('manual_reviews')
        ).where(ContractReview.user_id == current_user.id)
        
        review_stats_result = await db.execute(review_stats_query)
        review_stats_row = review_stats_result.first()
        
        # 最近活动
        recent_activity_query = select(Contract).where(
            Contract.user_id == current_user.id
        ).order_by(Contract.uploaded_at.desc()).limit(10)
        
        recent_activity_result = await db.execute(recent_activity_query)
        recent_activities = recent_activity_result.scalars().all()
        
        return {
            "contract_stats": {
                "total": contract_stats_row.total or 0,
                "reviewed": contract_stats_row.reviewed or 0,
                "parsed": contract_stats_row.parsed or 0,
                "error": contract_stats_row.error or 0,
                "avg_risk_score": float(contract_stats_row.avg_risk_score) if contract_stats_row.avg_risk_score else 0
            },
            "review_stats": {
                "total_reviews": review_stats_row.total_reviews or 0,
                "ai_reviews": review_stats_row.ai_reviews or 0,
                "manual_reviews": review_stats_row.manual_reviews or 0
            },
            "recent_activities": [
                {
                    "id": contract.id,
                    "title": contract.title,
                    "action": "uploaded" if contract.status == ContractStatus.UPLOADED else 
                             "parsed" if contract.status == ContractStatus.PARSED else
                             "reviewed" if contract.status == ContractStatus.REVIEWED else
                             "updated",
                    "status": contract.status.value,
                    "timestamp": contract.uploaded_at.isoformat() if contract.uploaded_at else None,
                    "risk_level": contract.risk_level
                }
                for contract in recent_activities
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户统计失败: {str(e)}"
        )


@router.get("/admin/stats")
async def get_admin_stats(
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    获取管理员统计信息（仅管理员可访问）
    """
    # 检查权限
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    try:
        # 用户统计
        user_stats_query = select(
            User.role,
            func.count().label('count'),
            func.max(User.created_at).label('latest_created')
        ).group_by(User.role)
        
        user_stats_result = await db.execute(user_stats_query)
        user_stats = []
        for row in user_stats_result:
            user_stats.append({
                "role": row.role,
                "count": row.count,
                "latest_created": row.latest_created.isoformat() if row.latest_created else None
            })
        
        # 系统使用统计
        system_stats_query = text("""
            SELECT 
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM contracts) as total_contracts,
                (SELECT COUNT(*) FROM contract_reviews) as total_reviews,
                (SELECT AVG(risk_score) FROM contracts WHERE risk_score IS NOT NULL) as avg_system_risk_score,
                (SELECT COUNT(*) FROM contracts WHERE risk_level = 'high') as high_risk_contracts
        """)
        
        system_stats_result = await db.execute(system_stats_query)
        system_stats_row = system_stats_result.first()
        
        # 活跃用户（最近30天有活动的用户）
        active_users_query = text("""
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM (
                SELECT user_id FROM contracts WHERE uploaded_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                UNION
                SELECT user_id FROM contract_reviews WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            ) as recent_activity
        """)
        
        active_users_result = await db.execute(active_users_query)
        active_users_row = active_users_result.first()
        
        # 存储使用统计
        storage_stats_query = text("""
            SELECT 
                SUM(file_size) as total_storage_bytes,
                AVG(file_size) as avg_file_size,
                COUNT(*) as total_files
            FROM contracts 
            WHERE file_size IS NOT NULL
        """)
        
        storage_stats_result = await db.execute(storage_stats_query)
        storage_stats_row = storage_stats_result.first()
        
        return {
            "user_distribution": user_stats,
            "system_overview": {
                "total_users": system_stats_row.total_users or 0,
                "total_contracts": system_stats_row.total_contracts or 0,
                "total_reviews": system_stats_row.total_reviews or 0,
                "avg_system_risk_score": float(system_stats_row.avg_system_risk_score) if system_stats_row.avg_system_risk_score else 0,
                "high_risk_contracts": system_stats_row.high_risk_contracts or 0,
                "active_users": active_users_row.active_users or 0
            },
            "storage_usage": {
                "total_storage_bytes": storage_stats_row.total_storage_bytes or 0,
                "total_storage_mb": (storage_stats_row.total_storage_bytes or 0) / (1024 * 1024),
                "avg_file_size": storage_stats_row.avg_file_size or 0,
                "total_files": storage_stats_row.total_files or 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取管理员统计失败: {str(e)}"
        )


# 导入必要的类型
from sqlalchemy import Integer