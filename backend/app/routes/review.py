"""
合同审核相关路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, text

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.contract import Contract, ContractReview, ContractStatus
from app.schemas.contract import (
    ContractReviewResponse,
    ContractReviewCreateRequest,
    ContractReviewUpdateRequest,
    ContractReviewListResponse,
    AIReviewRequest,
    AIReviewResponse,
)
from app.services.ai_review_service import run_ai_review

router = APIRouter()


@router.post("/{contract_id}/review", response_model=ContractReviewResponse)
async def create_contract_review(
    contract_id: int,
    request: ContractReviewCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    创建合同审核记录
    """
    # 获取合同
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同不存在"
        )
    
    # 检查权限
    if current_user.role not in ["admin", "reviewer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权审核此合同"
        )
    
    # 检查合同状态
    if contract.status not in [ContractStatus.PARSED, ContractStatus.AI_REVIEWED, ContractStatus.MANUAL_PENDING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="合同状态不支持审核，请先完成解析"
        )
    
    # 创建/更新审核记录：复用该合同最新一条已有记录（通常是 AI 审核记录），
    # 将人工审核结果合并进去，避免 review-details 取到无 AI 数据的空记录
    existing_review = await db.execute(
        select(ContractReview).where(
            ContractReview.contract_id == contract_id
        ).order_by(desc(ContractReview.id)).limit(1)
    )
    existing_review = existing_review.scalar_one_or_none()

    manual_review_result = request.manual_review_result or {}
    final_result = {}
    if existing_review and existing_review.ai_review_result:
        final_result["ai_review"] = existing_review.ai_review_result
    if manual_review_result:
        final_result["manual_review"] = manual_review_result

    if existing_review:
        # 更新现有记录，保留 AI 结果，补充人工结果
        review = existing_review
        review.manual_review_result = manual_review_result or review.manual_review_result
        if request.risk_points is not None:
            review.risk_points = request.risk_points
        if request.suggestions is not None:
            review.suggestions = request.suggestions
        review.is_manual_reviewed = True
        review.manual_reviewed_at = func.now() if hasattr(func, 'now') else None
        review.is_finalized = True
        review.finalized_at = func.now() if hasattr(func, 'now') else None
        review.final_review_result = final_result or None
    else:
        # 无历史记录，新建
        review = ContractReview(
            contract_id=contract_id,
            user_id=current_user.id,
            manual_review_result=manual_review_result,
            risk_points=request.risk_points,
            suggestions=request.suggestions,
            is_manual_reviewed=True,
            manual_reviewed_at=func.now() if hasattr(func, 'now') else None,
            is_finalized=True,
            finalized_at=func.now() if hasattr(func, 'now') else None,
            final_review_result=final_result or None
        )
        db.add(review)
    
    # 更新合同状态
    contract.status = ContractStatus.REVIEWED
    contract.reviewed_at = func.now() if hasattr(func, 'now') else None
    
    # 如果有风险评分，更新到合同
    if request.risk_score is not None:
        contract.risk_score = request.risk_score
        contract.risk_level = request.risk_level
    
    if request.review_summary:
        contract.review_summary = request.review_summary
    
    await db.commit()
    await db.refresh(review)
    
    return ContractReviewResponse.from_orm(review)


@router.get("/{contract_id}/reviews", response_model=ContractReviewListResponse)
async def get_contract_reviews(
    contract_id: int,
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    获取合同的审核记录列表
    """
    # 获取合同
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同不存在"
        )
    
    # 检查权限
    if contract.user_id != current_user.id and current_user.role not in ["admin", "reviewer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此合同的审核记录"
        )
    
    # 查询审核记录
    query = select(ContractReview).where(
        ContractReview.contract_id == contract_id
    ).order_by(desc(ContractReview.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    reviews = result.scalars().all()
    
    # 获取总数
    count_query = select(func.count()).select_from(ContractReview).where(
        ContractReview.contract_id == contract_id
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    return ContractReviewListResponse(
        reviews=[ContractReviewResponse.from_orm(review) for review in reviews],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{contract_id}/reviews/{review_id}", response_model=ContractReviewResponse)
async def get_contract_review_detail(
    contract_id: int,
    review_id: int,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    获取单个审核记录详情
    """
    # 获取审核记录
    review = await db.get(ContractReview, review_id)
    if not review or review.contract_id != contract_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审核记录不存在"
        )
    
    # 获取合同
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同不存在"
        )
    
    # 检查权限
    if contract.user_id != current_user.id and current_user.role not in ["admin", "reviewer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此审核记录"
        )
    
    return ContractReviewResponse.from_orm(review)


