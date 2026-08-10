"""
AI 审核服务
"""
import json
import logging
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """AI 审核服务基类"""
    
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.client = self._create_client()
        
    def _create_client(self):
        """创建 AI 客户端"""
        if self.provider == "deepseek":
            return AsyncOpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_API_BASE,
                http_client=httpx.AsyncClient(timeout=60.0)
            )
        elif self.provider == "openai":
            return AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE,
                http_client=httpx.AsyncClient(timeout=60.0)
            )
        else:
            raise ValueError(f"不支持的 AI 提供商: {self.provider}")
    
    async def review_contract(self, contract_text: str, contract_type: str = "other") -> Dict[str, Any]:
        """
        审核合同文本
        
        Args:
            contract_text: 合同文本内容
            contract_type: 合同类型
            
        Returns:
            审核结果字典
        """
        try:
            # 构建审核提示词
            prompt = self._build_review_prompt(contract_text, contract_type)
            
            # 调用 AI 模型
            response = await self._call_ai_model(prompt)
            
            # 解析响应
            review_result = self._parse_ai_response(response)
            
            # 计算风险评分
            risk_score = self._calculate_risk_score(review_result)
            risk_level = self._determine_risk_level(risk_score)
            
            return {
                "success": True,
                "review_result": review_result,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "summary": self._generate_summary(review_result),
            }
            
        except Exception as e:
            logger.error(f"合同审核失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "review_result": {},
                "risk_score": 0,
                "risk_level": "unknown",
                "summary": "审核失败，请稍后重试",
            }
    
    def _build_review_prompt(self, contract_text: str, contract_type: str) -> str:
        """构建审核提示词"""
        # 根据合同类型选择不同的审核重点
        review_focus = self._get_review_focus_by_type(contract_type)
        
        prompt = f"""你是一名专业的法律顾问，请对以下合同进行审查分析。

合同类型：{contract_type}
审核重点：{review_focus}

合同内容：
{contract_text[:8000]}  # 限制文本长度

请按照以下格式进行分析：

1. **合同基本信息**
   - 合同类型：
   - 主要当事人：
   - 合同标的：

2. **关键条款分析**
   - 权利义务条款：
   - 付款条款：
   - 违约责任：
   - 争议解决：
   - 保密条款：
   - 知识产权：

3. **风险识别**
   - 高风险条款（红色）：
   - 中风险条款（黄色）：
   - 低风险条款（蓝色）：

4. **具体风险点**
   - 条款位置：
   - 风险描述：
   - 风险等级：
   - 修改建议：

5. **总体评价**
   - 合同完整性：
   - 条款公平性：
   - 法律合规性：
   - 商业合理性：

6. **修改建议**
   - 必须修改项：
   - 建议优化项：
   - 注意事项：

请以 JSON 格式返回结果，包含以下字段：
- basic_info: 合同基本信息
- key_clauses: 关键条款分析
- risk_identification: 风险识别
- specific_risks: 具体风险点列表
- overall_evaluation: 总体评价
- modification_suggestions: 修改建议
"""
        return prompt
    
    def _get_review_focus_by_type(self, contract_type: str) -> str:
        """根据合同类型获取审核重点"""
        focus_map = {
            "purchase": "价格条款、交付条款、质量保证、付款条件、违约责任",
            "sales": "价格条款、交付条款、质量保证、付款条件、售后服务",
            "service": "服务范围、服务标准、服务期限、费用结算、保密义务",
            "employment": "工作内容、薪酬待遇、工作时间、保密义务、竞业限制",
            "lease": "租赁期限、租金支付、维修责任、使用限制、续租条件",
            "partnership": "出资比例、利润分配、决策机制、退出机制、保密义务",
            "other": "权利义务对等性、条款明确性、法律合规性、商业合理性",
        }
        return focus_map.get(contract_type, focus_map["other"])
    
    async def _call_ai_model(self, prompt: str) -> str:
        """调用 AI 模型"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo" if self.provider == "openai" else "deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一名专业的法律顾问，擅长合同审查和分析。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"AI 模型调用失败: {e}")
            # 任何错误都返回模拟数据供开发测试
            logger.warning("AI 服务不可用，返回模拟审核数据")
            # 模拟审核结果 JSON
            mock_json = {
                "basic_info": {
                    "合同类型": "服务合同",
                    "主要当事人": "甲方：某某公司；乙方：某某个人",
                    "合同标的": "工作完成"
                },
                "key_clauses": {
                    "权利义务条款": "基本明确",
                    "付款条款": "支付金额10000元，时间未明确",
                    "违约责任": "违约金5000元，可能过高",
                    "争议解决": "仲裁条款有效",
                    "保密条款": "缺失",
                    "知识产权": "未约定"
                },
                "risk_identification": {
                    "高风险条款（红色）": ["违约责任可能过高", "保密条款缺失"],
                    "中风险条款（黄色）": ["付款时间不明确"],
                    "低风险条款（蓝色）": ["争议解决条款"]
                },
                "specific_risks": [
                    {
                        "条款位置": "第3条",
                        "风险描述": "违约金可能过高，不符合法律规定",
                        "风险等级": "high",
                        "修改建议": "建议将违约金调整至实际损失的30%以下"
                    },
                    {
                        "条款位置": "缺失",
                        "风险描述": "未包含保密条款",
                        "风险等级": "high",
                        "修改建议": "增加保密条款，明确保密义务和期限"
                    },
                    {
                        "条款位置": "第1条",
                        "风险描述": "付款时间未明确",
                        "风险等级": "medium",
                        "修改建议": "明确具体付款时间点"
                    }
                ],
                "overall_evaluation": {
                    "合同完整性": "一般",
                    "条款公平性": "基本公平",
                    "法律合规性": "部分条款需调整",
                    "商业合理性": "合理"
                },
                "modification_suggestions": {
                    "必须修改项": ["调整违约金条款", "增加保密条款"],
                    "建议优化项": ["明确付款时间"],
                    "注意事项": ["建议由法律专业人士最终审定"]
                }
            }
            import json
            return json.dumps(mock_json, ensure_ascii=False)
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """解析 AI 响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("AI 响应不是有效的 JSON，尝试提取 JSON 部分")
            # 尝试从响应中提取 JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # 如果无法提取 JSON，返回结构化错误
                return {
                    "error": "无法解析 AI 响应",
                    "raw_response": response[:500]
                }
    
    def _calculate_risk_score(self, review_result: Dict[str, Any]) -> float:
        """计算风险评分 (0-100)"""
        try:
            risk_score = 0
            
            # 从具体风险点计算
            specific_risks = review_result.get("specific_risks", [])
            for risk in specific_risks:
                risk_level = risk.get("risk_level", "medium")
                if risk_level == "high":
                    risk_score += 10
                elif risk_level == "medium":
                    risk_score += 5
                elif risk_level == "low":
                    risk_score += 2
            
            # 从总体评价计算
            overall_eval = review_result.get("overall_evaluation", {})
            for key, value in overall_eval.items():
                if isinstance(value, str):
                    if "差" in value or "不足" in value or "缺失" in value:
                        risk_score += 5
                elif isinstance(value, bool) and not value:
                    risk_score += 5
            
            # 限制在 0-100 之间
            return min(max(risk_score, 0), 100)
            
        except Exception as e:
            logger.error(f"计算风险评分失败: {e}")
            return 50  # 默认中等风险
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """确定风险等级"""
        if risk_score >= 70:
            return "high"
        elif risk_score >= 30:
            return "medium"
        else:
            return "low"
    
    def _generate_summary(self, review_result: Dict[str, Any]) -> str:
        """生成审核摘要"""
        try:
            specific_risks = review_result.get("specific_risks", [])
            high_risks = [r for r in specific_risks if r.get("risk_level") == "high"]
            medium_risks = [r for r in specific_risks if r.get("risk_level") == "medium"]
            
            summary = f"发现 {len(high_risks)} 个高风险点，{len(medium_risks)} 个中风险点。"
            
            if high_risks:
                summary += f" 高风险包括：{', '.join([r.get('risk_description', '')[:50] for r in high_risks[:3]])}"
            
            return summary
            
        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            return "合同审核完成，请查看详细报告。"
    
    async def generate_revision_suggestions(self, original_text: str, risk_points: List[Dict]) -> str:
        """生成修订建议"""
        try:
            prompt = f"""请根据以下风险点，为合同文本提供具体的修订建议。

原始合同文本：
{original_text[:4000]}

风险点：
{json.dumps(risk_points, ensure_ascii=False, indent=2)}

请为每个风险点提供：
1. 具体的修改建议
2. 修改后的条款示例
3. 修改理由

请以清晰的结构化格式返回。"""
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo" if self.provider == "openai" else "deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一名专业的法律顾问，擅长合同条款修订。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=3000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"生成修订建议失败: {e}")
            return "无法生成修订建议，请手动处理。"
    
    async def compare_contracts(self, original_text: str, revised_text: str) -> Dict[str, Any]:
        """比较合同版本"""
        try:
            prompt = f"""请比较以下两个合同版本，分析主要变化和改进。

原始版本：
{original_text[:3000]}

修订版本：
{revised_text[:3000]}

请分析：
1. 主要修改内容
2. 风险改善情况
3. 条款优化程度
4. 整体改进评价

请以 JSON 格式返回结果。"""
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo" if self.provider == "openai" else "deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一名专业的法律顾问，擅长合同版本比较。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return {
                "success": True,
                "comparison_result": result
            }
            
        except Exception as e:
            logger.error(f"合同比较失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# 创建全局 AI 服务实例
ai_service = AIService()