"""
合同数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ContractStatus(str, enum.Enum):
    """合同状态枚举"""
    UPLOADED = "uploaded"  # 已上传
    PARSING = "parsing"    # 解析中
    PARSED = "parsed"      # 已解析
    AI_PENDING = "ai_pending"  # 待AI审核
    AI_REVIEWED = "ai_reviewed"  # AI审核完成
    MANUAL_PENDING = "manual_pending"  # 待人工审核
    REVIEWED = "reviewed"  # 审核完毕
    ARCHIVED = "archived"  # 已归档
    ERROR = "error"        # 错误


class ContractType(str, enum.Enum):
    """合同类型枚举"""
    PURCHASE = "purchase"      # 采购合同
    SALES = "sales"           # 销售合同
    SERVICE = "service"       # 服务合同
    EMPLOYMENT = "employment"  # 劳动合同
    LEASE = "lease"           # 租赁合同
    PARTNERSHIP = "partnership"  # 合作协议
    OTHER = "other"           # 其他


class Contract(Base):
    """合同表"""
    __tablename__ = "contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 合同基本信息
    title = Column(String(200), nullable=False)
    description = Column(Text)
    contract_type = Column(Enum(ContractType, values_callable=lambda enum: [e.value for e in enum]), default=ContractType.OTHER)
    status = Column(Enum(ContractStatus, values_callable=lambda enum: [e.value for e in enum]), default=ContractStatus.UPLOADED)
    
    # 文件信息
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500))  # MinIO存储路径
    file_size = Column(Integer)  # 文件大小（字节）
    file_type = Column(String(50))  # pdf, doc, docx等
    file_hash = Column(String(64))  # 文件哈希值
    
    # 解析结果
    parsed_text = Column(Text)  # 解析出的文本内容
    parsed_json = Column(JSON)  # 结构化解析结果
    page_count = Column(Integer)  # 页数
    word_count = Column(Integer)  # 字数
    
    # 审核信息
    risk_level = Column(String(20))  # 风险等级：high, medium, low
    risk_score = Column(Float)  # 风险评分 0-100
    review_summary = Column(Text)  # 审核摘要
    
    # 时间戳
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    parsed_at = Column(DateTime(timezone=True))
    reviewed_at = Column(DateTime(timezone=True))
    archived_at = Column(DateTime(timezone=True))
    
    # 关系
    user = relationship("User", backref="contracts")
    reviews = relationship("ContractReview", back_populates="contract", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Contract(id={self.id}, title={self.title}, status={self.status})>"


class ContractReview(Base):
    """合同审核记录表"""
    __tablename__ = "contract_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 审核结果
    ai_review_result = Column(JSON)  # AI审核原始结果
    manual_review_result = Column(JSON)  # 人工审核结果
    final_review_result = Column(JSON)  # 最终审核结果
    
    # 风险点
    risk_points = Column(JSON)  # 风险点列表
    suggestions = Column(JSON)  # 修改建议
    
    # 审核状态
    is_ai_reviewed = Column(Boolean, default=False)
    is_manual_reviewed = Column(Boolean, default=False)
    is_finalized = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ai_reviewed_at = Column(DateTime(timezone=True))
    manual_reviewed_at = Column(DateTime(timezone=True))
    finalized_at = Column(DateTime(timezone=True))
    
    # 关系
    contract = relationship("Contract", back_populates="reviews")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ContractReview(id={self.id}, contract_id={self.contract_id})>"

