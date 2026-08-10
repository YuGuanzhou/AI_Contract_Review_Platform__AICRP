"""
合同管理路由
"""
from __future__ import annotations
import os
import hashlib
import logging
from io import BytesIO
from datetime import datetime, timedelta
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user_dependency
from app.models.user import User
from app.models.contract import Contract, ContractStatus, ContractType
from app.schemas.contract import (
    ContractResponse,
    ContractCreateRequest,
    ContractUpdateRequest,
    ContractListResponse,
    ContractUploadResponse,
    ContractStatsResponse,
)
from app.services.file_service import FileService
from app.services.parser_service import ParserService
from app.services.contract_processing_service import ContractProcessingService

logger = logging.getLogger(__name__)

router = APIRouter()


# 注意：/stats 必须声明在 /{contract_id} 之前，否则会被 path 参数捕获导致 422
@router.get("/stats", response_model=ContractStatsResponse)
async def get_contract_stats(
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db),
):
    """
    获取合同统计信息
    普通用户统计自己的合同，管理员/审核员统计全部合同
    """
    # 权限过滤：非管理员/审核员只看自己的合同
    own = []
    if current_user.role not in ["admin", "superadmin", "reviewer"]:
        own.append(Contract.user_id == current_user.id)

    total = await db.scalar(select(func.count()).select_from(Contract).where(*own)) or 0

    pending = await db.scalar(
        select(func.count()).select_from(Contract).where(
            Contract.status.in_([
                ContractStatus.AI_PENDING,
                ContractStatus.AI_REVIEWED,
                ContractStatus.MANUAL_PENDING,
            ]),
            *own
        )
    ) or 0

    approved = await db.scalar(
        select(func.count()).select_from(Contract).where(
            Contract.status == ContractStatus.REVIEWED,
            *own
        )
    ) or 0

    high_risk = await db.scalar(
        select(func.count()).select_from(Contract).where(
            Contract.risk_level == "high",
            *own
        )
    ) or 0

    avg_score = await db.scalar(
        select(func.avg(Contract.risk_score)).where(
            Contract.risk_score.isnot(None),
            *own
        )
    ) or 0.0

    # 最近 7 天上传
    cutoff = datetime.now() - timedelta(days=7)
    recent = await db.scalar(
        select(func.count()).select_from(Contract).where(
            Contract.uploaded_at >= cutoff,
            *own
        )
    ) or 0

    return ContractStatsResponse(
        total_contracts=total,
        pending_reviews=pending,
        approved_contracts=approved,
        high_risk_contracts=high_risk,
        avg_risk_score=round(float(avg_score), 1),
        recent_contracts=recent,
    )


