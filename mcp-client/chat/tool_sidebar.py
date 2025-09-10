# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import json
import chainlit as cl
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.time_util import format_duration
from core.core import logger

class ToolCallRecord:
    """工具调用记录类 - 数据处理和格式化"""
    
    def __init__(self, step: cl.Step):
        self.name = step.name or "Unknown Tool"
        self.input = step.input or {}
        self.output = step.output or ""
        self.created_at = step.created_at
        self.duration = self._extract_duration(step.output)
        self.status = self._determine_status(step.output)
        self.step_id = id(step)  # 用于唯一标识
        
    def _extract_duration(self, output: str) -> Optional[str]:
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
    
    def _determine_status(self, output: str) -> str:
        """确定执行状态"""
        if not output:
            return "pending"
        if '"error"' in output.lower() or "error" in output.lower():
            return "error"
        return "success"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": f"tool_{self.step_id}",
            "name": self.name,
            "input": self.input,
            "output": self.output,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "duration": self.duration,
            "status": self.status,
            "timestamp": self.created_at.isoformat() if self.created_at else datetime.now().isoformat()
        }


def get_current_tool_calls() -> List[ToolCallRecord]:
    """获取当前会话的工具调用记录"""
    try:
        current_steps = cl.user_session.get("current_steps", [])
        tool_records = []
        
        for step in current_steps:
            if hasattr(step, 'name') and step.name:
                try:
                    tool_records.append(ToolCallRecord(step))
                except Exception as e:
                    logger.warning(f"处理工具记录时出错: {e}")
        
        return tool_records
        
    except Exception as e:
        logger.error(f"获取工具调用记录时出错: {e}")
        return []


def get_tool_statistics() -> Dict[str, Any]:
    """获取工具使用统计"""
    try:
        tool_records = get_current_tool_calls()
        
        if not tool_records:
            return {"total": 0, "success": 0, "error": 0, "pending": 0, "tools": {}}
        
        stats = {
            "total": len(tool_records),
            "success": len([r for r in tool_records if r.status == "success"]),
            "error": len([r for r in tool_records if r.status == "error"]),
            "pending": len([r for r in tool_records if r.status == "pending"]),
            "tools": {}
        }
        
        # 按工具名称统计
        for record in tool_records:
            tool_name = record.name
            if tool_name not in stats["tools"]:
                stats["tools"][tool_name] = {"count": 0, "success": 0, "error": 0, "pending": 0}
            
            stats["tools"][tool_name]["count"] += 1
            stats["tools"][tool_name][record.status] += 1
        
        return stats
        
    except Exception as e:
        logger.error(f"获取工具统计时出错: {e}")
        return {"total": 0, "success": 0, "error": 0, "pending": 0, "tools": {}}


# 兼容性保持 - 移除旧的侧边栏更新函数，仅保留数据处理功能
async def update_sidebar():
    """已弃用 - 使用API接口获取数据"""
    logger.warning("update_sidebar() 函数已弃用，请使用 API 接口获取工具调用数据")
    pass