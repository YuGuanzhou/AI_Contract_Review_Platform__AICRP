"""
合同相关的 Pydantic 模式
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ContractStatus(str, Enum):
    """合同状态枚举"""
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    AI_PENDING = "ai_pending"
    AI_REVIEWED = "ai_reviewed"
    MANUAL_PENDING = "manual_pending"
    REVIEWED = "reviewed"
    ARCHIVED = "archived"
    ERROR = "error"


class ContractType(str, Enum):
    """合同类型枚举"""
    PURCHASE = "purchase"
    SALES = "sales"
    SERVICE = "service"
    EMPLOYMENT = "employment"
    LEASE = "lease"
    PARTNERSHIP = "partnership"
    OTHER = "other"


class ContractResponse(BaseModel):
    """合同响应"""
    id: int
    user_id: int
    title: str
    description: Optional[str]
    contract_type: ContractType
    status: ContractStatus
    
    # 文件信息
    original_filename: str
    file_path: Optional[str]
    file_size: Optional[int]
    file_type: Optional[str]
    file_hash: Optional[str]
    
    # 解析结果
    parsed_text: Optional[str]
    parsed_json: Optional[Dict[str, Any]]
    page_count: Optional[int]
    word_count: Optional[int]
    
    # 审核信息
    risk_level: Optional[str]
    risk_score: Optional[float]
    review_summary: Optional[str]
    
    # 时间戳
    uploaded_at: datetime
    parsed_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    archived_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ContractCreateRequest(BaseModel):
    """合同创建请求"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    contract_type: ContractType = ContractType.OTHER


class ContractUpdateRequest(BaseModel):
    """合同更新请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    contract_type: Optional[ContractType] = None
    status: Optional[ContractStatus] = None
    risk_level: Optional[str] = Field(None, max_length=20)
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    review_summary: Optional[str] = Field(None, max_length=2000)


class ContractListResponse(BaseModel):
    """合同列表响应"""
    contracts: List[ContractResponse]
    total: int
    skip: int
    limit: int


class ContractUploadResponse(BaseModel):
    """合同上传响应"""
    contract: ContractResponse
    message: str


class ContractReviewResponse(BaseModel):
    """合同审核响应"""
    id: int
    contract_id: int
    user_id: int
    
    # 审核结果
    ai_review_result: Optional[Dict[str, Any]]
    manual_review_result: Optional[Dict[str, Any]]
    final_review_result: Optional[Dict[str, Any]]
    
    # 风险点
    risk_points: Optional[List[Dict[str, Any]]]
    suggestions: Optional[Dict[str, Any]]
    
    # 审核状态
    is_ai_reviewed: bool
    is_manual_reviewed: bool
    is_finalized: bool
    
    # 时间戳
    created_at: datetime
    ai_reviewed_at: Optional[datetime]
    manual_reviewed_at: Optional[datetime]
    finalized_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ContractReviewCreateRequest(BaseModel):
    """合同审核创建请求"""
    manual_review_result: Optional[Dict[str, Any]] = None
    risk_points: Optional[List[Dict[str, Any]]] = None
    suggestions: Optional[Dict[str, Any]] = None
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    risk_level: Optional[str] = Field(None, max_length=20)
    review_summary: Optional[str] = Field(None, max_length=2000)


class ContractReviewUpdateRequest(BaseModel):
    """合同审核更新请求"""
    manual_review_result: Optional[Dict[str, Any]] = None
    risk_points: Optional[List[Dict[str, Any]]] = None
    suggestions: Optional[Dict[str, Any]] = None
    is_finalized: Optional[bool] = None


class ContractReviewListResponse(BaseModel):
    """合同审核列表响应"""
    reviews: List[ContractReviewResponse]
    total: int
    skip: int
    limit: int


class AIReviewRequest(BaseModel):
    """AI审核请求"""
    force_new: bool = False  # 是否强制重新审核


class AIReviewResponse(BaseModel):
    """AI审核响应"""
    success: bool
    review_id: Optional[int] = None
    risk_score: float
    risk_level: str
    summary: str
    review_result: Dict[str, Any]
    message: str


class ContractStatsResponse(BaseModel):
    """合同统计响应"""
    total_contracts: int
    pending_reviews: int
    approved_contracts: int
    high_risk_contracts: int
    avg_risk_score: float
    recent_contracts: int


# 更新前向引用
ContractResponse.update_forward_refs()
ContractListResponse.update_forward_refs()
ContractUploadResponse.update_forward_refs()
ContractReviewResponse.update_forward_refs()
ContractReviewListResponse.update_forward_refs()