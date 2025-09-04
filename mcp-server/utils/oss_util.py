# -*- coding: utf-8 -*-
import os
import logging
from typing import List, Optional
from dotenv import load_dotenv
import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class OSSUploader:
    """阿里云OSS上传工具类"""
    
    def __init__(self):
        """初始化OSS上传器"""
        # 从环境变量读取OSS配置
        self.access_key_id = os.getenv('OSS_ACCESS_KEY_ID')
        self.access_key_secret = os.getenv('OSS_ACCESS_KEY_SECRET')
        self.endpoint = os.getenv('OSS_ENDPOINT', 'oss-cn-shanghai.aliyuncs.com')
        self.bucket_name = os.getenv('OSS_BUCKET_NAME', 'story-board')
        self.cdn_domain = os.getenv('OSS_CDN_DOMAIN', 'static.chuangyi-keji.com')
        
        # 验证必要的配置
        if not self.access_key_id or not self.access_key_secret:
            raise ValueError("OSS_ACCESS_KEY_ID 和 OSS_ACCESS_KEY_SECRET 必须在.env文件中配置")
        
        # 设置环境变量供oss2使用
        os.environ['OSS_ACCESS_KEY_ID'] = self.access_key_id
        os.environ['OSS_ACCESS_KEY_SECRET'] = self.access_key_secret
        
        # 初始化OSS客户端
        self.auth = oss2.ProviderAuth(EnvironmentVariableCredentialsProvider())
        self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)
        
        logger.info(f"OSS上传器初始化完成，Bucket: {self.bucket_name}, Endpoint: {self.endpoint}")
    
    def upload_file(self, local_file_path: str, oss_path: str) -> bool:
        """
        上传单个文件到OSS
        
        Args:
            local_file_path: 本地文件路径
            oss_path: OSS存储路径
            
        Returns:
            bool: 上传是否成功
        """
        try:
            self.bucket.put_object_from_file(oss_path, local_file_path)
            logger.info(f"文件上传成功: {local_file_path} -> {oss_path}")
            return True
        except Exception as e:
            logger.error(f"文件上传失败: {local_file_path}, 错误: {str(e)}")
            return False
    
    def upload_image(self, image, save_name: str, save_path: str, oss_folder: str = 'generate_figure_images') -> Optional[str]:
        """
        上传图片到OSS
        
        Args:
            image: PIL Image对象
            save_name: 保存的文件名
            save_path: 本地保存路径
            oss_folder: OSS存储文件夹
            
        Returns:
            str: 图片URL，失败返回None
        """
        try:
            # 保存图片到本地
            save_path_final = os.path.join(save_path, save_name)
            image.save(save_path_final)
            
            # 上传到OSS
            oss_save_path = f'{oss_folder}/{save_name}'
            if self.upload_file(save_path_final, oss_save_path):
                # 获取CDN URL
                img_url = self.get_oss_url(oss_save_path)
                logger.info(f"图片上传成功，URL: {img_url}")
                return img_url
            else:
                return None
        except Exception as e:
            logger.error(f"图片上传失败: {save_name}, 错误: {str(e)}")
            return None
    
    def upload_images_batch(self, images: List, save_names: List[str], save_path: str, 
                           oss_folder: str = 'generate_figure_images') -> List[str]:
        """
        批量上传图片到OSS
        
        Args:
            images: PIL Image对象列表
            save_names: 保存的文件名列表
            save_path: 本地保存路径
            oss_folder: OSS存储文件夹
            
        Returns:
            List[str]: 图片URL列表
        """
        img_urls = []
        
        for save_name, img in zip(save_names, images):
            img_url = self.upload_image(img, save_name, save_path, oss_folder)
            if img_url:
                img_urls.append(img_url)
            else:
                logger.warning(f"图片上传失败: {save_name}")
        
        logger.info(f"批量上传完成，成功上传 {len(img_urls)}/{len(images)} 张图片")
        return img_urls
    
    def get_oss_url_with_sign_url(self, bucket_path: str, last_time: int = 9023372035211434538) -> str:
        """
        获取带签名的OSS URL
        
        Args:
            bucket_path: OSS存储路径
            last_time: 签名有效期（时间戳）
            
        Returns:
            str: 带签名的URL
        """
        try:
            url = self.bucket.sign_url('GET', bucket_path, last_time, slash_safe=True)
            # 替换为CDN域名
            url = url.replace(f"http://{self.bucket_name}.{self.endpoint}/", f"https://{self.cdn_domain}/")
            return url
        except Exception as e:
            logger.error(f"获取签名URL失败: {bucket_path}, 错误: {str(e)}")
            return ""
    
    def get_oss_url(self, bucket_path: str) -> str:
        """
        获取OSS CDN URL
        
        Args:
            bucket_path: OSS存储路径
            
        Returns:
            str: CDN URL
        """
        return f"https://{self.cdn_domain}/{bucket_path}"
    
    def delete_file(self, oss_path: str) -> bool:
        """
        删除OSS文件
        
        Args:
            oss_path: OSS存储路径
            
        Returns:
            bool: 删除是否成功
        """
        try:
            self.bucket.delete_object(oss_path)
            logger.info(f"文件删除成功: {oss_path}")
            return True
        except Exception as e:
            logger.error(f"文件删除失败: {oss_path}, 错误: {str(e)}")
            return False
    
    def list_files(self, prefix: str = "", max_keys: int = 100) -> List[str]:
        """
        列出OSS文件
        
        Args:
            prefix: 文件前缀
            max_keys: 最大返回数量
            
        Returns:
            List[str]: 文件路径列表
        """
        try:
            files = []
            for obj in oss2.ObjectIterator(self.bucket, prefix=prefix, max_keys=max_keys):
                files.append(obj.key)
            return files
        except Exception as e:
            logger.error(f"列出文件失败: {str(e)}")
            return []

