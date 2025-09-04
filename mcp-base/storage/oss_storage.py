# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""
阿里云OSS存储实现
将文件存储到阿里云OSS
"""

import os
import uuid
import aiofiles
from pathlib import Path
from typing import BinaryIO, Optional
import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider

from .base import StorageBackend, FileInfo
from config.settings import settings


class OSSStorage(StorageBackend):
    """阿里云OSS文件存储"""
    
    def __init__(self, 
                 access_key_id: Optional[str] = None,
                 access_key_secret: Optional[str] = None,
                 endpoint: Optional[str] = None,
                 bucket_name: Optional[str] = None,
                 cdn_domain: Optional[str] = None):
        
        # 从环境变量或参数获取OSS配置
        self.access_key_id = access_key_id or os.getenv('OSS_ACCESS_KEY_ID')
        self.access_key_secret = access_key_secret or os.getenv('OSS_ACCESS_KEY_SECRET')
        self.endpoint = endpoint or os.getenv('OSS_ENDPOINT', 'oss-cn-shanghai.aliyuncs.com')
        self.bucket_name = bucket_name or os.getenv('OSS_BUCKET_NAME', 'story-board')
        self.cdn_domain = cdn_domain or os.getenv('OSS_CDN_DOMAIN', 'static.chuangyi-keji.com')
        
        # 验证必要的配置
        if not self.access_key_id or not self.access_key_secret:
            raise ValueError("OSS_ACCESS_KEY_ID 和 OSS_ACCESS_KEY_SECRET 必须配置")
        
        # 设置环境变量供oss2使用
        os.environ['OSS_ACCESS_KEY_ID'] = self.access_key_id
        os.environ['OSS_ACCESS_KEY_SECRET'] = self.access_key_secret
        
        # 初始化OSS客户端
        self.auth = oss2.ProviderAuth(EnvironmentVariableCredentialsProvider())
        self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)
    
    def _generate_file_id(self, filename: str) -> str:
        """生成唯一的文件ID"""
        # 保留文件扩展名
        ext = Path(filename).suffix
        return f"{uuid.uuid4().hex}{ext}"
    
    def _get_oss_path(self, file_id: str) -> str:
        """获取OSS存储路径"""
        return f"mcp_base_files/{file_id}"
    
    def _get_file_url(self, file_id: str) -> str:
        """获取文件的访问URL（使用CDN）"""
        oss_path = self._get_oss_path(file_id)
        return f"https://{self.cdn_domain}/{oss_path}"
    
    async def upload(
        self, 
        file_data: BinaryIO, 
        filename: str, 
        content_type: str
    ) -> FileInfo:
        """上传文件到OSS"""
        
        # 生成唯一文件ID
        file_id = self._generate_file_id(filename)
        oss_path = self._get_oss_path(file_id)
        
        try:
            # 读取文件内容
            content = file_data.read()
            file_size = len(content)
            
            # 上传到OSS
            self.bucket.put_object(oss_path, content)
            
            return FileInfo(
                file_id=file_id,
                filename=filename,
                content_type=content_type,
                size=file_size,
                url=self._get_file_url(file_id)
            )
        except Exception as e:
            raise Exception(f"OSS上传失败: {str(e)}")
    
    async def download(self, file_id: str) -> Optional[bytes]:
        """从OSS下载文件"""
        oss_path = self._get_oss_path(file_id)
        
        try:
            # 从OSS下载文件
            result = self.bucket.get_object(oss_path)
            return result.read()
        except Exception:
            return None
    
    async def delete(self, file_id: str) -> bool:
        """删除OSS文件"""
        oss_path = self._get_oss_path(file_id)
        
        try:
            self.bucket.delete_object(oss_path)
            return True
        except Exception:
            return False
    
    async def exists(self, file_id: str) -> bool:
        """检查OSS文件是否存在"""
        oss_path = self._get_oss_path(file_id)
        
        try:
            return self.bucket.object_exists(oss_path)
        except Exception:
            return False
    
    async def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """获取OSS文件信息"""
        oss_path = self._get_oss_path(file_id)
        
        try:
            # 获取OSS对象信息
            object_info = self.bucket.head_object(oss_path)
            
            return FileInfo(
                file_id=file_id,
                filename=file_id,  # OSS中存储的是file_id
                content_type=object_info.content_type,
                size=object_info.content_length,
                url=self._get_file_url(file_id)
            )
        except Exception:
            return None
