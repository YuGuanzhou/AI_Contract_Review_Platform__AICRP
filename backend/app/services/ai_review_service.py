"""
AI 审核服务 - 统一 AI 审核落库流程

历史问题：review.py 的 ai_review_contract 与 reviewer.py 的 start_contract_review
各有一套「调 AI → 建审核记录 → 改状态」逻辑，导致：
- 查重条件不一致（reviewer.py 按 contract_id + user_id，后台自动审核记录 user_id
  是合同所有者，导致重复创建审核记录）
- 状态流转不一致（reviewer.py 停留在 AI_REVIEWED，合同进不了人工审核队列）

本模块将「AI 审核 → 幂等落库 → 合同状态流转」收敛为唯一实现，供各路由复用。
"""
import logging
from typing import Dict, Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models.contract import Contract, ContractStatus, ContractReview
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)


async def run_ai_review(
    db: AsyncSession,
    contract: Contract,
    user_id: int,
) -> Dict[str, Any]:
    """
    执行 AI 审核并幂等落库。

    Args:
        db: 数据库会话
        contract: 合同（需已解析，含 parsed_text）
        user_id: 触发审核的用户 ID（用于创建记录时标记）

    Returns:
        {"success": True, "ai_result": ai_result, "review": review}
        或 {"success": False, "error": "..."}
    """
    # 1. 调用 AI 服务审核合同
    ai_result = await ai_service.review_contract(
        contract_text=contract.parsed_text,
        contract_type=contract.contract_type.value,
    )
    if not ai_result.get("success", False):
        return {"success": False, "error": ai_result.get("error", "未知错误")}

    review_result = ai_result.get("review_result", {})

    # 2. 复用该合同最新一条审核记录（按 contract_id 查，
    #    兼容上传后台自动审核记录 user_id = contract.user_id 的情况）
    existing = await db.execute(
        select(ContractReview)
        .where(ContractReview.contract_id == contract.id)
        .order_by(desc(ContractReview.id))
        .limit(1)
    )
    existing = existing.scalar_one_or_none()

    if existing:
        review = existing
        review.ai_review_result = review_result
        review.risk_points = review_result.get("specific_risks", [])
        review.suggestions = review_result.get("modification_suggestions", {})
        review.is_ai_reviewed = True
        review.ai_reviewed_at = func.now()
    else:
        review = ContractReview(
            contract_id=contract.id,
            user_id=user_id,
            ai_review_result=review_result,
            risk_points=review_result.get("specific_risks", []),
            suggestions=review_result.get("modification_suggestions", {}),
            is_ai_reviewed=True,
            ai_reviewed_at=func.now(),
        )
        db.add(review)

    # 3. 更新合同风险信息
    contract.risk_score = ai_result.get("risk_score", 0)
    contract.risk_level = ai_result.get("risk_level", "unknown")
    contract.review_summary = ai_result.get("summary", "")

    # 4. AI 审核完成 → 流转到人工审核队列（防止卡死在 ai_pending/ai_reviewed）
    if contract.status in (
        ContractStatus.PARSED,
        ContractStatus.AI_PENDING,
        ContractStatus.AI_REVIEWED,
    ):
        contract.status = ContractStatus.MANUAL_PENDING
    contract.reviewed_at = func.now()

    await db.commit()
    await db.refresh(review)

    return {"success": True, "ai_result": ai_result, "review": review}
