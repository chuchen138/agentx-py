from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from .trace_context import TraceContext


class ExecutionStartEvent(BaseModel):
    trace_context: TraceContext
    user_message: Optional[str] = None
    user_message_id: Optional[str] = None
    timestamp: datetime = datetime.utcnow()


class ExecutionEndEvent(BaseModel):
    trace_context: TraceContext
    execution_success: bool = True
    error_phase: Optional[str] = None
    error_message: Optional[str] = None
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    tool_call_count: int = 0
    total_tool_execution_time: int = 0
    is_fallback_used: bool = False
    fallback_reason: Optional[str] = None
    fallback_from_endpoint: Optional[str] = None
    fallback_to_endpoint: Optional[str] = None
    timestamp: datetime = datetime.utcnow()


class ModelCallEvent(BaseModel):
    trace_context: TraceContext
    model_endpoint: str
    provider_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model_call_time: int  # 毫秒
    ai_response: Optional[str] = None
    is_fallback_used: bool = False
    fallback_reason: Optional[str] = None
    fallback_from_endpoint: Optional[str] = None
    fallback_to_endpoint: Optional[str] = None
    timestamp: datetime = datetime.utcnow()


class ToolCallEvent(BaseModel):
    trace_context: TraceContext
    tool_name: str
    tool_request_args: str
    tool_response_data: str
    tool_execution_time: int  # 毫秒
    tool_success: bool
    error_message: Optional[str] = None
    is_fallback_used: bool = False
    fallback_reason: Optional[str] = None
    fallback_from_endpoint: Optional[str] = None
    fallback_to_endpoint: Optional[str] = None
    timestamp: datetime = datetime.utcnow()