@router.put("/{contract_id}/reviews/{review_id}", response_model=ContractReviewResponse)
async def update_contract_review(
    contract_id: int,
    review_id: int,
    request: ContractReviewUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    更新审核记录
    """
    # 获取审核记录
    review = await db.get(ContractReview, review_id)
    if not review or review.contract_id != contract_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审核记录不存在"
        )
    
    # 检查权限（审核员与管理员可修改，与其他端点权限规则一致）
    if review.user_id != current_user.id and current_user.role not in ["admin", "reviewer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此审核记录"
        )
    
    # 更新字段
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)
    
    await db.commit()
    await db.refresh(review)
    
    return ContractReviewResponse.from_orm(review)


@router.post("/{contract_id}/ai-review", response_model=AIReviewResponse)
async def ai_review_contract(
    contract_id: int,
    request: AIReviewRequest,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    AI 审核合同
    """
    # 获取合同
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同不存在"
        )

    # 检查权限
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

        ai_result = result["ai_result"]
        return AIReviewResponse(
            success=True,
            review_id=result["review"].id,
            risk_score=ai_result.get("risk_score", 0),
            risk_level=ai_result.get("risk_level", "unknown"),
            summary=ai_result.get("summary", ""),
            review_result=ai_result.get("review_result", {}),
            message="AI 审核完成"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 审核过程中发生错误: {str(e)}"
        )


@router.post("/{contract_id}/finalize-review")
async def finalize_contract_review(
    contract_id: int,
    review_id: int,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    最终确认审核结果
    """
    # 获取审核记录
    review = await db.get(ContractReview, review_id)
    if not review or review.contract_id != contract_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审核记录不存在"
        )
    
    # 检查权限（审核员与管理员可确认，与其他端点权限规则一致）
    if review.user_id != current_user.id and current_user.role not in ["admin", "reviewer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权确认此审核结果"
        )
    
    # 检查是否已完成审核
    if not review.is_ai_reviewed and not review.is_manual_reviewed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先完成 AI 审核或人工审核"
        )
    
    # 合并审核结果
    final_result = {}
    if review.ai_review_result:
        final_result.update({"ai_review": review.ai_review_result})
    if review.manual_review_result:
        final_result.update({"manual_review": review.manual_review_result})
    
    review.final_review_result = final_result
    review.is_finalized = True
    review.finalized_at = func.now() if hasattr(func, 'now') else None
    
    # 更新合同状态
    contract = await db.get(Contract, contract_id)
    if contract:
        contract.status = ContractStatus.REVIEWED
        contract.reviewed_at = func.now() if hasattr(func, 'now') else None
    
    await db.commit()
    
    return {
        "message": "审核结果已确认",
        "review_id": review.id,
        "contract_id": contract_id,
        "finalized_at": review.finalized_at
    }


@router.get("/stats/risk-distribution")
async def get_risk_distribution(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    获取风险分布统计
    """
    # 根据用户角色决定查询范围
    if current_user.role in ["admin", "reviewer"]:
        # 管理员和审核员可以查看所有合同
        query = """
            SELECT 
                risk_level,
                COUNT(*) as count,
                AVG(risk_score) as avg_score
            FROM contracts
            WHERE risk_level IS NOT NULL
            GROUP BY risk_level
            ORDER BY 
                CASE risk_level
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'low' THEN 3
                    ELSE 4
                END
        """
    else:
        # 普通用户只能查看自己的合同
        query = """
            SELECT 
                risk_level,
                COUNT(*) as count,
                AVG(risk_score) as avg_score
            FROM contracts
            WHERE user_id = :user_id AND risk_level IS NOT NULL
            GROUP BY risk_level
            ORDER BY 
                CASE risk_level
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'low' THEN 3
                    ELSE 4
                END
        """
    
    result = await db.execute(
        text(query),
        {"user_id": current_user.id}
    )
    
    distribution = []
    for row in result:
        distribution.append({
            "risk_level": row.risk_level,
            "count": row.count,
            "avg_score": float(row.avg_score) if row.avg_score else 0
        })
    
    return {
        "distribution": distribution,
        "total": sum(item["count"] for item in distribution)
    }
