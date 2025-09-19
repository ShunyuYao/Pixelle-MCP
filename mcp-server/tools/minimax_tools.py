# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import json
import os
import tempfile
from typing import Optional
from pydantic import Field
from core import mcp, logger
from utils.minimax_client import get_minimax_client
from utils.file_uploader import upload


@mcp.tool(name="text_to_audio_tool")
async def text_to_audio_tool(
    text: str = Field(description="要转换为语音的文本内容"),
    voice_id: str = Field(default="female-aixia", description="声音 ID，可选值如: female-aixia, male-qn, etc."),
    speed: Optional[float] = Field(default=1.0, description="语速，范围 0.5-2.0"),
    volume: Optional[float] = Field(default=1.0, description="音量，范围 0.1-2.0")
):
    """
    使用 MiniMax API 将文本转换为语音。
    
    支持多种声音选择和参数调整，生成高质量的语音文件。
    """
    def error(msg: str):
        return json.dumps({"success": False, "error": msg})
    
    try:
        # 参数验证
        if not text.strip():
            return error("文本内容不能为空")
        
        if len(text) > 5000:
            return error("文本长度不能超过5000字符")
        
        if speed and (speed < 0.5 or speed > 2.0):
            return error("语速必须在0.5-2.0范围内")
        
        if volume and (volume < 0.1 or volume > 2.0):
            return error("音量必须在0.1-2.0范围内")
        
        # 获取 MiniMax 客户端
        client = get_minimax_client()
        
        # 调用文本转语音 API
        params = {"speed": speed, "volume": volume} if speed or volume else {}
        result = await client.text_to_audio(text, voice_id, **params)
        
        # 处理结果
        if "task_id" in result:
            # 异步任务，等待完成
            logger.info(f"Text-to-audio task started: {result['task_id']}")
            final_result = await client.wait_for_task_completion(result["task_id"])
        else:
            final_result = result
        
        # 检查是否有音频文件 URL
        audio_url = final_result.get("audio_url") or final_result.get("file_url")
        if not audio_url:
            return error("API 返回结果中未找到音频文件 URL")
        
        # 构建返回结果
        response = {
            "success": True,
            "audio_url": audio_url,
            "voice_id": voice_id,
            "text_length": len(text),
            "parameters": {
                "speed": speed,
                "volume": volume
            }
        }
        
        logger.info(f"Text-to-audio completed successfully: {audio_url}")
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except ValueError as e:
        logger.error(f"MiniMax client configuration error: {e}")
        return error("MiniMax API 配置错误，请检查 API 密钥设置")
    except Exception as e:
        logger.error(f"Text-to-audio failed: {e}")
        return error(f"文本转语音失败: {str(e)}")


@mcp.tool(name="voice_cloning_tool")
async def voice_cloning_tool(
    text: str = Field(description="要用克隆声音合成的文本"),
    reference_audio_url: str = Field(description="参考音频文件的URL，用于克隆声音特征"),
    similarity: Optional[float] = Field(default=0.8, description="声音相似度，范围 0.1-1.0")
):
    """
    使用 MiniMax API 进行声音克隆，根据参考音频生成指定文本的语音。
    
    需要提供参考音频文件来学习声音特征，然后生成指定文本的语音。
    """
    def error(msg: str):
        return json.dumps({"success": False, "error": msg})
    
    try:
        # 参数验证
        if not text.strip():
            return error("文本内容不能为空")
        
        if not reference_audio_url:
            return error("参考音频 URL 不能为空")
        
        if len(text) > 3000:
            return error("文本长度不能超过3000字符")
        
        if similarity and (similarity < 0.1 or similarity > 1.0):
            return error("相似度必须在0.1-1.0范围内")
        
        # 获取 MiniMax 客户端
        client = get_minimax_client()
        
        # 调用声音克隆 API
        params = {"similarity": similarity} if similarity else {}
        result = await client.voice_cloning(text, reference_audio_url, **params)
        
        # 处理异步任务
        if "task_id" in result:
            logger.info(f"Voice cloning task started: {result['task_id']}")
            final_result = await client.wait_for_task_completion(result["task_id"])
        else:
            final_result = result
        
        # 检查结果
        audio_url = final_result.get("audio_url") or final_result.get("file_url")
        if not audio_url:
            return error("API 返回结果中未找到音频文件 URL")
        
        response = {
            "success": True,
            "cloned_audio_url": audio_url,
            "reference_audio_url": reference_audio_url,
            "text_length": len(text),
            "similarity": similarity
        }
        
        logger.info(f"Voice cloning completed successfully: {audio_url}")
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except ValueError as e:
        logger.error(f"MiniMax client configuration error: {e}")
        return error("MiniMax API 配置错误，请检查 API 密钥设置")
    except Exception as e:
        logger.error(f"Voice cloning failed: {e}")
        return error(f"声音克隆失败: {str(e)}")


