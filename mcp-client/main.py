# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import chainlit as cl
from chainlit.mcp import McpConnection
from mcp import ClientSession
import utils.llm_util as llm_util
from converters.message_converter import messages_from_chaintlit_to_openai
import chat.starters as starters
import auth.auth as auth

from core.core import logger
from core.prompt import DEFAULT_SYSTEM_PROMPT
from converters.tool_converter import tools_from_chaintlit_to_openai
from chat.chat_handler import handle_mcp_connect, handle_mcp_disconnect
from chat.chat_settings import setup_chat_settings, setup_settings_update
import chat.chat_handler as tool_handler
from chat.tool_sidebar import update_sidebar
from utils.file_uploader import upload
from api_endpoints import start_api_server, update_shared_data_store


@cl.set_chat_profiles
async def chat_profile(user: cl.User | None) -> list[cl.ChatProfile]:
    models = llm_util.get_all_models()
    default_model = llm_util.get_default_model()
    default_model_name = default_model.name if default_model else None
    return [
        cl.ChatProfile(
            name=model.name,
            markdown_description=f"Use **{model.name}** to talk with you.",
            default=default_model_name == model.name,
        )
        for model in models
    ]

@cl.on_chat_start
async def start():
    """初始化聊天会话"""
    await setup_chat_settings()
    
    # 启动API服务器（仅启动一次）
    start_api_server(port=9004)
    
    # 从settings中获取系统提示词，如果没有则使用默认值
    settings = cl.user_session.get("settings", {})
    system_prompt = settings.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
    
    sys_message = cl.Message(
        type="system_message",
        content=system_prompt
    )
    cl.chat_context.add(sys_message)
    
    # 初始化侧边栏（保持兼容性）
    await update_sidebar()
    
    # 更新共享数据存储
    update_shared_data_store()
    
@cl.on_settings_update
async def on_settings_update(settings):
    await setup_settings_update(settings)

@cl.on_mcp_connect
async def on_mcp(connection: McpConnection, session: ClientSession) -> None:
    """处理 MCP 连接"""
    await handle_mcp_connect(connection, session, tools_from_chaintlit_to_openai)
    cl.user_session.set("mcp_session", session)


@cl.on_mcp_disconnect
async def on_mcp_disconnect(name: str, session: ClientSession):
    """MCP 连接断开时调用"""
    logger.info(f"MCP 连接已断开: {name}")
    await handle_mcp_disconnect(name)


@cl.on_message
async def on_message(message: cl.Message):
    """处理用户消息"""
    # 检查是否为starter消息，如果已处理则直接返回
    is_handled = await starters.hook_by_starters(message)
    if is_handled:
        return
    
    need_update = False
    for element in message.elements:
        is_media = isinstance(element, cl.Image) \
            or isinstance(element, cl.Audio) \
            or isinstance(element, cl.Video)
        if is_media and element.path and not element.url:
            element.size = "small"
            element.url = upload(element.path, filename=element.name)
            need_update = True
    if need_update:
        await message.update()
    
    cl_messages = cl.chat_context.get()
    messages = messages_from_chaintlit_to_openai(cl_messages)
    
    # 使用工具处理器处理流式响应和工具调用
    chat_profile = cl.user_session.get("chat_profile")
    model_info = llm_util.get_model_info_by_name(chat_profile)
    await tool_handler.process_streaming_response(
        messages=messages,
        model_info=model_info,
    )
    
    # 更新侧边栏显示最新的工具调用记录
    await update_sidebar()
    
    # 更新共享数据存储供API使用
    update_shared_data_store()


if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)
