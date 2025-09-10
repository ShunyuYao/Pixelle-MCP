# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
import chainlit as cl
from datetime import datetime
import json
import traceback
import uvicorn
import threading
import asyncio
from core.core import logger

# 创建独立的FastAPI应用
app = FastAPI(title="MCP Tools API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 共享数据存储（用于API服务器与Chainlit应用之间的数据交换）
shared_data_store = {
    "current_steps": [],
    "last_updated": None
}


def format_tool_input_for_api(input_data: Any) -> Dict[str, Any]:
    """格式化工具输入参数供API返回"""
    if not input_data:
        return {}
    
    # 如果input_data是字符串，尝试解析为JSON，否则作为原始值返回
    if isinstance(input_data, str):
        try:
            # 尝试解析JSON字符串
            parsed_data = json.loads(input_data)
            if isinstance(parsed_data, dict):
                input_data = parsed_data
            else:
                # 如果解析后不是字典，作为原始值返回
                return {"raw_input": input_data}
        except json.JSONDecodeError:
            # 如果不是有效的JSON，作为原始字符串返回
            if len(input_data) > 500:
                return {
                    "raw_input": {
                        "value": input_data[:500] + "...",
                        "truncated": True,
                        "full_length": len(input_data)
                    }
                }
            else:
                return {"raw_input": input_data}
    
    # 如果不是字典类型，尝试转换为字典格式
    if not isinstance(input_data, dict):
        return {"value": str(input_data)}
    
    # 处理过长的值
    formatted_input = {}
    for key, value in input_data.items():
        if isinstance(value, str) and len(value) > 500:
            formatted_input[key] = {
                "value": value[:500] + "...",
                "truncated": True,
                "full_length": len(value)
            }
        elif isinstance(value, (dict, list)):
            try:
                json_str = json.dumps(value, ensure_ascii=False)
                if len(json_str) > 500:
                    formatted_input[key] = {
                        "value": json_str[:500] + "...",
                        "truncated": True,
                        "full_length": len(json_str),
                        "type": type(value).__name__
                    }
                else:
                    formatted_input[key] = value
            except Exception:
                formatted_input[key] = str(value)
        else:
            formatted_input[key] = value
    
    return formatted_input


def format_tool_output_for_api(output: str) -> Dict[str, Any]:
    """格式化工具输出结果供API返回"""
    if not output:
        return {"value": "", "truncated": False}
    
    # 移除时间标记
    clean_output = output
    if output.startswith("[Took "):
        bracket_end = output.find("]")
        if bracket_end != -1:
            clean_output = output[bracket_end + 1:].strip()
    
    # 处理过长的输出
    if len(clean_output) > 1000:
        return {
            "value": clean_output[:1000] + "...",
            "truncated": True,
            "full_length": len(clean_output)
        }
    else:
        return {
            "value": clean_output,
            "truncated": False,
            "full_length": len(clean_output)
        }


def extract_duration_from_output(output: str) -> Optional[str]:
    """从输出中提取执行时间"""
    try:
        if output and "[Took " in output:
            start = output.find("[Took ") + 6
            end = output.find("]", start)
            if end > start:
                return output[start:end]
    except Exception:
        pass
    return None


def determine_status_from_output(output: str) -> str:
    """确定执行状态"""
    if not output:
        return "pending"
    if '"error"' in output.lower() or "error" in output.lower():
        return "error"
    return "success"


def update_shared_data_store(steps_data=None):
    """更新共享数据存储"""
    try:
        if steps_data is not None:
            # 直接使用传入的数据
            shared_data_store["current_steps"] = steps_data
            shared_data_store["last_updated"] = datetime.now().isoformat()
            logger.debug(f"共享数据存储已更新，包含 {len(steps_data)} 个步骤")
        else:
            # 尝试从用户会话获取（可能无法访问）
            try:
                if hasattr(cl, 'user_session') and cl.user_session:
                    current_steps = cl.user_session.get("current_steps", [])
                    shared_data_store["current_steps"] = current_steps
                    shared_data_store["last_updated"] = datetime.now().isoformat()
                    logger.debug(f"共享数据存储已更新，包含 {len(current_steps)} 个步骤")
                else:
                    logger.debug("用户会话不可访问，跳过数据更新")
            except Exception as inner_e:
                logger.debug(f"从用户会话获取数据失败: {inner_e}")
    except Exception as e:
        logger.warning(f"更新共享数据存储失败: {e}")


@app.get("/api/tool-calls")
async def get_tool_calls():
    """获取当前会话的MCP工具调用记录"""
    try:
        # 从共享数据存储获取工具调用步骤
        current_steps = shared_data_store.get("current_steps", [])
        
        if not current_steps:
            return JSONResponse({
                "tools": [],
                "stats": {
                    "total": 0,
                    "success": 0,
                    "error": 0,
                    "pending": 0
                },
                "message": "No tool calls in current session",
                "timestamp": datetime.now().isoformat()
            })
        
        # 转换步骤为API响应格式
        tool_records = []
        for step in current_steps:
            if hasattr(step, 'name') and step.name:
                try:
                    # 提取基本信息
                    tool_name = step.name
                    tool_input = getattr(step, 'input', {}) or {}
                    tool_output = getattr(step, 'output', '') or ''
                    created_at = getattr(step, 'created_at', None)
                    
                    # 处理时间格式
                    timestamp = datetime.now().isoformat()
                    created_at_iso = None
                    
                    if created_at:
                        if isinstance(created_at, str):
                            # 如果 created_at 已经是字符串，直接使用
                            created_at_iso = created_at
                            timestamp = created_at
                        elif hasattr(created_at, 'isoformat'):
                            # 如果是 datetime 对象，转换为 ISO 格式
                            created_at_iso = created_at.isoformat()
                            timestamp = created_at_iso
                        else:
                            # 其他情况，尝试转换为字符串
                            created_at_iso = str(created_at)
                            timestamp = created_at_iso
                    
                    # 处理数据
                    formatted_input = format_tool_input_for_api(tool_input)
                    formatted_output = format_tool_output_for_api(tool_output)
                    duration = extract_duration_from_output(tool_output)
                    status = determine_status_from_output(tool_output)
                    
                    tool_record = {
                        "id": f"tool_{id(step)}",  # 使用对象ID作为唯一标识
                        "name": tool_name,
                        "input": formatted_input,
                        "output": formatted_output,
                        "status": status,
                        "duration": duration,
                        "timestamp": timestamp,
                        "created_at": created_at_iso
                    }
                    
                    tool_records.append(tool_record)
                    
                except Exception as e:
                    logger.warning(f"处理工具记录时出错: {e}")
                    logger.debug(f"步骤对象信息: name={getattr(step, 'name', 'N/A')}, input_type={type(getattr(step, 'input', None))}, input_value={getattr(step, 'input', None)}")
                    # 添加错误记录以便调试
                    tool_records.append({
                        "id": f"error_{id(step)}",
                        "name": f"解析错误: {getattr(step, 'name', 'Unknown')}",
                        "input": {"error": f"无法解析工具参数: {str(e)}"},
                        "output": {"value": f"解析失败: {str(e)}", "truncated": False},
                        "status": "error",
                        "duration": None,
                        "timestamp": datetime.now().isoformat(),
                        "created_at": None
                    })
        
        # 按时间倒序排序（最新的在前）
        tool_records.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # 限制返回数量（避免响应过大）
        MAX_RECORDS = 50
        limited_records = tool_records[:MAX_RECORDS]
        
        # 计算统计信息
        stats = {
            "total": len(tool_records),
            "success": len([r for r in tool_records if r["status"] == "success"]),
            "error": len([r for r in tool_records if r["status"] == "error"]),
            "pending": len([r for r in tool_records if r["status"] == "pending"]),
            "displayed": len(limited_records)
        }
        
        response_data = {
            "tools": limited_records,
            "stats": stats,
            "message": f"返回 {len(limited_records)} 条工具调用记录",
            "timestamp": datetime.now().isoformat(),
            "has_more": len(tool_records) > MAX_RECORDS
        }
        
        logger.debug(f"API返回了 {len(limited_records)} 条工具调用记录")
        return JSONResponse(response_data)
        
    except Exception as e:
        logger.error(f"获取工具调用记录时出错: {e}")
        logger.error(f"堆栈跟踪: {traceback.format_exc()}")
        
        return JSONResponse(
            status_code=500,
            content={
                "tools": [],
                "stats": {
                    "total": 0,
                    "success": 0,
                    "error": 0,
                    "pending": 0
                },
                "error": str(e),
                "message": "获取工具调用记录失败",
                "timestamp": datetime.now().isoformat()
            }
        )


@app.get("/api/tool-calls/{tool_id}")
async def get_tool_call_detail(tool_id: str):
    """获取特定工具调用的详细信息"""
    try:
        # 从共享数据存储获取工具调用步骤
        current_steps = shared_data_store.get("current_steps", [])
        
        # 查找指定的工具调用
        for step in current_steps:
            if hasattr(step, 'name') and step.name and f"tool_{id(step)}" == tool_id:
                tool_input = getattr(step, 'input', {}) or {}
                tool_output = getattr(step, 'output', '') or ''
                created_at = getattr(step, 'created_at', None)
                
                # 处理时间格式
                timestamp = datetime.now().isoformat()
                created_at_iso = None
                
                if created_at:
                    if isinstance(created_at, str):
                        created_at_iso = created_at
                        timestamp = created_at
                    elif hasattr(created_at, 'isoformat'):
                        created_at_iso = created_at.isoformat()
                        timestamp = created_at_iso
                    else:
                        created_at_iso = str(created_at)
                        timestamp = created_at_iso
                
                # 返回完整的详细信息（不截断）
                detail = {
                    "id": tool_id,
                    "name": step.name,
                    "input": tool_input,  # 完整输入
                    "output": tool_output,  # 完整输出
                    "status": determine_status_from_output(tool_output),
                    "duration": extract_duration_from_output(tool_output),
                    "timestamp": timestamp,
                    "created_at": created_at_iso
                }
                
                return JSONResponse(detail)
        
        # 未找到指定的工具调用
        return JSONResponse(
            status_code=404,
            content={
                "error": "Tool call not found",
                "message": f"未找到ID为 {tool_id} 的工具调用",
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"获取工具调用详情时出错: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "message": "获取工具调用详情失败",
                "timestamp": datetime.now().isoformat()
            }
        )


@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return JSONResponse({
        "status": "healthy",
        "service": "mcp-tools-api",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })


# API服务器管理
_api_server_thread = None
_api_server_running = False

def start_api_server(port: int = 9004):
    """在独立线程中启动API服务器"""
    global _api_server_thread, _api_server_running
    
    if _api_server_running:
        logger.info(f"API服务器已在端口 {port} 运行")
        return
    
    def run_server():
        try:
            logger.info(f"启动MCP工具API服务器，端口: {port}")
            uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
        except Exception as e:
            logger.error(f"API服务器启动失败: {e}")
    
    _api_server_thread = threading.Thread(target=run_server, daemon=True)
    _api_server_thread.start()
    _api_server_running = True
    
    logger.info(f"API服务器线程已启动，访问地址: http://localhost:{port}/api/health")


def stop_api_server():
    """停止API服务器"""
    global _api_server_running
    _api_server_running = False
    logger.info("API服务器已停止")


if __name__ == "__main__":
    # 独立运行API服务器
    uvicorn.run(app, host="0.0.0.0", port=9004)