@router.get("/", response_model=ContractListResponse)
async def list_contracts(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    contract_type: Optional[str] = None,
    user_id: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db),
):
    """
    获取合同列表
    普通用户只能查看自己的合同，管理员可以查看所有合同或指定用户的合同
    """
    # 构建基础查询
    query = select(Contract)
    count_query = select(func.count()).select_from(Contract)
    
    # 权限过滤：非管理员只能查看自己的合同
    if current_user.role not in ["admin", "superadmin"]:
        query = query.where(Contract.user_id == current_user.id)
        count_query = count_query.where(Contract.user_id == current_user.id)
    else:
        # 管理员可以指定用户筛选
        if user_id is not None:
            query = query.where(Contract.user_id == user_id)
            count_query = count_query.where(Contract.user_id == user_id)
    
    # 状态筛选
    if status:
        query = query.where(Contract.status == status)
        count_query = count_query.where(Contract.status == status)
    
    # 合同类型筛选
    if contract_type:
        query = query.where(Contract.contract_type == contract_type)
        count_query = count_query.where(Contract.contract_type == contract_type)
    
    # 搜索筛选
    if search:
        from sqlalchemy import or_
        search_filter = or_(
            Contract.title.ilike(f"%{search}%"),
            Contract.description.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    # 排序和分页
    query = query.order_by(desc(Contract.uploaded_at)).offset(skip).limit(limit)
    
    # 执行查询
    result = await db.execute(query)
    contracts = result.scalars().all()
    
    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    return ContractListResponse(
        contracts=[ContractResponse.from_orm(contract) for contract in contracts],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("/upload", response_model=ContractUploadResponse)
async def upload_contract(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    contract_type: ContractType = Form(ContractType.OTHER),
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    上传合同文件
    """
    # 权限检查：审核员不能上传合同
    if current_user.role == "reviewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="审核员无权上传合同"
        )
    
    # 验证文件类型
    file_ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
    if file_ext not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型，仅支持: {', '.join(settings.ALLOWED_FILE_TYPES)}"
        )
    
    # 验证文件大小
    file.file.seek(0, 2)  # 移动到文件末尾
    file_size = file.file.tell()
    file.file.seek(0)  # 重置文件指针
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制 ({settings.MAX_UPLOAD_SIZE // (1024*1024)}MB)"
        )
    
    # 计算文件哈希
    file_content = await file.read()
    file_hash = hashlib.sha256(file_content).hexdigest()
    file.file = BytesIO(file_content)  # 重新设置文件对象
    
    # 保存文件到 MinIO
    file_service = FileService()
    file_path = await file_service.save_contract_file(
        file=file,
        user_id=current_user.id,
        contract_title=title
    )
    
    # 创建合同记录
    contract = Contract(
        user_id=current_user.id,
        title=title,
        description=description,
        contract_type=contract_type,
        status=ContractStatus.UPLOADED,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        file_type=file_ext,
        file_hash=file_hash
    )
    
    db.add(contract)
    await db.commit()
    await db.refresh(contract)  # 重新加载对象以获取所有属性
    
    # 启动异步处理：解析 + AI审核
    processing_service = ContractProcessingService()
    await processing_service.process_contract_async(contract.id)
    
    # 手动创建ContractResponse对象，避免异步属性访问问题
    contract_response = ContractResponse(
        id=contract.id,
        user_id=contract.user_id,
        title=contract.title,
        description=contract.description,
        contract_type=contract.contract_type,
        status=contract.status,
        original_filename=contract.original_filename,
        file_path=contract.file_path,
        file_size=contract.file_size,
        file_type=contract.file_type,
        file_hash=contract.file_hash,
        parsed_text=contract.parsed_text,
        parsed_json=contract.parsed_json,
        page_count=contract.page_count,
        word_count=contract.word_count,
        risk_level=contract.risk_level,
        risk_score=contract.risk_score,
        review_summary=contract.review_summary,
        uploaded_at=contract.uploaded_at,
        parsed_at=contract.parsed_at,
        reviewed_at=contract.reviewed_at,
        archived_at=contract.archived_at
    )
    
    return ContractUploadResponse(
        contract=contract_response,
        message="合同上传成功，正在启动AI审核..."
    )


@router.get("/{contract_id}", response_model=None)
async def get_contract(
    contract_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    获取单个合同详情
    """
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同不存在"
        )
    
    # 检查权限
    if contract.user_id != current_user.id and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此合同"
        )
    
    return ContractResponse.from_orm(contract)


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: int,
    request: ContractUpdateRequest,
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    更新合同信息
    """
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同不存在"
        )
    
    # 检查权限
    if contract.user_id != current_user.id and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此合同"
        )
    
    # 更新字段
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contract, field, value)
    
    await db.commit()
    await db.refresh(contract)
    
    return ContractResponse.from_orm(contract)


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    删除合同
    """
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同不存在"
        )
    
    # 检查权限
    if contract.user_id != current_user.id and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此合同"
        )
    
    # 删除文件
    file_service = FileService()
    await file_service.delete_contract_file(contract.file_path)
    
    # 删除数据库记录
    await db.delete(contract)
    await db.commit()
    
    return {"message": "合同删除成功"}


