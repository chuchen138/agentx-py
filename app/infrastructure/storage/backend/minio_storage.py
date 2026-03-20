import os
from pathlib import Path
from typing import List, Dict, Any
from minio import Minio
from minio.error import S3Error
from app.infrastructure.storage.backend.base import StorageBackend, AsyncStorageBackend


class MinioStorageBackend(StorageBackend):
    """Minio存储适配器"""

    def __init__(self, 
                 endpoint: str = "10.128.18.216:9000",
                 access_key: str = "admin",
                 secret_key: str = "password",
                 bucket: str = "agentx-files",
                 secure: bool = False,
                 region: str = "us-east-1",
                 base_url: str = None):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.secure = secure
        self.region = region
        self.base_url = base_url or f"http://{endpoint}/{bucket}"
        
        # 尝试初始化Minio客户端
        try:
            print(f"Initializing Minio client with endpoint={endpoint}, access_key={access_key}, secure={secure}")
            self.client = Minio(
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
                region=region
            )
            print("Minio client initialized successfully")
            
            # 测试连接
            print("Testing Minio connection...")
            buckets = self.client.list_buckets()
            print(f"Successfully connected to Minio, found {len(buckets)} buckets")
            for bucket in buckets:
                print(f"  - {bucket.name}")
            
            # 尝试确保存储桶存在
            self._ensure_bucket_exists()
            print(f"Successfully connected to Minio at {endpoint}")
        except Exception as e:
            print(f"Warning: Failed to connect to Minio: {e}")
            print(f"Minio connection details: endpoint={endpoint}, access_key={access_key}, bucket={bucket}")
            import traceback
            traceback.print_exc()

    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        try:
            print(f"Checking if bucket {self.bucket} exists...")
            exists = self.client.bucket_exists(self.bucket)
            print(f"Bucket {self.bucket} exists: {exists}")
            if not exists:
                print(f"Creating bucket {self.bucket}...")
                self.client.make_bucket(self.bucket)
                print(f"Bucket {self.bucket} created successfully")
        except Exception as e:
            print(f"Error ensuring bucket exists: {e}")
            import traceback
            traceback.print_exc()

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，防止路径遍历攻击"""
        # 分割路径和文件名
        path_parts = filename.split("/")
        sanitized_parts = []
        
        for part in path_parts:
            # 移除特殊字符，保留字母数字和基本符号
            sanitized_part = "".join(c for c in part if c.isalnum() or c in "._- ")
            # 确保部分不为空
            if sanitized_part:
                sanitized_parts.append(sanitized_part)
        
        # 重新组合路径
        return "/".join(sanitized_parts)

    def save(self, file_content: bytes, filename: str, **kwargs) -> str:
        """保存文件，返回URL"""
        try:
            # 检查客户端是否初始化成功
            if not hasattr(self, 'client') or self.client is None:
                raise Exception("Minio client not initialized")
            
            # 清理文件名
            sanitized_filename = self._sanitize_filename(filename)
            
            # 上传文件
            # 对于bytes对象，需要包装成文件类对象
            import io
            file_obj = io.BytesIO(file_content)
            
            print(f"Uploading file to Minio: {sanitized_filename}")
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=sanitized_filename,
                data=file_obj,
                length=len(file_content),
                content_type=kwargs.get("content_type", "application/octet-stream")
            )
            
            # 生成URL
            file_url = f"{self.base_url}/{sanitized_filename}"
            print(f"File uploaded successfully to Minio: {file_url}")
            return file_url
        except Exception as e:
            print(f"Error saving file to Minio: {e}")
            import traceback
            traceback.print_exc()
            # 如果Minio保存失败，尝试使用本地存储
            print("Falling back to local storage...")
            from app.infrastructure.storage.backend.local_storage import LocalStorageBackend
            local_backend = LocalStorageBackend(root_dir="./uploads/fallback")
            local_url = local_backend.save(file_content, filename, **kwargs)
            print(f"File saved to local storage: {local_url}")
            return local_url

    def load(self, file_url: str) -> bytes:
        """加载文件内容"""
        try:
            # 从URL中提取对象名
            # 尝试多种方式提取对象名，以处理不同的base_url格式
            object_name = file_url
            
            # 方法1: 使用self.base_url
            if self.base_url in file_url:
                object_name = file_url.replace(f"{self.base_url}/", "")
            # 方法2: 从URL路径中提取
            else:
                # 从URL中提取路径部分
                import urllib.parse
                parsed_url = urllib.parse.urlparse(file_url)
                path = parsed_url.path
                # 移除开头的'/'
                if path.startswith('/'):
                    path = path[1:]
                # 移除bucket名称
                if path.startswith(f"{self.bucket}/"):
                    object_name = path.replace(f"{self.bucket}/", "")
                else:
                    object_name = path
            
            print(f"Loading object: {object_name} from bucket: {self.bucket}")
            
            # 获取对象
            response = self.client.get_object(
                bucket_name=self.bucket,
                object_name=object_name
            )
            
            # 读取内容
            content = response.read()
            response.close()
            response.release_conn()
            
            return content
        except S3Error as e:
            print(f"Error loading file: {e}")
            raise

    def update(self, file_url: str, new_content: bytes) -> str:
        """更新文件"""
        try:
            # 从URL中提取对象名
            object_name = file_url.replace(f"{self.base_url}/", "")
            
            # 上传新内容
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_name,
                data=bytes(new_content),
                length=len(new_content)
            )
            
            return file_url
        except S3Error as e:
            print(f"Error updating file: {e}")
            raise

    def delete(self, file_url: str) -> bool:
        """删除文件"""
        try:
            # 从URL中提取对象名
            object_name = file_url.replace(f"{self.base_url}/", "")
            
            # 删除对象
            self.client.remove_object(
                bucket_name=self.bucket,
                object_name=object_name
            )
            
            return True
        except S3Error as e:
            print(f"Error deleting file: {e}")
            return False

    def exists(self, file_url: str) -> bool:
        """检查文件是否存在"""
        try:
            # 从URL中提取对象名
            object_name = file_url.replace(f"{self.base_url}/", "")
            
            # 检查对象是否存在
            self.client.stat_object(
                bucket_name=self.bucket,
                object_name=object_name
            )
            
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            print(f"Error checking file existence: {e}")
            return False

    def get_url(self, file_url: str, expires_in: int = 3600) -> str:
        """获取访问URL"""
        try:
            # 从URL中提取对象名
            object_name = file_url.replace(f"{self.base_url}/", "")
            
            # 生成预签名URL
            presigned_url = self.client.presigned_get_object(
                bucket_name=self.bucket,
                object_name=object_name,
                expires=expires_in
            )
            
            return presigned_url
        except S3Error as e:
            print(f"Error getting presigned URL: {e}")
            return file_url

    def list_files(self, prefix: str = "") -> List[str]:
        """列出文件"""
        try:
            files = []
            
            # 列出对象
            objects = self.client.list_objects(
                bucket_name=self.bucket,
                prefix=prefix,
                recursive=True
            )
            
            for obj in objects:
                files.append(f"{self.base_url}/{obj.object_name}")
            
            return files
        except S3Error as e:
            print(f"Error listing files: {e}")
            return []

    def get_metadata(self, file_url: str) -> Dict[str, Any]:
        """获取文件元数据"""
        try:
            # 从URL中提取对象名
            object_name = file_url.replace(f"{self.base_url}/", "")
            
            # 获取对象元数据
            stat = self.client.stat_object(
                bucket_name=self.bucket,
                object_name=object_name
            )
            
            return {
                "size": stat.size,
                "mtime": stat.last_modified.timestamp(),
                "etag": stat.etag,
                "content_type": stat.content_type
            }
        except S3Error as e:
            print(f"Error getting file metadata: {e}")
            return {}


class AsyncMinioStorageBackend(AsyncStorageBackend):
    """异步Minio存储适配器"""

    def __init__(self, 
                 endpoint: str = "10.128.18.216:9000",
                 access_key: str = "admin",
                 secret_key: str = "password",
                 bucket: str = "agentx-files",
                 secure: bool = False,
                 region: str = "us-east-1",
                 base_url: str = None):
        self.sync_backend = MinioStorageBackend(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            bucket=bucket,
            secure=secure,
            region=region,
            base_url=base_url
        )

    async def save(self, file_content: bytes, filename: str, **kwargs) -> str:
        """保存文件，返回URL"""
        return self.sync_backend.save(file_content, filename, **kwargs)

    async def load(self, file_url: str) -> bytes:
        """加载文件内容"""
        return self.sync_backend.load(file_url)

    async def update(self, file_url: str, new_content: bytes) -> str:
        """更新文件"""
        return self.sync_backend.update(file_url, new_content)

    async def delete(self, file_url: str) -> bool:
        """删除文件"""
        return self.sync_backend.delete(file_url)

    async def exists(self, file_url: str) -> bool:
        """检查文件是否存在"""
        return self.sync_backend.exists(file_url)

    async def get_url(self, file_url: str, expires_in: int = 3600) -> str:
        """获取访问URL"""
        return self.sync_backend.get_url(file_url, expires_in)

    async def list_files(self, prefix: str = "") -> List[str]:
        """列出文件"""
        return self.sync_backend.list_files(prefix)

    async def get_metadata(self, file_url: str) -> Dict[str, Any]:
        """获取文件元数据"""
        return self.sync_backend.get_metadata(file_url)