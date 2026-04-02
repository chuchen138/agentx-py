from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AgentExecutionSummaryModel(Base):
    __tablename__ = "agent_execution_summary"
    
    trace_id = Column(String(100), primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    session_id = Column(String(100), index=True, nullable=False)
    agent_id = Column(String(100), index=True, nullable=False)
    execution_start_time = Column(DateTime, index=True, nullable=False)
    execution_end_time = Column(DateTime, nullable=True)
    total_execution_time = Column(Integer, nullable=True)  # 毫秒
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    tool_call_count = Column(Integer, default=0)
    total_tool_execution_time = Column(Integer, default=0)
    execution_success = Column(Boolean, default=True)
    error_phase = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    is_fallback_used = Column(Boolean, default=False)
    fallback_reason = Column(String(100), nullable=True)
    fallback_from_endpoint = Column(String(100), nullable=True)
    fallback_to_endpoint = Column(String(100), nullable=True)
    metadata_ = Column(JSON, default={}, name="metadata")


class AgentExecutionDetailModel(Base):
    __tablename__ = "agent_execution_details"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String(100), ForeignKey("agent_execution_summary.trace_id"), index=True, nullable=False)
    step_id = Column(String(100), index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    message_type = Column(String(50), index=True, nullable=False)  # USER_MESSAGE, AI_RESPONSE, MODEL_CALL, TOOL_CALL
    message_content = Column(Text, nullable=True)
    message_tokens = Column(Integer, nullable=True)
    model_endpoint = Column(String(100), nullable=True)
    provider_name = Column(String(100), nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    model_call_time = Column(Integer, nullable=True)  # 毫秒
    tool_name = Column(String(100), nullable=True)
    tool_request_args = Column(Text, nullable=True)
    tool_response_data = Column(Text, nullable=True)
    tool_execution_time = Column(Integer, nullable=True)  # 毫秒
    tool_success = Column(Boolean, nullable=True)
    is_fallback_used = Column(Boolean, default=False)
    fallback_reason = Column(String(100), nullable=True)
    fallback_from_endpoint = Column(String(100), nullable=True)
    fallback_to_endpoint = Column(String(100), nullable=True)
    user_id = Column(String(100), index=True, nullable=True)
    metadata_ = Column(JSON, default={}, name="metadata")