@mcp.tool(name="video_generation_tool")
async def video_generation_tool(
    prompt: str = Field(description="视频生成的描述提示，详细描述想要的视频内容"),
    duration: Optional[int] = Field(default=5, description="视频时长（秒），通常为3-10秒"),
    quality: Optional[str] = Field(default="standard", description="视频质量: standard, high"),
    aspect_ratio: Optional[str] = Field(default="16:9", description="视频宽高比: 16:9, 9:16, 1:1")
):
    """
    使用 MiniMax API 根据文本描述生成视频。
    
    支持多种分辨率和质量设置，可以生成短视频内容。
    """
    def error(msg: str):
        return json.dumps({"success": False, "error": msg})
    
    try:
        # 参数验证
        if not prompt.strip():
            return error("视频描述提示不能为空")
        
        if len(prompt) > 1000:
            return error("提示文本长度不能超过1000字符")
        
        if duration and (duration < 3 or duration > 10):
            return error("视频时长必须在3-10秒之间")
        
        valid_qualities = ["standard", "high"]
        if quality and quality not in valid_qualities:
            return error(f"质量参数必须是: {', '.join(valid_qualities)}")
        
        valid_ratios = ["16:9", "9:16", "1:1"]
        if aspect_ratio and aspect_ratio not in valid_ratios:
            return error(f"宽高比必须是: {', '.join(valid_ratios)}")
        
        # 获取 MiniMax 客户端
        client = get_minimax_client()
        
        # 调用视频生成 API
        params = {}
        if duration:
            params["duration"] = duration
        if quality:
            params["quality"] = quality
        if aspect_ratio:
            params["aspect_ratio"] = aspect_ratio
        
        result = await client.video_generation(prompt, **params)
        
        # 处理异步任务
        if "task_id" in result:
            logger.info(f"Video generation task started: {result['task_id']}")
            final_result = await client.wait_for_task_completion(
                result["task_id"], max_wait_time=600  # 视频生成可能需要更长时间
            )
        else:
            final_result = result
        
        # 检查结果
        video_url = final_result.get("video_url") or final_result.get("file_url")
        if not video_url:
            return error("API 返回结果中未找到视频文件 URL")
        
        response = {
            "success": True,
            "video_url": video_url,
            "prompt": prompt,
            "parameters": {
                "duration": duration,
                "quality": quality,
                "aspect_ratio": aspect_ratio
            }
        }
        
        logger.info(f"Video generation completed successfully: {video_url}")
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except ValueError as e:
        logger.error(f"MiniMax client configuration error: {e}")
        return error("MiniMax API 配置错误，请检查 API 密钥设置")
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        return error(f"视频生成失败: {str(e)}")


@mcp.tool(name="image_generation_tool")
async def image_generation_tool(
    prompt: str = Field(description="图像生成的描述提示，详细描述想要的图像内容"),
    width: Optional[int] = Field(default=1024, description="图像宽度，建议值: 512, 768, 1024"),
    height: Optional[int] = Field(default=1024, description="图像高度，建议值: 512, 768, 1024"),
    style: Optional[str] = Field(default="realistic", description="图像风格: realistic, anime, artistic, etc.")
):
    """
    使用 MiniMax API 根据文本描述生成图像。
    
    支持多种尺寸和风格设置，可以生成高质量的图像。
    """
    def error(msg: str):
        return json.dumps({"success": False, "error": msg})
    
    try:
        # 参数验证
        if not prompt.strip():
            return error("图像描述提示不能为空")
        
        if len(prompt) > 1000:
            return error("提示文本长度不能超过1000字符")
        
        if width and (width < 256 or width > 2048):
            return error("图像宽度必须在256-2048像素之间")
        
        if height and (height < 256 or height > 2048):
            return error("图像高度必须在256-2048像素之间")
        
        # 获取 MiniMax 客户端
        client = get_minimax_client()
        
        # 调用图像生成 API
        params = {}
        if width:
            params["width"] = width
        if height:
            params["height"] = height
        if style:
            params["style"] = style
        
        result = await client.image_generation(prompt, **params)
        
        # 处理异步任务
        if "task_id" in result:
            logger.info(f"Image generation task started: {result['task_id']}")
            final_result = await client.wait_for_task_completion(result["task_id"])
        else:
            final_result = result
        
        # 检查结果
        image_url = final_result.get("image_url") or final_result.get("file_url")
        if not image_url:
            return error("API 返回结果中未找到图像文件 URL")
        
        response = {
            "success": True,
            "image_url": image_url,
            "prompt": prompt,
            "parameters": {
                "width": width,
                "height": height,
                "style": style
            }
        }
        
        logger.info(f"Image generation completed successfully: {image_url}")
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except ValueError as e:
        logger.error(f"MiniMax client configuration error: {e}")
        return error("MiniMax API 配置错误，请检查 API 密钥设置")
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return error(f"图像生成失败: {str(e)}")


