"""
文件存储服务 - 支持本地存储和MinIO对象存储
"""
import os
import shutil
import uuid
from typing import Optional, Union
from fastapi import UploadFile
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class FileService:
    """文件存储服务 - 支持多种存储后端"""
    
    def __init__(self):
        # 根据配置选择存储类型
        self.storage_type = settings.STORAGE_TYPE.lower()
        logger.info(f"当前存储类型: {self.storage_type}")
        
        if self.storage_type == "local":
            # 本地存储目录
            self.storage_dir = "storage/contracts"
            os.makedirs(self.storage_dir, exist_ok=True)
            logger.info(f"使用本地存储，目录: {self.storage_dir}")
        elif self.storage_type == "minio":
            logger.info("使用MinIO对象存储")
            from app.services.minio_service import minio_service as _minio_svc
            self.minio_service = _minio_svc
        else:
            raise ValueError(f"不支持的存储类型: {self.storage_type}")
    
    async def save_contract_file(
        self,
        file: UploadFile,
        user_id: int,
        contract_title: str
    ) -> str:
        """
        保存合同文件
        
        Args:
            file: 上传的文件
            user_id: 用户ID
            contract_title: 合同标题
            
        Returns:
            文件存储路径或对象名称
        """
        if self.storage_type == "local":
            return await self._save_local(file, user_id, contract_title)
        elif self.storage_type == "minio":
            return await self._save_minio(file, user_id, contract_title)
        else:
            raise ValueError(f"不支持的存储类型: {self.storage_type}")
    
    async def _save_local(
        self,
        file: UploadFile,
        user_id: int,
        contract_title: str
    ) -> str:
        """保存到本地存储"""
        try:
            # 生成唯一文件名
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"
            
            # 用户目录
            user_dir = os.path.join(self.storage_dir, str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            
            # 完整文件路径
            file_path = os.path.join(user_dir, unique_filename)
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            logger.info(f"文件保存到本地成功: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"保存文件到本地失败: {e}")
            raise
    
    async def _save_minio(
        self,
        file: UploadFile,
        user_id: int,
        contract_title: str
    ) -> str:
        """保存到MinIO对象存储"""
        try:
            # 使用合同标题作为对象名称的一部分
            safe_title = "".join(c for c in contract_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:50]
            
            # 生成对象名称
            file_ext = file.filename.split('.')[-1] if '.' in file.filename else ''
            object_name = f"contracts/{user_id}/{safe_title}_{uuid.uuid4().hex[:8]}.{file_ext}" if file_ext else f"contracts/{user_id}/{safe_title}_{uuid.uuid4().hex[:8]}"
            
            # 上传到MinIO
            object_name = await self.minio_service.upload_file(
                file=file,
                user_id=user_id,
                object_name=object_name
            )
            
            logger.info(f"文件保存到MinIO成功: {object_name}")
            return object_name
            
        except Exception as e:
            logger.error(f"保存文件到MinIO失败: {e}")
            raise
    
    async def get_file_content(self, file_path: str) -> bytes:
        """
        获取文件内容
        
        Args:
            file_path: 文件路径或对象名称
            
        Returns:
            文件内容字节
        """
        logger.debug(f"获取文件内容，存储类型: {self.storage_type}, 文件路径: {repr(file_path)}")
        if self.storage_type == "local":
            return await self._get_local_content(file_path)
        elif self.storage_type == "minio":
            return await self._get_minio_content(file_path)
        else:
            raise ValueError(f"不支持的存储类型: {self.storage_type}")
    
    async def _get_local_content(self, file_path: str) -> bytes:
        """从本地存储获取文件内容"""
        try:
            full_path = await self.get_file_path(file_path)
            with open(full_path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取本地文件失败: {e}")
            raise
    
    async def _get_minio_content(self, object_name: str) -> bytes:
        """从MinIO获取文件内容"""
        try:
            return await self.minio_service.download_file(object_name)
        except Exception as e:
            # 安全地记录错误，避免编码问题
            try:
                logger.error(f"从MinIO下载文件失败: {e}")
            except UnicodeEncodeError:
                # 如果日志记录失败，使用ASCII安全的错误消息
                logger.error("从MinIO下载文件失败: 编码错误")
            raise
    
    async def get_file_url(self, file_path: str, expires_seconds: int = 3600) -> str:
        """
        获取文件访问URL
        
        Args:
            file_path: 文件路径或对象名称
            expires_seconds: URL过期时间（秒）
            
        Returns:
            文件访问URL
        """
        if self.storage_type == "local":
            # 本地文件返回文件路径
            return await self.get_file_path(file_path)
        elif self.storage_type == "minio":
            # MinIO返回预签名URL
            return await self.minio_service.get_file_url(file_path, expires_seconds)
        else:
            raise ValueError(f"不支持的存储类型: {self.storage_type}")
    
    async def get_file_path(self, file_path: str) -> str:
        """
        获取文件系统路径（仅对本地存储有效）
        
        Args:
            file_path: 存储路径
            
        Returns:
            本地文件系统路径
        """
        if self.storage_type != "local":
            logger.warning("非本地存储类型调用get_file_path方法")
            return file_path
            
        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(file_path):
            return os.path.join(os.getcwd(), file_path)
        return file_path
    
    async def delete_contract_file(self, file_path: str) -> bool:
        """
        删除合同文件
        
        Args:
            file_path: 文件路径或对象名称
            
        Returns:
            是否删除成功
        """
        if self.storage_type == "local":
            return await self._delete_local(file_path)
        elif self.storage_type == "minio":
            return await self._delete_minio(file_path)
        else:
            raise ValueError(f"不支持的存储类型: {self.storage_type}")
    
    async def _delete_local(self, file_path: str) -> bool:
        """删除本地文件"""
        try:
            full_path = await self.get_file_path(file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"本地文件删除成功: {full_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除本地文件失败: {e}")
            return False
    
    async def _delete_minio(self, object_name: str) -> bool:
        """删除MinIO文件"""
        try:
            return await self.minio_service.delete_file(object_name)
        except Exception as e:
            logger.error(f"删除MinIO文件失败: {e}")
            return False
    
    async def file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径或对象名称
            
        Returns:
            是否存在
        """
        if self.storage_type == "local":
            full_path = await self.get_file_path(file_path)
            return os.path.exists(full_path)
        elif self.storage_type == "minio":
            return await self.minio_service.file_exists(file_path)
        else:
            raise ValueError(f"不支持的存储类型: {self.storage_type}")
    
    async def get_file_size(self, file_path: str) -> int:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径或对象名称
            
        Returns:
            文件大小（字节）
        """
        if self.storage_type == "local":
            full_path = await self.get_file_path(file_path)
            if os.path.exists(full_path):
                return os.path.getsize(full_path)
            return 0
        elif self.storage_type == "minio":
            info = await self.minio_service.get_file_info(file_path)
            return info["size"] if info else 0
        else:
            raise ValueError(f"不支持的存储类型: {self.storage_type}")
    
    async def get_file_info(self, file_path: str) -> Optional[dict]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径或对象名称
            
        Returns:
            文件信息字典
        """
        if self.storage_type == "local":
            full_path = await self.get_file_path(file_path)
            if os.path.exists(full_path):
                return {
                    "size": os.path.getsize(full_path),
                    "path": full_path,
                    "storage_type": "local"
                }
            return None
        elif self.storage_type == "minio":
            info = await self.minio_service.get_file_info(file_path)
            if info:
                info["storage_type"] = "minio"
                info["object_name"] = file_path
            return info
        else:
            raise ValueError(f"不支持的存储类型: {self.storage_type}")
    
    async def list_user_files(self, user_id: int) -> list:
        """
        列出用户的所有文件
        
        Args:
            user_id: 用户ID
            
        Returns:
            文件列表
        """
        if self.storage_type == "local":
            return await self._list_local_files(user_id)
        elif self.storage_type == "minio":
            return await self._list_minio_files(user_id)
        else:
            raise ValueError(f"不支持的存储类型: {self.storage_type}")
    
    async def _list_local_files(self, user_id: int) -> list:
        """列出本地文件"""
        try:
            user_dir = os.path.join(self.storage_dir, str(user_id))
            if not os.path.exists(user_dir):
                return []
            
            file_list = []
            for filename in os.listdir(user_dir):
                file_path = os.path.join(user_dir, filename)
                if os.path.isfile(file_path):
                    file_list.append({
                        "name": filename,
                        "path": file_path,
                        "size": os.path.getsize(file_path),
                        "storage_type": "local"
                    })
            
            return file_list
        except Exception as e:
            logger.error(f"列出本地文件失败: {e}")
            return []
    
    async def _list_minio_files(self, user_id: int) -> list:
        """列出MinIO文件"""
        try:
            return await self.minio_service.list_user_files(user_id)
        except Exception as e:
            logger.error(f"列出MinIO文件失败: {e}")
            return []


# 创建全局文件服务实例
file_service = FileService()