@router.get("/{contract_id}/download")
async def download_contract(
    contract_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    下载合同文件
    """
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同不存在"
        )
    
    # 检查权限
    if contract.user_id != current_user.id and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权下载此合同"
        )
    
    # 根据存储类型处理文件
    file_service = FileService()
    
    if settings.STORAGE_TYPE == "local":
        # 本地存储：获取文件路径并返回FileResponse
        file_path = await file_service.get_file_path(contract.file_path)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            # 如果文件不存在，尝试在storage目录下查找
            storage_file_path = os.path.join("storage", file_path)
            if os.path.exists(storage_file_path):
                file_path = storage_file_path
            else:
                # 如果文件不存在，尝试查找相同ID的PDF文件（处理数据不一致问题）
                import glob
                storage_dir = os.path.dirname(file_path)
                
                # 首先尝试查找数据库记录中的文件名
                db_filename = os.path.basename(file_path)
                db_pattern = os.path.join(storage_dir, f"*{db_filename}*")
                matching_files = glob.glob(db_pattern)
                
                if not matching_files:
                    # 如果找不到，尝试查找任何PDF文件
                    file_pattern = os.path.join(storage_dir, "*.pdf")
                    matching_files = glob.glob(file_pattern)
                
                if matching_files:
                    # 使用第一个找到的文件
                    file_path = matching_files[0]
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="合同文件不存在"
                    )
        
        return FileResponse(
            path=file_path,
            filename=contract.original_filename,
            media_type="application/octet-stream"
        )
    else:
        # MinIO存储：获取文件内容并返回StreamingResponse
        try:
            file_content = await file_service.get_file_content(contract.file_path)
            
            from fastapi.responses import StreamingResponse
            from io import BytesIO
            
            return StreamingResponse(
                BytesIO(file_content),
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename=\"{contract.original_filename}\""
                }
            )
        except Exception as e:
            logger.error(f"获取文件内容失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取文件内容失败: {str(e)}"
            )


@router.get("/{contract_id}/preview")
async def preview_contract(
    contract_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    预览合同文件（内联显示）
    """
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同不存在"
        )
    
    # 在DEBUG模式下跳过权限检查，便于测试
    if not settings.DEBUG:
        # 检查权限
        if contract.user_id != current_user.id and current_user.role not in ["admin", "superadmin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权预览此合同"
            )
    
    # 根据存储类型处理文件
    file_service = FileService()
    
    if settings.STORAGE_TYPE == "local":
        # 本地存储：获取文件路径并返回FileResponse
        file_path = await file_service.get_file_path(contract.file_path)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            # 如果文件不存在，尝试在storage目录下查找
            storage_file_path = os.path.join("storage", file_path)
            if os.path.exists(storage_file_path):
                file_path = storage_file_path
            else:
                # 如果文件不存在，尝试查找相同ID的PDF文件（处理数据不一致问题）
                import glob
                storage_dir = os.path.dirname(file_path)
                
                # 首先尝试查找数据库记录中的文件名
                db_filename = os.path.basename(file_path)
                db_pattern = os.path.join(storage_dir, f"*{db_filename}*")
                matching_files = glob.glob(db_pattern)
                
                if not matching_files:
                    # 如果找不到，尝试查找任何PDF文件
                    file_pattern = os.path.join(storage_dir, "*.pdf")
                    matching_files = glob.glob(file_pattern)
                
                if matching_files:
                    # 使用第一个找到的文件
                    file_path = matching_files[0]
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="合同文件不存在"
                    )
        
        # 根据文件类型设置媒体类型
        file_ext = os.path.splitext(contract.original_filename)[1].lower()
        media_type_map = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png'
        }
        
        media_type = media_type_map.get(file_ext, 'application/octet-stream')
        
        return FileResponse(
            path=file_path,
            filename=contract.original_filename,
            media_type=media_type
        )
    else:
        # MinIO存储：获取文件内容并返回StreamingResponse
        try:
            file_content = await file_service.get_file_content(contract.file_path)
            
            # 根据文件类型设置媒体类型
            file_ext = os.path.splitext(contract.original_filename)[1].lower()
            media_type_map = {
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.txt': 'text/plain',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png'
            }
            
            media_type = media_type_map.get(file_ext, 'application/octet-stream')
            
            from fastapi.responses import StreamingResponse
            from io import BytesIO
            
            # 处理文件名编码问题
            import urllib.parse
            original_filename = contract.original_filename
            
            # 创建ASCII安全的文件名
            try:
                # 尝试编码为ASCII，如果失败则使用安全名称
                original_filename.encode('ascii')
                safe_filename = original_filename
            except UnicodeEncodeError:
                # 使用安全名称：contract_{id}{ext}
                safe_filename = f"contract_{contract_id}{file_ext}"
            
            # URL编码文件名用于filename*参数
            encoded_filename = urllib.parse.quote(original_filename, safe='')
            
            return StreamingResponse(
                BytesIO(file_content),
                media_type=media_type,
                headers={
                    "Content-Disposition": f"inline; filename=\"{safe_filename}\"; filename*=UTF-8''{encoded_filename}"
                }
            )
        except Exception as e:
            logger.error(f"获取文件内容失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取文件内容失败: {str(e)}"
            )
    
    # 处理文件名编码问题：使用ASCII安全的文件名
    # 如果文件名包含非ASCII字符，使用"contract_{id}.pdf"格式
    import re
    original_filename = contract.original_filename
    try:
        # 尝试编码为ASCII，如果失败则使用安全名称
        original_filename.encode('ascii')
        safe_filename = original_filename
    except UnicodeEncodeError:
        # 使用安全名称：contract_{id}{ext}
        safe_filename = f"contract_{contract_id}{file_ext}"
    
    # 创建响应，不设置filename参数，只通过headers设置Content-Disposition
    import urllib.parse
    encoded_filename = urllib.parse.quote(original_filename, safe='')
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers={
            "Content-Disposition": f"inline; filename=\"{safe_filename}\"; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.get("/{contract_id}/preview-public")
async def preview_contract_public(
    contract_id: int,
    db = Depends(get_db)
):
    """
    公开预览合同文件（用于测试，不需要认证）
    """
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同不存在"
        )
    
    # 从存储获取文件路径
    file_service = FileService()
    
    # 根据存储类型处理
    if settings.STORAGE_TYPE == "local":
        # 本地存储：使用FileResponse
        file_path = await file_service.get_file_path(contract.file_path)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            # 如果文件不存在，尝试查找相同ID的PDF文件（处理数据不一致问题）
            import glob
            storage_dir = os.path.dirname(file_path)
            file_pattern = os.path.join(storage_dir, "*.pdf")
            pdf_files = glob.glob(file_pattern)
            
            if pdf_files:
                # 使用第一个找到的PDF文件
                file_path = pdf_files[0]
                # 更新文件扩展名以便正确设置媒体类型
                file_ext = '.pdf'
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="合同文件不存在"
                )
        
        # 根据文件类型设置媒体类型
        file_ext = os.path.splitext(contract.original_filename)[1].lower()
        media_type_map = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png'
        }
        
        media_type = media_type_map.get(file_ext, 'application/octet-stream')
        
        # 处理文件名编码问题：使用ASCII安全的文件名
        # 如果文件名包含非ASCII字符，使用"contract_{id}.pdf"格式
        import re
        original_filename = contract.original_filename
        try:
            # 尝试编码为ASCII，如果失败则使用安全名称
            original_filename.encode('ascii')
            safe_filename = original_filename
        except UnicodeEncodeError:
            # 使用安全名称：contract_{id}{ext}
            safe_filename = f"contract_{contract_id}{file_ext}"
        
        # 创建响应，不设置filename参数，只通过headers设置Content-Disposition
        import urllib.parse
        encoded_filename = urllib.parse.quote(original_filename, safe='')
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            headers={
                "Content-Disposition": f"inline; filename=\"{safe_filename}\"; filename*=UTF-8''{encoded_filename}"
            }
        )
    else:
        # MinIO存储：获取文件内容并返回StreamingResponse
        try:
            file_content = await file_service.get_file_content(contract.file_path)
            
            # 根据文件类型设置媒体类型
            file_ext = os.path.splitext(contract.original_filename)[1].lower()
            media_type_map = {
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.txt': 'text/plain',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png'
            }
            
            media_type = media_type_map.get(file_ext, 'application/octet-stream')
            
            from fastapi.responses import StreamingResponse
            from io import BytesIO
            
            # 处理文件名编码问题
            import urllib.parse
            original_filename = contract.original_filename
            
            # 创建ASCII安全的文件名
            try:
                # 尝试编码为ASCII，如果失败则使用安全名称
                original_filename.encode('ascii')
                safe_filename = original_filename
            except UnicodeEncodeError:
                # 使用安全名称：contract_{id}{ext}
                safe_filename = f"contract_{contract_id}{file_ext}"
            
            # URL编码文件名用于filename*参数
            encoded_filename = urllib.parse.quote(original_filename, safe='')
            
            return StreamingResponse(
                BytesIO(file_content),
                media_type=media_type,
                headers={
                    "Content-Disposition": f"inline; filename=\"{safe_filename}\"; filename*=UTF-8''{encoded_filename}"
                }
            )
        except Exception as e:
            # 安全地记录错误，避免编码问题
            try:
                # 尝试获取错误消息的字符串表示
                error_str = str(e)
                # 尝试编码为ASCII以检查是否安全
                error_str.encode('ascii')
                logger.error(f"获取文件内容失败: {error_str}")
            except (UnicodeEncodeError, UnicodeDecodeError):
                # 如果日志记录失败，使用ASCII安全的错误消息
                logger.error("获取文件内容失败: 编码错误")
            
            # 返回安全的错误详情，避免编码问题
            try:
                error_detail = str(e)
                # 尝试编码为ASCII，如果失败则使用通用错误消息
                error_detail.encode('ascii')
            except (UnicodeEncodeError, UnicodeDecodeError):
                error_detail = "文件处理失败，可能包含不支持的字符"
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取文件内容失败: {error_detail}"
            )


