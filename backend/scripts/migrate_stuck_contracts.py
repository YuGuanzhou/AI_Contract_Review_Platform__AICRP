"""
一次性数据迁移：修复旧版本遗留的卡死合同状态

背景：
- 旧代码 AI 审核完成后未把状态从 ai_pending 流转到 manual_pending，导致合同卡死，
  无法进入审核工作台（其筛选条件是 AI_REVIEWED / MANUAL_PENDING）。
- 上传后台自动审核在 AI 调用中断时（如进程重启）也可能停留在过渡态 ai_pending。

迁移规则：
- ai_reviewed  → manual_pending   （AI 已审核完，进入人工审核队列）
- ai_pending + 存在 is_ai_reviewed=True 的审核记录 → manual_pending（AI 其实完成了，只是状态没流转）
- ai_pending + 无审核记录                     → parsed        （AI 未完成，回退到已解析，可重新触发 AI 审核）

用法：
    cd backend
    ../.venv/Scripts/python.exe -m scripts.migrate_stuck_contracts
"""
import asyncio
import logging

from sqlalchemy import text

from app.core.database import AsyncSessionLocal

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# 规则 1: ai_reviewed → manual_pending
UPDATE_AI_REVIEWED = """
    UPDATE contracts
    SET status = 'manual_pending'
    WHERE status = 'ai_reviewed'
"""

# 规则 2: ai_pending + 已有 AI 审核记录 → manual_pending
UPDATE_AI_PENDING_WITH_RECORD = """
    UPDATE contracts c
    JOIN (
        SELECT contract_id, MAX(is_ai_reviewed) AS has_ai
        FROM contract_reviews
        GROUP BY contract_id
    ) cr ON cr.contract_id = c.id
    SET c.status = 'manual_pending'
    WHERE c.status = 'ai_pending' AND cr.has_ai = 1
"""

# 规则 3: ai_pending + 无审核记录 → parsed（可重新触发 AI）
UPDATE_AI_PENDING_NO_RECORD = """
    UPDATE contracts c
    LEFT JOIN (
        SELECT contract_id, MAX(is_ai_reviewed) AS has_ai
        FROM contract_reviews
        GROUP BY contract_id
    ) cr ON cr.contract_id = c.id
    SET c.status = 'parsed'
    WHERE c.status = 'ai_pending' AND cr.contract_id IS NULL
"""


async def run() -> None:
    async with AsyncSessionLocal() as db:
        # 迁移前快照
        before = await db.execute(text(
            "SELECT status, COUNT(*) FROM contracts GROUP BY status"
        ))
        print("=== 迁移前状态分布 ===")
        for row in before.fetchall():
            print(f"  {row[0]}: {row[1]}")

        n1 = (await db.execute(text(UPDATE_AI_REVIEWED))).rowcount
        n2 = (await db.execute(text(UPDATE_AI_PENDING_WITH_RECORD))).rowcount
        n3 = (await db.execute(text(UPDATE_AI_PENDING_NO_RECORD))).rowcount
        await db.commit()

        print(f"\n迁移完成：ai_reviewed→manual_pending {n1} 条, "
              f"ai_pending(有AI记录)→manual_pending {n2} 条, "
              f"ai_pending(无记录)→parsed {n3} 条")

        after = await db.execute(text(
            "SELECT status, COUNT(*) FROM contracts GROUP BY status"
        ))
        print("\n=== 迁移后状态分布 ===")
        for row in after.fetchall():
            print(f"  {row[0]}: {row[1]}")


if __name__ == "__main__":
    asyncio.run(run())
