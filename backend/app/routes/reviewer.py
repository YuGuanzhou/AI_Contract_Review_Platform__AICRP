"""
审核员工作台相关路由
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_, or_, text
from sqlalchemy.orm import selectinload, joinedload

from app.core.database import get_db
from app.core.security import get_current_user_dependency
from app.models.user import User
from app.models.contract import Contract, ContractStatus, ContractReview
from app.schemas.contract import ContractResponse
from app.services.ai_review_service import run_ai_review

router = APIRouter()


@router.get("/contracts/pending")
async def get_pending_contracts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    filter: Optional[str] = Query(None, description="筛选条件"),
    sort_by: Optional[str] = Query(None, description="排序字段"),
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    获取待审核的合同列表
    审核员和管理员可以查看所有待审核的合同（状态为 AI_REVIEWED 或 MANUAL_PENDING）
    返回格式与前端兼容
    """
    # 权限检查：仅审核员和管理员可以访问
    if current_user.role not in ["reviewer", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问审核工作台"
        )
    
    # 构建基础查询
    query = select(Contract).options(joinedload(Contract.user), selectinload(Contract.reviews)).where(
        Contract.status.in_([ContractStatus.AI_REVIEWED, ContractStatus.MANUAL_PENDING])
    )
    
    # 可选的状态筛选（暂不支持其他筛选）
    if filter:
        # 简单的标题搜索
        query = query.where(Contract.title.ilike(f"%{filter}%"))
    
    # 排序：默认按上传时间倒序
    if sort_by == "risk_score":
        query = query.order_by(desc(Contract.risk_score))
    elif sort_by == "uploaded_at":
        query = query.order_by(desc(Contract.uploaded_at))
    else:
        query = query.order_by(desc(Contract.uploaded_at))
    
    # 计算总数
    count_query = select(func.count()).select_from(Contract).where(
        Contract.status.in_([ContractStatus.AI_REVIEWED, ContractStatus.MANUAL_PENDING])
    )
    if filter:
        count_query = count_query.where(Contract.title.ilike(f"%{filter}%"))
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # 执行查询
    result = await db.execute(query)
    contracts = result.unique().scalars().all()
    
    # 转换为前端需要的格式
    now = datetime.now()
    items = []
    for contract in contracts:
        # 获取AI审核发现数量（真实数据：审核记录里的具体风险点）
        ai_findings_count = 0
        if contract.reviews:
            for review in contract.reviews:
                if review.risk_points and isinstance(review.risk_points, list):
                    ai_findings_count = len(review.risk_points)
                    break
                if review.ai_review_result and isinstance(review.ai_review_result, dict):
                    specific_risks = review.ai_review_result.get("specific_risks")
                    if isinstance(specific_risks, list):
                        ai_findings_count = len(specific_risks)
                        break

        # 等待时长：从 AI 审核完成（或上传）到现在的时长（小时）
        wait_base = contract.reviewed_at or contract.uploaded_at
        waiting_hours = 0
        if wait_base:
            try:
                waiting_hours = round((now - wait_base).total_seconds() / 3600, 1)
            except TypeError:
                waiting_hours = 0

        items.append({
            "id": contract.id,
            "contract_number": str(contract.id),  # 使用ID作为合同编号
            "contract_name": contract.title,
            "file_type": contract.file_type or "unknown",
            "file_size": contract.file_size or 0,
            "uploader": contract.user.full_name or contract.user.username,
            "uploader_company": contract.user.company or "",
            "risk_score": contract.risk_score or 0.0,
            "ai_findings_count": ai_findings_count,
            "created_at": contract.uploaded_at.isoformat() if contract.uploaded_at else "",
            "waiting_hours": waiting_hours,
            "is_urgent": False,
            "assigned_to": None,
            "contract_type": contract.contract_type.value if contract.contract_type else "other"
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/stats")
async def get_reviewer_stats(
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    获取审核员工作统计
    """
    if current_user.role not in ["reviewer", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问审核工作台"
        )
    
    # 统计待审核合同数量
    pending_query = select(func.count()).where(
        Contract.status.in_([ContractStatus.AI_REVIEWED, ContractStatus.MANUAL_PENDING])
    )
    pending_result = await db.execute(pending_query)
    pending_count = pending_result.scalar()
    
    # 统计已审核合同数量（由当前审核员审核的）
    reviewed_query = select(func.count()).select_from(ContractReview).where(
        ContractReview.user_id == current_user.id
    )
    reviewed_result = await db.execute(reviewed_query)
    reviewed_count = reviewed_result.scalar()
    
    return {
        "pending_count": pending_count,
        "reviewed_count": reviewed_count,
        "total_assigned": pending_count + reviewed_count
    }


@router.post("/contracts/{contract_id}/start-review")
async def start_contract_review(
    contract_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    开始审核合同 - 触发AI审核并返回审核详情
    """
    # 获取合同
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同不存在"
        )

    # 检查权限：审核员、管理员或合同所有者可以开始审核
    if contract.user_id != current_user.id and current_user.role not in ["admin", "reviewer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权审核此合同"
        )

    # 检查合同是否有解析内容
    if not contract.parsed_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="合同尚未解析，请先解析合同"
        )

    try:
        # 统一 AI 审核流程（幂等落库 + 状态流转到 MANUAL_PENDING）
        result = await run_ai_review(db, contract, current_user.id)
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI 审核失败: {result['error']}"
            )

        review = result["review"]
        ai_result = result["ai_result"]

        # 重新加载合同所有者关系（commit 后未加载，异步上下文禁止惰性加载）
        await db.refresh(contract, attribute_names=["user"])

        # 构建前端需要的审核详情格式
        ai_findings = []
        review_result = ai_result.get("review_result", {})
        specific_risks = review_result.get("specific_risks", [])
        for i, risk in enumerate(specific_risks):
            ai_findings.append({
                "id": i + 1,
                "type": risk.get("type", "risk"),
                "severity": risk.get("risk_level", "medium"),
                "description": risk.get("风险描述", "") or risk.get("risk_description", ""),
                "suggestion": risk.get("修改建议", "") or risk.get("modification_suggestion", ""),
                "confidence": 0.8,
                "clause_reference": risk.get("条款位置", "") or risk.get("clause_location", ""),
                "page_number": None
            })

        return {
            "id": review.id,
            "contract_id": contract.id,
            "contract_info": {
                "title": contract.title,
                "contract_number": str(contract.id),
                "uploader": (contract.user.full_name or contract.user.username) if contract.user else "",
                "upload_time": contract.uploaded_at.isoformat() if contract.uploaded_at else "",
                "file_type": contract.file_type,
                "file_size": contract.file_size
            },
            "ai_review": {
                "risk_score": ai_result.get("risk_score", 0),
                "findings": ai_findings,
                "summary": ai_result.get("summary", ""),
                "confidence": 0.9
            },
            "human_review": None,
            "comparison": None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"开始审核过程中发生错误: {str(e)}"
        )