@router.post("/{contract_id}/parse")
async def parse_contract(
    contract_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    手动触发合同解析
    """
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同不存在"
        )
    
    # 检查权限
    if contract.user_id != current_user.id and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此合同"
        )
    
    # 更新状态
    contract.status = ContractStatus.PARSING
    await db.commit()
    
    # 解析合同
    parser_service = ParserService()
    try:
        parse_result = await parser_service.parse_contract(contract.file_path)
        
        # 更新解析结果
        contract.parsed_text = parse_result.get("text")
        contract.parsed_json = parse_result.get("structured_data")
        contract.page_count = parse_result.get("page_count", 0)
        contract.word_count = parse_result.get("word_count", 0)
        contract.status = ContractStatus.PARSED
        contract.parsed_at = func.now()
        
        await db.commit()
        await db.refresh(contract)
        
        return {
            "message": "合同解析成功",
            "contract": ContractResponse.from_orm(contract)
        }
    except Exception as e:
        contract.status = ContractStatus.ERROR
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"合同解析失败: {str(e)}"
        )


@router.get("/{contract_id}/review-details")
async def get_contract_review_details(
    contract_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    获取合同审核详情（包括AI审核结果）
    """
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同不存在"
        )
    
    # 检查权限
    if contract.user_id != current_user.id and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此合同"
        )
    
    # 使用合同处理服务获取审核详情
    processing_service = ContractProcessingService()
    review_details = await processing_service.get_contract_review_details(contract_id, db)
    
    if not review_details.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取审核详情失败: {review_details.get('error')}"
        )
    
    return review_details


