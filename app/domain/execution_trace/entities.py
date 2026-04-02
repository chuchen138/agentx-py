from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class AgentExecutionSummary(BaseModel):
    trace_id: str
    user_id: str
    session_id: str
    agent_id: str
    execution_start_time: datetime
    execution_end_time: Optional[datetime] = None
    total_execution_time: Optional[int] = None  # 毫秒
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    tool_call_count: int = 0
    total_tool_execution_time: int = 0
    execution_success: bool = True
    error_phase: Optional[str] = None
    error_message: Optional[str] = None
    is_fallback_used: bool = False
    fallback_reason: Optional[str] = None
    fallback_from_endpoint: Optional[str] = None
    fallback_to_endpoint: Optional[str] = None
    metadata: Dict[str, Any] = {}


class AgentExecutionDetail(BaseModel):
    trace_id: str
    step_id: str
    timestamp: datetime
    message_type: str  # USER_MESSAGE, AI_RESPONSE, MODEL_CALL, TOOL_CALL
    message_content: Optional[str] = None
    message_tokens: Optional[int] = None
    model_endpoint: Optional[str] = None
    provider_name: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    model_call_time: Optional[int] = None  # 毫秒
    tool_name: Optional[str] = None
    tool_request_args: Optional[str] = None
    tool_response_data: Optional[str] = None
    tool_execution_time: Optional[int] = None  # 毫秒
    tool_success: Optional[bool] = None
    is_fallback_used: bool = False
    fallback_reason: Optional[str] = None
    fallback_from_endpoint: Optional[str] = None
    fallback_to_endpoint: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
