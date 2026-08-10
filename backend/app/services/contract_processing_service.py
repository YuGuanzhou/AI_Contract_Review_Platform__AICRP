"""
合同处理服务 - 集成解析和AI审核
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contract, ContractStatus, ContractReview
from app.services.parser_service import ParserService
from app.services.ai_service import AIService
from app.services.file_service import FileService
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class ContractProcessingService:
    """合同处理服务，集成解析和AI审核"""
    
    def __init__(self):
        self.parser_service = ParserService()
        self.ai_service = AIService()
        self.file_service = FileService()
    
    async def process_contract(self, contract_id: int, db: AsyncSession) -> Dict[str, Any]:
        """
        处理合同：解析文件并进行AI审核
        
        Args:
            contract_id: 合同ID
            db: 数据库会话
            
        Returns:
            处理结果字典
        """
        try:
            # 获取合同
            contract = await db.get(Contract, contract_id)
            if not contract:
                return {"success": False, "error": "合同不存在"}
            
            # 更新状态为解析中
            contract.status = ContractStatus.PARSING
            await db.commit()
            
            # 1. 解析合同文件
            logger.info(f"开始解析合同 {contract_id}: {contract.title}")
            
            # 获取文件内容
            file_content = await self.file_service.get_file_content(contract.file_path)
            
            # 创建临时文件
            import tempfile
            import os
            file_ext = os.path.splitext(contract.original_filename)[1].lower() if contract.original_filename else '.pdf'
            with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name
            
            try:
                parse_result = await self.parser_service.parse_contract(tmp_path)
            finally:
                # 删除临时文件
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
            
            if not parse_result.get("success"):
                contract.status = ContractStatus.ERROR
                await db.commit()
                return {"success": False, "error": f"解析失败: {parse_result.get('error')}"}
            
            # 更新解析结果
            contract.parsed_text = parse_result.get("text", "")
            contract.parsed_json = parse_result.get("structured_data", {})
            contract.page_count = parse_result.get("page_count", 0)
            contract.word_count = parse_result.get("word_count", 0)
            contract.parsed_at = datetime.now()
            contract.status = ContractStatus.PARSED
            await db.commit()
            
            logger.info(f"合同 {contract_id} 解析完成，开始AI审核")
            
            # 2. AI审核合同
            contract.status = ContractStatus.AI_PENDING
            await db.commit()
            
            ai_review_result = await self.ai_service.review_contract(
                contract_text=contract.parsed_text,
                contract_type=contract.contract_type.value
            )
            
            if not ai_review_result.get("success"):
                contract.status = ContractStatus.ERROR
                await db.commit()
                return {"success": False, "error": f"AI审核失败: {ai_review_result.get('error')}"}
            
            # 更新AI审核结果
            contract.risk_score = ai_review_result.get("risk_score", 0)
            contract.risk_level = ai_review_result.get("risk_level", "unknown")
            contract.review_summary = ai_review_result.get("summary", "")
            contract.reviewed_at = datetime.now()
            contract.status = ContractStatus.MANUAL_PENDING
            await db.commit()
            
            # 3. 创建审核记录
            review_record = ContractReview(
                contract_id=contract.id,
                user_id=contract.user_id,
                ai_review_result=ai_review_result.get("review_result", {}),
                risk_points=ai_review_result.get("review_result", {}).get("specific_risks", []),
                suggestions=ai_review_result.get("review_result", {}).get("modification_suggestions", {}),
                is_ai_reviewed=True,
                is_manual_reviewed=False,
                is_finalized=False
            )
            
            db.add(review_record)
            await db.commit()
            
            logger.info(f"合同 {contract_id} AI审核完成，风险等级: {contract.risk_level}, 评分: {contract.risk_score}")
            
            return {
                "success": True,
                "contract_id": contract_id,
                "parse_result": parse_result,
                "ai_review_result": ai_review_result,
                "risk_score": contract.risk_score,
                "risk_level": contract.risk_level,
                "summary": contract.review_summary
            }
            
        except Exception as e:
            logger.error(f"处理合同 {contract_id} 失败: {e}", exc_info=True)
            
            # 更新合同状态为错误
            try:
                contract = await db.get(Contract, contract_id)
                if contract:
                    contract.status = ContractStatus.ERROR
                    await db.commit()
            except Exception:
                pass
            
            return {"success": False, "error": str(e)}
    
    async def process_contract_async(self, contract_id: int):
        """
        异步处理合同（在后台运行）
        
        Args:
            contract_id: 合同ID
        """
        try:
            logger.info(f"启动异步处理合同 {contract_id}")
            # 这里可以集成到任务队列（如Celery、RQ等）
            # 目前使用简单的异步任务
            asyncio.create_task(self._process_contract_background(contract_id))
        except Exception as e:
            logger.error(f"启动异步处理失败: {e}")
    
    async def _process_contract_background(self, contract_id: int):
        """
        后台处理合同
        """
        # 创建新的数据库会话
        async with AsyncSessionLocal() as db:
            try:
                result = await self.process_contract(contract_id, db)
                if result["success"]:
                    logger.info(f"后台处理合同 {contract_id} 成功")
                else:
                    logger.error(f"后台处理合同 {contract_id} 失败: {result.get('error')}")
            except Exception as e:
                logger.error(f"后台处理合同 {contract_id} 异常: {e}")
    
    async def get_contract_review_details(self, contract_id: int, db: AsyncSession) -> Dict[str, Any]:
        """
        获取合同审核详情
        
        Args:
            contract_id: 合同ID
            db: 数据库会话
            
        Returns:
            审核详情字典
        """
        try:
            # 获取合同
            contract = await db.get(Contract, contract_id)
            if not contract:
                return {"success": False, "error": "合同不存在"}
            
            # 获取最新的审核记录
            from sqlalchemy import select, desc
            query = select(ContractReview).where(
                ContractReview.contract_id == contract_id
            ).order_by(desc(ContractReview.id)).limit(1)
            
            result = await db.execute(query)
            review_record = result.scalar_one_or_none()
            
            if not review_record:
                return {
                    "success": True,
                    "contract_id": contract_id,
                    "status": contract.status,
                    "risk_score": contract.risk_score,
                    "risk_level": contract.risk_level,
                    "review_summary": contract.review_summary,
                    "has_ai_review": False,
                    "ai_review_result": None,
                    "risk_points": [],
                    "suggestions": []
                }
            
            return {
                "success": True,
                "contract_id": contract_id,
                "status": contract.status,
                "risk_score": contract.risk_score,
                "risk_level": contract.risk_level,
                "review_summary": contract.review_summary,
                "has_ai_review": review_record.is_ai_reviewed,
                "ai_review_result": review_record.ai_review_result,
                "risk_points": review_record.risk_points or [],
                "suggestions": review_record.suggestions or [],
                "reviewed_at": contract.reviewed_at
            }
            
        except Exception as e:
            logger.error(f"获取合同审核详情失败: {e}")
            return {"success": False, "error": str(e)}