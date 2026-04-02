import hashlib
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from .trace_context import TraceContext
from .event_publisher import EventPublisher
from .events import ExecutionStartEvent, ExecutionEndEvent, ModelCallEvent, ToolCallEvent


class TraceCollector:
    def __init__(self, event_publisher: EventPublisher):
        self.event_publisher = event_publisher
        self.sampling_rate = 0.1  # 默认采样率 10%
        self.enabled = True
        
    def start_trace(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
        user_message: Optional[str] = None,
        user_message_id: Optional[str] = None
    ) -> TraceContext:
        """开始追踪"""
        try:
            if not self.enabled:
                # 返回禁用的上下文
                return TraceContext(
                    trace_id=str(uuid.uuid4()),
                    user_id=user_id,
                    session_id=session_id,
                    agent_id=agent_id,
                    enabled=False
                )
            
            # 生成 trace_id
            trace_id = f"trace_{datetime.utcnow().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8]}"
            
            # 检查是否需要采样
            if not self._should_sample(trace_id, user_id):
                return TraceContext(
                    trace_id=trace_id,
                    user_id=user_id,
                    session_id=session_id,
                    agent_id=agent_id,
                    enabled=False
                )
            
            # 创建 TraceContext
            trace_context = TraceContext(
                trace_id=trace_id,
                user_id=user_id,
                session_id=session_id,
                agent_id=agent_id,
                span_id=str(uuid.uuid4()),
                parent_span_id=None
            )
            
            # 发布执行开始事件
            event = ExecutionStartEvent(
                trace_context=trace_context,
                user_message=user_message,
                user_message_id=user_message_id
            )
            # 直接调用 publish 方法（在测试中使用同步方式）
            import asyncio
            asyncio.run(self.event_publisher.publish(event))
            
            return trace_context
        except Exception:
            # 追踪失败时返回禁用的上下文
            return TraceContext(
                trace_id=str(uuid.uuid4()),
                user_id=user_id,
                session_id=session_id,
                agent_id=agent_id,
                enabled=False
            )
    
    def record_model_call(
        self,
        trace_context: TraceContext,
        model_endpoint: str,
        provider_name: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        model_call_time: int,
        ai_response: Optional[str] = None,
        is_fallback_used: bool = False,
        fallback_reason: Optional[str] = None,
        fallback_from_endpoint: Optional[str] = None,
        fallback_to_endpoint: Optional[str] = None
    ) -> None:
        """记录模型调用"""
        if not trace_context.is_enabled():
            return
        
        try:
            event = ModelCallEvent(
                trace_context=trace_context,
                model_endpoint=model_endpoint,
                provider_name=provider_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                model_call_time=model_call_time,
                ai_response=ai_response,
                is_fallback_used=is_fallback_used,
                fallback_reason=fallback_reason,
                fallback_from_endpoint=fallback_from_endpoint,
                fallback_to_endpoint=fallback_to_endpoint
            )
            import asyncio
            asyncio.run(self.event_publisher.publish(event))
        except Exception:
            # 记录失败不影响主流程
            pass
    
    def record_tool_call(
        self,
        trace_context: TraceContext,
        tool_name: str,
        tool_request_args: str,
        tool_response_data: str,
        tool_execution_time: int,
        tool_success: bool,
        error_message: Optional[str] = None,
        is_fallback_used: bool = False,
        fallback_reason: Optional[str] = None,
        fallback_from_endpoint: Optional[str] = None,
        fallback_to_endpoint: Optional[str] = None
    ) -> None:
        """记录工具调用"""
        if not trace_context.is_enabled():
            return
        
        try:
            event = ToolCallEvent(
                trace_context=trace_context,
                tool_name=tool_name,
                tool_request_args=tool_request_args,
                tool_response_data=tool_response_data,
                tool_execution_time=tool_execution_time,
                tool_success=tool_success,
                error_message=error_message,
                is_fallback_used=is_fallback_used,
                fallback_reason=fallback_reason,
                fallback_from_endpoint=fallback_from_endpoint,
                fallback_to_endpoint=fallback_to_endpoint
            )
            import asyncio
            asyncio.run(self.event_publisher.publish(event))
        except Exception:
            # 记录失败不影响主流程
            pass
    
    def complete_trace(
        self,
        trace_context: TraceContext,
        execution_success: bool = True,
        error_phase: Optional[str] = None,
        error_message: Optional[str] = None,
        total_input_tokens: int = 0,
        total_output_tokens: int = 0,
        total_tokens: int = 0,
        tool_call_count: int = 0,
        total_tool_execution_time: int = 0,
        is_fallback_used: bool = False,
        fallback_reason: Optional[str] = None,
        fallback_from_endpoint: Optional[str] = None,
        fallback_to_endpoint: Optional[str] = None
    ) -> None:
        """完成追踪"""
        if not trace_context.is_enabled():
            return
        
        try:
            # 设置结束时间
            trace_context.set_end_time()
            
            event = ExecutionEndEvent(
                trace_context=trace_context,
                execution_success=execution_success,
                error_phase=error_phase,
                error_message=error_message,
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                total_tokens=total_tokens,
                tool_call_count=tool_call_count,
                total_tool_execution_time=total_tool_execution_time,
                is_fallback_used=is_fallback_used,
                fallback_reason=fallback_reason,
                fallback_from_endpoint=fallback_from_endpoint,
                fallback_to_endpoint=fallback_to_endpoint
            )
            import asyncio
            asyncio.run(self.event_publisher.publish(event))
        except Exception:
            # 记录失败不影响主流程
            pass
    
    def _should_sample(self, trace_id: str, user_id: str) -> bool:
        """判断是否需要采样"""
        # 开发环境全量采集
        import os
        if os.environ.get('ENVIRONMENT', 'development') == 'development':
            return True
        
        # 错误请求强制全量（这里简化处理，实际应该根据请求状态判断）
        # if is_error_request():
        #     return True
        
        # VIP 用户强制全量（这里简化处理，实际应该根据用户等级判断）
        # if is_vip_user(user_id):
        #     return True
        
        # 白名单强制全量（这里简化处理，实际应该检查白名单）
        # if in_whitelist(trace_id):
        #     return True
        
        # 哈希采样
        trace_hash = int(hashlib.md5(trace_id.encode()).hexdigest(), 16)
        return (trace_hash % 100) < (self.sampling_rate * 100)
