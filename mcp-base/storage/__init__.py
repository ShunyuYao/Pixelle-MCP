# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

"""
存储模块
提供多种存储后端的统一接口
"""

from .base import StorageBackend, FileInfo
from .local_storage import LocalStorage
from .oss_storage import OSSStorage
from config.settings import settings, StorageType


class StorageFactory:
    """存储后端工厂类"""
    
    @staticmethod
    def create_storage() -> StorageBackend:
        """根据配置创建存储后端"""
        if settings.storage_type == StorageType.LOCAL:
            return LocalStorage()
        elif settings.storage_type == StorageType.OSS:
            return OSSStorage()
        else:
            raise ValueError(f"Unsupported storage type: {settings.storage_type}")


# 全局存储实例
storage = StorageFactory.create_storage()


__all__ = [
    "StorageBackend", 
    "FileInfo", 
    "LocalStorage", 
    "OSSStorage",
    "StorageFactory", 
    "storage"
] 