@router.post("/{contract_id}/trigger-ai-review")
async def trigger_ai_review(
    contract_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db = Depends(get_db)
):
    """
    手动触发AI审核
    """
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同不存在"
        )
    
    # 检查权限
    if contract.user_id != current_user.id and current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此合同"
        )
    
    # 检查合同是否已解析
    if not contract.parsed_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="合同未解析，请先解析合同"
        )
    
    # 使用合同处理服务进行AI审核
    processing_service = ContractProcessingService()
    
    try:
        # 更新状态为审核中
        contract.status = ContractStatus.AI_PENDING
        await db.commit()
        
        # 执行AI审核
        ai_review_result = await processing_service.ai_service.review_contract(
            contract_text=contract.parsed_text,
            contract_type=contract.contract_type.value
        )
        
        if not ai_review_result.get("success"):
            contract.status = ContractStatus.ERROR
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI审核失败: {ai_review_result.get('error')}"
            )
        
        # 更新AI审核结果
        contract.risk_score = ai_review_result.get("risk_score", 0)
        contract.risk_level = ai_review_result.get("risk_level", "unknown")
        contract.review_summary = ai_review_result.get("summary", "")
        contract.reviewed_at = func.now()
        contract.status = ContractStatus.MANUAL_PENDING
        await db.commit()
        
        # 创建/更新审核记录：复用该合同最新一条记录，避免与后台自动审核记录重复
        from app.models.contract import ContractReview
        existing_review = await db.execute(
            select(ContractReview).where(
                ContractReview.contract_id == contract.id
            ).order_by(desc(ContractReview.id)).limit(1)
        )
        existing_review = existing_review.scalar_one_or_none()

        ai_review_result = ai_review_result.get("review_result", {})

        if existing_review:
            # 更新现有记录
            existing_review.ai_review_result = ai_review_result
            existing_review.risk_points = ai_review_result.get("specific_risks", [])
            existing_review.suggestions = ai_review_result.get("modification_suggestions", {})
            existing_review.is_ai_reviewed = True
            existing_review.ai_reviewed_at = func.now()
            review_record = existing_review
        else:
            # 创建新记录
            review_record = ContractReview(
                contract_id=contract.id,
                user_id=contract.user_id,
                ai_review_result=ai_review_result,
                risk_points=ai_review_result.get("specific_risks", []),
                suggestions=ai_review_result.get("modification_suggestions", {}),
                is_ai_reviewed=True,
                is_manual_reviewed=False,
                is_finalized=False
            )
            db.add(review_record)
        await db.commit()
        # 提交后刷新合同，避免 from_orm 在同步上下文触发惰性加载（MissingGreenlet）
        await db.refresh(contract)

        return {
            "message": "AI审核完成",
            "risk_score": contract.risk_score,
            "risk_level": contract.risk_level,
            "summary": contract.review_summary,
            "contract": ContractResponse.from_orm(contract)
        }
        
    except Exception as e:
        contract.status = ContractStatus.ERROR
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI审核过程出错: {str(e)}"
        )