# 全局OSS上传器实例
_oss_uploader = None

def get_oss_uploader() -> OSSUploader:
    """
    获取OSS上传器实例（单例模式）
    
    Returns:
        OSSUploader: OSS上传器实例
    """
    global _oss_uploader
    if _oss_uploader is None:
        _oss_uploader = OSSUploader()
    return _oss_uploader

# 便捷函数
def upload_image(image, save_name: str, save_path: str, oss_folder: str = 'generate_figure_images') -> Optional[str]:
    """便捷函数：上传单个图片"""
    return get_oss_uploader().upload_image(image, save_name, save_path, oss_folder)

def upload_images_batch(images: List, save_names: List[str], save_path: str, 
                       oss_folder: str = 'generate_figure_images') -> List[str]:
    """便捷函数：批量上传图片"""
    return get_oss_uploader().upload_images_batch(images, save_names, save_path, oss_folder)

def get_oss_url(bucket_path: str) -> str:
    """便捷函数：获取OSS URL"""
    return get_oss_uploader().get_oss_url(bucket_path)

# 视频上传接口
def upload_video_file(local_path: str, oss_folder: str = 'uploaded_videos') -> Optional[str]:
    """
    上传视频文件到 OSS 并返回 CDN URL

    Args:
        local_path (str): 本地视频文件路径
        oss_folder (str): OSS 存储文件夹（默认 'uploaded_videos'）

    Returns:
        Optional[str]: 上传成功后的 URL，失败返回 None
    """
    if not os.path.exists(local_path):
        logger.warning(f"视频文件不存在: {local_path}")
        return None

    basename = os.path.basename(local_path)
    oss_path = f"{oss_folder}/{basename}"

    uploader = get_oss_uploader()
    success = uploader.upload_file(local_path, oss_path)
    if success:
        return uploader.get_oss_url(oss_path)
    else:
        logger.error(f"视频上传失败: {local_path}")
        return None
