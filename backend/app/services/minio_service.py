"""
MinIO对象存储服务
"""
import io
import uuid
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile, HTTPException
from fastapi import status
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class MinioService:
    """MinIO对象存储服务"""
    
    def __init__(self):
        """初始化MinIO客户端"""
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        
        # 确保bucket存在
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"创建存储桶: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"创建存储桶失败: {e}")
            raise
    
    async def upload_file(
        self,
        file: UploadFile,
        user_id: int,
        object_name: Optional[str] = None
    ) -> str:
        """
        上传文件到MinIO
        
        Args:
            file: 上传的文件
            user_id: 用户ID
            object_name: 对象名称（可选）
            
        Returns:
            对象存储路径
        """
        try:
            # 生成对象名称
            if not object_name:
                file_ext = file.filename.split('.')[-1] if '.' in file.filename else ''
                object_name = f"users/{user_id}/{uuid.uuid4().hex}.{file_ext}" if file_ext else f"users/{user_id}/{uuid.uuid4().hex}"
            
            # 读取文件内容
            content = await file.read()
            file_size = len(content)
            
            # 上传到MinIO
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=io.BytesIO(content),
                length=file_size,
                content_type=file.content_type
            )
            
            logger.info(f"文件上传成功: {object_name}, 大小: {file_size}字节")
            return object_name
            
        except S3Error as e:
            logger.error(f"上传文件失败: {e}")
            raise
        except Exception as e:
            logger.error(f"上传文件失败: {e}")
            raise
    
    async def download_file(self, object_name: str) -> bytes:
        """
        从MinIO下载文件
        
        Args:
            object_name: 对象名称
            
        Returns:
            文件内容字节
        """
        try:
            # 首先记录对象名称（使用repr避免编码问题）
            logger.debug(f"开始下载文件，对象名称: {repr(object_name)}")
            
            # 确保对象名称是ASCII安全的
            # MinIO客户端内部可能使用latin-1编码，所以我们需要确保字符串可以被latin-1编码
            ascii_safe_name = object_name
            
            # 尝试编码为latin-1，如果失败则使用原始名称
            try:
                ascii_safe_name.encode('latin-1')
                logger.debug(f"对象名称可以编码为latin-1: {repr(ascii_safe_name)}")
            except UnicodeEncodeError:
                # 如果包含非latin-1字符，尝试使用URL编码
                import urllib.parse
                ascii_safe_name = urllib.parse.quote(object_name, safe='')
                logger.debug(f"对象名称包含非latin-1字符，使用URL编码: {repr(ascii_safe_name)}")
            
            logger.debug(f"下载文件 - 对象名称: {repr(object_name)}, ASCII安全名称: {repr(ascii_safe_name)}")
            
            # 首先尝试ASCII安全名称
            try:
                response = self.client.get_object(
                    bucket_name=self.bucket_name,
                    object_name=ascii_safe_name
                )
                data = response.read()
                response.close()
                response.release_conn()
                return data
            except S3Error as e:
                if "NoSuchKey" not in str(e):
                    raise
                logger.debug(f"ASCII安全名称不存在，尝试原始名称: {object_name}")
            
            # 如果ASCII安全名称失败，尝试原始名称（如果不同）
            if ascii_safe_name != object_name:
                try:
                    response = self.client.get_object(
                        bucket_name=self.bucket_name,
                        object_name=object_name
                    )
                    data = response.read()
                    response.close()
                    response.release_conn()
                    return data
                except S3Error as e:
                    if "NoSuchKey" not in str(e):
                        raise
                    logger.debug(f"原始名称也不存在")
            
            # 如果都失败，尝试其他可能的编码
            # 对象可能以UTF-8字节形式存储
            try:
                utf8_bytes = object_name.encode('utf-8')
                # 尝试将UTF-8字节解码为latin-1（这可能产生乱码，但可能匹配MinIO中的存储方式）
                latin1_name = utf8_bytes.decode('latin-1', errors='ignore')
                if latin1_name and latin1_name != object_name:
                    logger.debug(f"尝试UTF-8转latin-1编码的名称: {repr(latin1_name)}")
                    try:
                        response = self.client.get_object(
                            bucket_name=self.bucket_name,
                            object_name=latin1_name
                        )
                        data = response.read()
                        response.close()
                        response.release_conn()
                        return data
                    except S3Error:
                        pass
            except Exception:
                pass
            
            # 所有尝试都失败
            # 使用安全的对象名称，避免编码问题
            safe_object_name = object_name
            try:
                # 尝试编码为ASCII，如果失败则使用通用名称
                safe_object_name.encode('ascii')
            except UnicodeEncodeError:
                safe_object_name = f"object_{hash(object_name) % 10000}"
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文件不存在: {safe_object_name}"
            )
                
        except Exception as e:
            # 安全地处理所有异常，避免编码问题
            error_type = type(e).__name__
            
            # 安全地记录错误
            try:
                error_msg = str(e)
                # 尝试编码为ASCII以检查是否安全
                error_msg.encode('ascii')
                logger.error(f"下载文件失败 [{error_type}]: {error_msg}, object_name: {repr(object_name)}")
            except (UnicodeEncodeError, UnicodeDecodeError):
                logger.error(f"下载文件失败 [{error_type}]: [编码错误], object_name: {repr(object_name)}")
            
            # 检查是否是文件不存在错误
            error_str = str(e)
            if "NoSuchKey" in error_str or "not found" in error_str.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文件不存在"
                )
            
            # 返回通用的错误消息，避免编码问题
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="下载文件失败"
            )
    
    async def get_file_url(self, object_name: str, expires_seconds: int = 3600) -> str:
        """
        获取文件临时访问URL
        
        Args:
            object_name: 对象名称
            expires_seconds: URL过期时间（秒）
            
        Returns:
            临时访问URL
        """
        try:
            import urllib.parse
            
            # 对对象名称进行URL编码，确保特殊字符被正确处理
            encoded_object_name = urllib.parse.quote(object_name, safe='')
            
            logger.debug(f"生成文件URL - 原始对象名称: {object_name}, 编码后: {encoded_object_name}")
            
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=encoded_object_name,
                expires=expires_seconds
            )
            return url
        except S3Error as e:
            logger.error(f"生成文件URL失败: {e}, object_name: {object_name}")
            
            # 如果URL编码失败，尝试使用原始对象名称
            try:
                url = self.client.presigned_get_object(
                    bucket_name=self.bucket_name,
                    object_name=object_name,
                    expires=expires_seconds
                )
                return url
            except S3Error as e2:
                logger.error(f"使用原始对象名称也失败: {e2}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"生成文件URL失败: {str(e2)}"
                )
    
    async def delete_file(self, object_name: str) -> bool:
        """
        删除MinIO中的文件
        
        Args:
            object_name: 对象名称
            
        Returns:
            是否删除成功
        """
        try:
            import urllib.parse
            
            # 对对象名称进行URL编码，确保特殊字符被正确处理
            encoded_object_name = urllib.parse.quote(object_name, safe='')
            
            logger.debug(f"删除文件 - 原始对象名称: {object_name}, 编码后: {encoded_object_name}")
            
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=encoded_object_name
            )
            logger.info(f"文件删除成功: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"删除文件失败: {e}, object_name: {object_name}")
            
            # 如果URL编码失败，尝试使用原始对象名称
            try:
                self.client.remove_object(
                    bucket_name=self.bucket_name,
                    object_name=object_name
                )
                logger.info(f"文件删除成功(使用原始名称): {object_name}")
                return True
            except S3Error as e2:
                logger.error(f"使用原始对象名称也失败: {e2}")
                return False
    
    async def file_exists(self, object_name: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            object_name: 对象名称
            
        Returns:
            是否存在
        """
        try:
            import urllib.parse
            
            # 对对象名称进行URL编码，确保特殊字符被正确处理
            encoded_object_name = urllib.parse.quote(object_name, safe='')
            
            logger.debug(f"检查文件存在 - 原始对象名称: {object_name}, 编码后: {encoded_object_name}")
            
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=encoded_object_name
            )
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                # 如果URL编码的对象不存在，尝试使用原始对象名称
                try:
                    self.client.stat_object(
                        bucket_name=self.bucket_name,
                        object_name=object_name
                    )
                    return True
                except S3Error as e2:
                    if e2.code == "NoSuchKey":
                        return False
                    logger.error(f"使用原始对象名称检查也失败: {e2}")
                    return False
            logger.error(f"检查文件存在失败: {e}, object_name: {object_name}")
            return False
    
    async def get_file_info(self, object_name: str) -> Optional[dict]:
        """
        获取文件信息
        
        Args:
            object_name: 对象名称
            
        Returns:
            文件信息字典
        """
        try:
            import urllib.parse
            
            # 对对象名称进行URL编码，确保特殊字符被正确处理
            encoded_object_name = urllib.parse.quote(object_name, safe='')
            
            logger.debug(f"获取文件信息 - 原始对象名称: {object_name}, 编码后: {encoded_object_name}")
            
            stat = self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=encoded_object_name
            )
            return {
                "size": stat.size,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified,
                "etag": stat.etag
            }
        except S3Error as e:
            if e.code == "NoSuchKey":
                # 如果URL编码的对象不存在，尝试使用原始对象名称
                try:
                    stat = self.client.stat_object(
                        bucket_name=self.bucket_name,
                        object_name=object_name
                    )
                    return {
                        "size": stat.size,
                        "content_type": stat.content_type,
                        "last_modified": stat.last_modified,
                        "etag": stat.etag
                    }
                except S3Error as e2:
                    if e2.code == "NoSuchKey":
                        return None
                    logger.error(f"使用原始对象名称获取信息也失败: {e2}")
                    return None
            logger.error(f"获取文件信息失败: {e}, object_name: {object_name}")
            return None
    
    async def list_user_files(self, user_id: int, prefix: str = "") -> list:
        """
        列出用户的所有文件
        
        Args:
            user_id: 用户ID
            prefix: 前缀过滤
            
        Returns:
            文件对象列表
        """
        try:
            objects = self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=f"users/{user_id}/{prefix}" if prefix else f"users/{user_id}/",
                recursive=True
            )
            
            file_list = []
            for obj in objects:
                file_list.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified
                })
            
            return file_list
        except S3Error as e:
            logger.error(f"列出用户文件失败: {e}")
            return []


# 创建全局MinIO服务实例
minio_service = MinioService()