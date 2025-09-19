# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import asyncio
import json
import os
import tempfile
from typing import Dict, Any, Optional, Union
import httpx
from core import logger


class MiniMaxClient:
    """MiniMax API 客户端，支持文本转语音、图像生成、视频生成等功能"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.minimax.chat"):
        """
        初始化 MiniMax 客户端
        
        Args:
            api_key: MiniMax API 密钥
            base_url: API 基础 URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            endpoint: API 端点
            **kwargs: 其他请求参数
            
        Returns:
            API 响应数据
        """
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, headers=self.headers, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"MiniMax API request failed: {e}")
                raise Exception(f"API request failed: {str(e)}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise Exception(f"Invalid JSON response: {str(e)}")
    
    async def text_to_audio(self, text: str, voice_id: str = "female-aixia", **kwargs) -> Dict[str, Any]:
        """
        文本转语音
        
        Args:
            text: 要转换的文本
            voice_id: 声音 ID
            **kwargs: 其他参数（如语速、音量等）
            
        Returns:
            包含音频 URL 或数据的响应
        """
        data = {
            "voice_id": voice_id,
            "text": text,
            **kwargs
        }
        
        return await self._make_request("POST", "/v1/text_to_audio", json=data)
    
    async def voice_cloning(self, text: str, reference_audio_url: str, **kwargs) -> Dict[str, Any]:
        """
        声音克隆
        
        Args:
            text: 要合成的文本
            reference_audio_url: 参考音频 URL
            **kwargs: 其他参数
            
        Returns:
            包含克隆音频 URL 或数据的响应
        """
        data = {
            "text": text,
            "reference_audio_url": reference_audio_url,
            **kwargs
        }
        
        return await self._make_request("POST", "/v1/voice_cloning", json=data)
    
    async def image_generation(self, prompt: str, model: str = "abab6.5s-chat", **kwargs) -> Dict[str, Any]:
        """
        图像生成
        
        Args:
            prompt: 图像生成提示
            model: 使用的模型
            **kwargs: 其他参数（如尺寸、质量等）
            
        Returns:
            包含生成图像 URL 或数据的响应
        """
        data = {
            "model": model,
            "prompt": prompt,
            **kwargs
        }
        
        return await self._make_request("POST", "/v1/text_to_image", json=data)
    
    async def video_generation(self, prompt: str, model: str = "video-01", **kwargs) -> Dict[str, Any]:
        """
        视频生成
        
        Args:
            prompt: 视频生成提示
            model: 使用的模型
            **kwargs: 其他参数（如时长、质量等）
            
        Returns:
            包含生成视频 URL 或数据的响应
        """
        data = {
            "model": model,
            "prompt": prompt,
            **kwargs
        }
        
        return await self._make_request("POST", "/v1/video_generation", json=data)
    
    async def music_generation(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        音乐生成
        
        Args:
            prompt: 音乐生成提示
            **kwargs: 其他参数（如时长、风格等）
            
        Returns:
            包含生成音乐 URL 或数据的响应
        """
        data = {
            "prompt": prompt,
            **kwargs
        }
        
        return await self._make_request("POST", "/v1/music_generation", json=data)
    
    async def voice_design(self, description: str, **kwargs) -> Dict[str, Any]:
        """
        声音设计
        
        Args:
            description: 声音描述
            **kwargs: 其他参数
            
        Returns:
            包含设计声音 URL 或数据的响应
        """
        data = {
            "description": description,
            **kwargs
        }
        
        return await self._make_request("POST", "/v1/voice_design", json=data)
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态（用于异步任务）
        
        Args:
            task_id: 任务 ID
            
        Returns:
            任务状态信息
        """
        return await self._make_request("GET", f"/v1/query/{task_id}")
    
    async def wait_for_task_completion(self, task_id: str, max_wait_time: int = 300, 
                                     check_interval: int = 5) -> Dict[str, Any]:
        """
        等待异步任务完成
        
        Args:
            task_id: 任务 ID
            max_wait_time: 最大等待时间（秒）
            check_interval: 检查间隔（秒）
            
        Returns:
            完成的任务结果
        """
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            result = await self.get_task_status(task_id)
            
            status = result.get("status", "unknown")
            
            if status == "completed":
                return result
            elif status == "failed":
                raise Exception(f"Task failed: {result.get('error', 'Unknown error')}")
            
            await asyncio.sleep(check_interval)
            elapsed_time += check_interval
        
        raise Exception(f"Task timeout after {max_wait_time} seconds")


# 全局客户端实例
_minimax_client: Optional[MiniMaxClient] = None


def get_minimax_client() -> MiniMaxClient:
    """
    获取 MiniMax 客户端实例（单例）
    
    Returns:
        MiniMax 客户端实例
    """
    global _minimax_client
    
    if _minimax_client is None:
        api_key = os.getenv("MINIMAX_API_KEY")
        if not api_key:
            raise ValueError("MINIMAX_API_KEY environment variable is required")
        
        base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat")
        _minimax_client = MiniMaxClient(api_key, base_url)
    
    return _minimax_client