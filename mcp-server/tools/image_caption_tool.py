# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import asyncio
import base64
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import Field

from core import mcp, logger
from utils.file_uploader import upload
from utils.file_util import download_files, create_temp_file

try:
    import litellm
    from litellm import acompletion
except ImportError:
    logger.error("litellm not installed. Please install it: pip install litellm")
    raise

# Gemini配置 - 从环境变量获取
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODELS", "gemini-2.5-flash").split(",")[0].strip() if os.getenv("GEMINI_MODELS") else "gemini-2.5-flash"

def encode_image_to_base64(image_path: str) -> str:
    """将图像文件编码为base64字符串"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"编码图像文件失败: {e}")
        return ""

def create_multimodal_message(text: str, image_path: str = None) -> List[Dict[str, Any]]:
    """创建多模态消息格式"""
    content = []
    
    # 添加文本内容
    if text.strip():
        content.append({
            "type": "text",
            "text": text
        })
    
    # 添加图像内容
    if image_path and os.path.exists(image_path):
        # 获取文件扩展名
        file_extension = Path(image_path).suffix.lower()
        mime_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }.get(file_extension, 'image/jpeg')
        
        # 编码图像
        base64_image = encode_image_to_base64(image_path)
        if base64_image:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_image}"
                }
            })
    
    return content

async def call_gemini_api(messages: List[Dict[str, Any]]) -> Optional[str]:
    """调用Gemini API"""
    if not GEMINI_API_KEY:
        logger.error("Gemini API key not configured")
        return None
    
    try:
        # 配置LiteLLM参数
        litellm_params = {
            "model": f"openai/{GEMINI_MODEL}",
            "messages": messages,
            "stream": False,
            "api_key": GEMINI_API_KEY,
            "base_url": GEMINI_BASE_URL,
            "timeout": 30,
        }
        
        logger.info(f"Calling Gemini API with model: {GEMINI_MODEL}")
        
        # 调用Gemini API
        response = await acompletion(**litellm_params)
        
        # 提取响应内容
        if response and response.choices:
            content = response.choices[0].message.content
            logger.info("Gemini API call successful")
            return content
        else:
            logger.error("No valid response from Gemini API")
            return None
            
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        return None

@mcp.tool(name="image_caption_tool")
async def image_caption_tool(
    image_url: str = Field(description="The URL of the image to analyze and describe"),
    # prompt: str = Field(
    #     default="Please describe the content of this image in detail, including the main subject, background, style, colors and other visual elements",
    #     description="The prompt to guide the image analysis. You can specify what aspects to focus on or ask specific questions about the image."
    # ),
    detail_level: str = Field(
        default="concise",
        description="The level of detail for the description. Options: 'concise', 'detailed', 'very_detailed'"
    )
):
    """
    Analyze and describe the content of an image using Gemini's vision capabilities.
    
    This tool is useful when:
    - Users upload an image and want to understand its content
    - You need to provide context about an image for further processing
    - Analyzing visual elements, objects, scenes, or people in images
    - Generating descriptions for accessibility or documentation purposes
    
    The tool will provide comprehensive analysis including:
    - Main subjects and objects in the image
    - Background and environment details
    - Visual style, composition, and artistic elements
    - Colors, lighting, and mood
    - Any text or symbols visible in the image
    
    If not specified detail_level, the tool will provide a concise description of the main content of the image.
    Use this tool whenever you need to understand or describe image content.
    """
    
    def error(msg: str):
        return json.dumps({"success": False, "error": msg})
    
    try:
        # 检查API配置
        if not GEMINI_API_KEY:
            return error("Gemini API key not configured. Please set GEMINI_API_KEY in config.yml")
        
        # 构建提示词
        detail_prompt = ""
        if detail_level == "concise":
            detail_prompt = "Please provide a concise description of the main content of the image."
        elif detail_level == "detailed":
            detail_prompt = "Please provide a detailed description of the image content, including the main subject, background, style, etc."
        elif detail_level == "very_detailed":
            detail_prompt = "Please provide a very detailed analysis of the image, including all visual elements, composition, colors, lighting, details, etc."
        
        full_prompt = detail_prompt # f"{prompt} {detail_prompt}"
        
        logger.info(f"Processing image: {image_url}")
        logger.info(f"Prompt: {full_prompt}")
        
        # 下载图像文件
        with download_files(image_url, '.jpg') as temp_image_path:
            # 创建多模态消息
            messages = [
                {
                    "role": "user",
                    "content": create_multimodal_message(full_prompt, temp_image_path)
                }
            ]
            
            # 调用Gemini API
            result = await call_gemini_api(messages)
            
            if result:
                # 构建返回结果
                response_data = {
                    "success": True,
                    "image_url": image_url,
                    "prompt": full_prompt,
                    "description": result,
                    "model": GEMINI_MODEL,
                    "detail_level": detail_level
                }
                
                logger.info("Image caption analysis completed successfully")
                return json.dumps(response_data, ensure_ascii=False, indent=2)
            else:
                return error("Failed to get response from Gemini API")
                
    except Exception as e:
        logger.error(f"Image caption tool failed: {e}")
        return error(f"Image caption analysis failed: {str(e)}")

@mcp.tool(name="image_analysis_tool")
async def image_analysis_tool(
    image_url: str = Field(description="The URL of the image to analyze"),
    analysis_type: str = Field(
        default="general",
        description="The type of analysis to perform. Options: 'general', 'objects', 'text', 'style', 'composition', 'emotion'"
    )
):
    """
    Perform specialized analysis on images using Gemini's vision capabilities.
    
    This tool provides different types of image analysis:
    - 'general': General image description and content analysis
    - 'objects': Identify and list all objects in the image
    - 'text': Extract and read any text visible in the image
    - 'style': Analyze the artistic style, technique, and visual aesthetics
    - 'composition': Analyze the composition, layout, and visual structure
    - 'emotion': Analyze the emotional content, mood, and atmosphere
    
    Use this tool when you need specific types of image analysis for different purposes.
    """
    
    def error(msg: str):
        return json.dumps({"success": False, "error": msg})
    
    try:
        # 检查API配置
        if not GEMINI_API_KEY:
            return error("Gemini API key not configured. Please set GEMINI_API_KEY in config.yml")
        
        # 根据分析类型构建提示词
        analysis_prompts = {
            "general": "Please comprehensively analyze the content of this image, including the main subject, background, style, colors and all visual elements.",
            "objects": "Please identify and list all objects, people, animals, etc. in the image, describing their positions and characteristics.",
            "text": "Please identify and extract all visible text content in the image, including titles, labels, captions, etc.",
            "style": "Please analyze the artistic style, creative techniques, and visual aesthetic features of this image, including color combinations, line usage, overall style, etc.",
            "composition": "Please analyze the composition, layout, and visual structure of this image, including subject positioning, background arrangement, spatial relationships, etc.",
            "emotion": "Please analyze the emotions, atmosphere, and mood conveyed by this image, including color emotions, lighting effects, overall feeling, etc."
        }
        
        prompt = analysis_prompts.get(analysis_type, analysis_prompts["general"])
        
        logger.info(f"Performing {analysis_type} analysis on image: {image_url}")
        
        # 下载图像文件
        with download_files(image_url, '.jpg') as temp_image_path:
            # 创建多模态消息
            messages = [
                {
                    "role": "user",
                    "content": create_multimodal_message(prompt, temp_image_path)
                }
            ]
            
            # 调用Gemini API
            result = await call_gemini_api(messages)
            
            if result:
                # 构建返回结果
                response_data = {
                    "success": True,
                    "image_url": image_url,
                    "analysis_type": analysis_type,
                    "analysis_result": result,
                    "model": GEMINI_MODEL,
                }
                
                logger.info(f"{analysis_type} analysis completed successfully")
                return json.dumps(response_data, ensure_ascii=False, indent=2)
            else:
                return error("Failed to get response from Gemini API")
                
    except Exception as e:
        logger.error(f"Image analysis tool failed: {e}")
        return error(f"Image analysis failed: {str(e)}")