@mcp.tool(name="music_generation_tool")
async def music_generation_tool(
    prompt: str = Field(description="音乐生成的描述提示，描述想要的音乐风格、情感、节奏等"),
    duration: Optional[int] = Field(default=30, description="音乐时长（秒），通常为15-60秒"),
    genre: Optional[str] = Field(default="pop", description="音乐类型: pop, rock, jazz, classical, electronic, etc.")
):
    """
    使用 MiniMax API 根据文本描述生成音乐。
    
    支持多种音乐风格和时长设置，可以生成背景音乐或完整乐曲。
    """
    def error(msg: str):
        return json.dumps({"success": False, "error": msg})
    
    try:
        # 参数验证
        if not prompt.strip():
            return error("音乐描述提示不能为空")
        
        if len(prompt) > 500:
            return error("提示文本长度不能超过500字符")
        
        if duration and (duration < 15 or duration > 120):
            return error("音乐时长必须在15-120秒之间")
        
        # 获取 MiniMax 客户端
        client = get_minimax_client()
        
        # 调用音乐生成 API
        params = {}
        if duration:
            params["duration"] = duration
        if genre:
            params["genre"] = genre
        
        result = await client.music_generation(prompt, **params)
        
        # 处理异步任务
        if "task_id" in result:
            logger.info(f"Music generation task started: {result['task_id']}")
            final_result = await client.wait_for_task_completion(
                result["task_id"], max_wait_time=600  # 音乐生成可能需要更长时间
            )
        else:
            final_result = result
        
        # 检查结果
        music_url = final_result.get("music_url") or final_result.get("file_url")
        if not music_url:
            return error("API 返回结果中未找到音乐文件 URL")
        
        response = {
            "success": True,
            "music_url": music_url,
            "prompt": prompt,
            "parameters": {
                "duration": duration,
                "genre": genre
            }
        }
        
        logger.info(f"Music generation completed successfully: {music_url}")
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except ValueError as e:
        logger.error(f"MiniMax client configuration error: {e}")
        return error("MiniMax API 配置错误，请检查 API 密钥设置")
    except Exception as e:
        logger.error(f"Music generation failed: {e}")
        return error(f"音乐生成失败: {str(e)}")


@mcp.tool(name="voice_design_tool")
async def voice_design_tool(
    description: str = Field(description="声音特征描述，如年龄、性别、音色、情感等"),
    age_range: Optional[str] = Field(default="adult", description="年龄范围: child, teen, adult, elderly"),
    gender: Optional[str] = Field(default="neutral", description="性别: male, female, neutral"),
    emotion: Optional[str] = Field(default="neutral", description="情感: happy, sad, angry, calm, neutral")
):
    """
    使用 MiniMax API 根据描述设计定制化的声音。
    
    可以指定年龄、性别、情感等特征来创建独特的声音特性。
    """
    def error(msg: str):
        return json.dumps({"success": False, "error": msg})
    
    try:
        # 参数验证
        if not description.strip():
            return error("声音描述不能为空")
        
        if len(description) > 300:
            return error("描述长度不能超过300字符")
        
        valid_ages = ["child", "teen", "adult", "elderly"]
        if age_range and age_range not in valid_ages:
            return error(f"年龄范围必须是: {', '.join(valid_ages)}")
        
        valid_genders = ["male", "female", "neutral"]
        if gender and gender not in valid_genders:
            return error(f"性别必须是: {', '.join(valid_genders)}")
        
        valid_emotions = ["happy", "sad", "angry", "calm", "neutral", "excited", "gentle"]
        if emotion and emotion not in valid_emotions:
            return error(f"情感必须是: {', '.join(valid_emotions)}")
        
        # 获取 MiniMax 客户端
        client = get_minimax_client()
        
        # 调用声音设计 API
        params = {}
        if age_range:
            params["age_range"] = age_range
        if gender:
            params["gender"] = gender
        if emotion:
            params["emotion"] = emotion
        
        result = await client.voice_design(description, **params)
        
        # 处理异步任务
        if "task_id" in result:
            logger.info(f"Voice design task started: {result['task_id']}")
            final_result = await client.wait_for_task_completion(result["task_id"])
        else:
            final_result = result
        
        # 检查结果
        voice_id = final_result.get("voice_id")
        voice_sample_url = final_result.get("voice_sample_url")
        
        if not voice_id and not voice_sample_url:
            return error("API 返回结果中未找到声音 ID 或样本文件")
        
        response = {
            "success": True,
            "voice_id": voice_id,
            "voice_sample_url": voice_sample_url,
            "description": description,
            "parameters": {
                "age_range": age_range,
                "gender": gender,
                "emotion": emotion
            }
        }
        
        logger.info(f"Voice design completed successfully: {voice_id}")
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except ValueError as e:
        logger.error(f"MiniMax client configuration error: {e}")
        return error("MiniMax API 配置错误，请检查 API 密钥设置")
    except Exception as e:
        logger.error(f"Voice design failed: {e}")
        return error(f"声音设计失败: {str(e)}")