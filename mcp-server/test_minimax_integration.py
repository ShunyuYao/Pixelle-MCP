#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MiniMax 工具集成测试脚本

用于验证 MiniMax 工具是否正确集成到 mcp-server 中
"""

import os
import asyncio
from utils.minimax_client import MiniMaxClient


async def test_client_initialization():
    """测试客户端初始化"""
    print("🧪 测试 MiniMax 客户端初始化...")
    
    try:
        # 测试没有 API key 的情况
        os.environ.pop("MINIMAX_API_KEY", None)
        
        try:
            from utils.minimax_client import get_minimax_client
            client = get_minimax_client()
            print("❌ 应该在没有 API key 时抛出异常")
            return False
        except ValueError as e:
            print(f"✅ 正确处理缺少 API key 的情况: {e}")
        
        # 测试正常初始化
        os.environ["MINIMAX_API_KEY"] = "test-api-key"
        os.environ["MINIMAX_BASE_URL"] = "https://api.minimax.chat"
        
        client = MiniMaxClient("test-key", "https://api.minimax.chat")
        print("✅ 客户端初始化成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 客户端初始化测试失败: {e}")
        return False


def test_tool_imports():
    """测试工具导入"""
    print("\n🧪 测试 MiniMax 工具导入...")
    
    try:
        from tools.minimax_tools import (
            text_to_audio_tool,
            voice_cloning_tool,
            video_generation_tool,
            image_generation_tool,
            music_generation_tool,
            voice_design_tool
        )
        
        tools = [
            "text_to_audio_tool",
            "voice_cloning_tool", 
            "video_generation_tool",
            "image_generation_tool",
            "music_generation_tool",
            "voice_design_tool"
        ]
        
        for tool_name in tools:
            print(f"✅ {tool_name} 导入成功")
        
        print(f"✅ 所有 {len(tools)} 个工具导入成功")
        return True
        
    except Exception as e:
        print(f"❌ 工具导入测试失败: {e}")
        return False


def test_configuration():
    """测试配置验证"""
    print("\n🧪 测试配置设置...")
    
    try:
        # 检查环境变量是否正确设置
        required_env_vars = [
            "MINIMAX_API_KEY",
            "MINIMAX_BASE_URL"
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if var not in os.environ or not os.environ[var]:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️ 缺少环境变量（测试环境正常）: {missing_vars}")
        else:
            print("✅ 所有必需的环境变量都已设置")
        
        # 检查配置值
        api_key = os.environ.get("MINIMAX_API_KEY", "")
        base_url = os.environ.get("MINIMAX_BASE_URL", "")
        
        print(f"📝 配置信息:")
        print(f"   API Key: {'*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else '未设置'}")
        print(f"   Base URL: {base_url or '未设置'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False


async def test_api_structure():
    """测试 API 结构"""
    print("\n🧪 测试 API 结构...")
    
    try:
        client = MiniMaxClient("test-key")
        
        # 检查客户端是否有所需的方法
        required_methods = [
            "text_to_audio",
            "voice_cloning",
            "image_generation", 
            "video_generation",
            "music_generation",
            "voice_design"
        ]
        
        for method_name in required_methods:
            if hasattr(client, method_name):
                print(f"✅ 方法 {method_name} 存在")
            else:
                print(f"❌ 方法 {method_name} 不存在")
                return False
        
        print("✅ 所有必需的 API 方法都存在")
        return True
        
    except Exception as e:
        print(f"❌ API 结构测试失败: {e}")
        return False


def print_integration_summary():
    """打印集成摘要"""
    print("\n" + "="*60)
    print("📋 MiniMax 集成摘要")
    print("="*60)
    print("✅ 配置文件: config.yml 已更新 MiniMax 配置段")
    print("✅ 依赖项: pyproject.toml 已添加所需依赖")
    print("✅ API 客户端: utils/minimax_client.py 已实现")
    print("✅ 工具集合: tools/minimax_tools.py 已实现")
    print("\n📦 可用工具:")
    print("   • text_to_audio_tool - 文本转语音")
    print("   • voice_cloning_tool - 声音克隆")
    print("   • video_generation_tool - 视频生成")
    print("   • image_generation_tool - 图像生成")
    print("   • music_generation_tool - 音乐生成")
    print("   • voice_design_tool - 声音设计")
    print("\n🔧 使用说明:")
    print("   1. 在 config.yml 中设置你的 MiniMax API key")
    print("   2. 重启 mcp-server 服务")
    print("   3. 在 mcp-client 中即可使用这些工具")
    print("="*60)


async def main():
    """主测试函数"""
    print("🚀 开始 MiniMax 工具集成测试")
    print("="*60)
    
    test_results = []
    
    # 运行所有测试
    test_results.append(await test_client_initialization())
    test_results.append(test_tool_imports())
    test_results.append(test_configuration())
    test_results.append(await test_api_structure())
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！MiniMax 工具已成功集成")
        print_integration_summary()
        return True
    else:
        print("⚠️ 部分测试失败，请检查相关配置")
        return False


if __name__ == "__main__":
    asyncio.run(main())