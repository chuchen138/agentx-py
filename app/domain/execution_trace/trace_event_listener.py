import asyncio
import json
import gzip
import base64
import uuid
from datetime import datetime
from typing import List, Optional
from .event_publisher import EventPublisher
from .events import ExecutionStartEvent, ExecutionEndEvent, ModelCallEvent, ToolCallEvent
from .entities import AgentExecutionSummary, AgentExecutionDetail
from .data_masker import DataMasker


class TraceEventListener:
    def __init__(self, event_publisher: EventPublisher, repository: any):
        self.event_publisher = event_publisher
        self.repository = repository
        self.batch_size = 100
        self.batch_timeout = 5  # 秒
        self.running = False
        self.batch_events = []
        self.last_process_time = datetime.utcnow()
        
    async def start(self):
        """启动事件监听器"""
        self.running = True
        await self._process_events()
        
    async def stop(self):
        """停止事件监听器"""
        self.running = False
        
    async def _process_events(self):
        """处理事件队列中的事件"""
        while self.running:
            try:
                # 尝试获取事件，设置超时以定期检查批处理
                try:
                    event = await asyncio.wait_for(self.event_publisher.get(), timeout=1)
                    if event:
                        self.batch_events.append(event)
                except asyncio.TimeoutError:
                    pass
                
                # 检查是否需要批处理
                current_time = datetime.utcnow()
                time_elapsed = (current_time - self.last_process_time).total_seconds()
                
                if len(self.batch_events) >= self.batch_size or time_elapsed >= self.batch_timeout:
                    if self.batch_events:
                        await self._process_batch(self.batch_events)
                        self.batch_events = []
                        self.last_process_time = current_time
            except Exception:
                # 处理异常，避免监听器崩溃
                await asyncio.sleep(1)
        
    async def _process_batch(self, events: List[any]):
        """批量处理事件"""
        try:
            summaries = {}
            details = []
            
            for event in events:
                if isinstance(event, ExecutionStartEvent):
                    # 处理执行开始事件
                    summary = self._create_summary_from_start_event(event)
                    summaries[summary.trace_id] = summary
                elif isinstance(event, ExecutionEndEvent):
                    # 处理执行结束事件
                    summary = self._update_summary_from_end_event(event, summaries.get(event.trace_context.trace_id))
                    if summary:
                        summaries[summary.trace_id] = summary
                elif isinstance(event, ModelCallEvent):
                    # 处理模型调用事件
                    detail = self._create_detail_from_model_event(event)
                    details.append(detail)
                elif isinstance(event, ToolCallEvent):
                    # 处理工具调用事件
                    detail = self._create_detail_from_tool_event(event)
                    details.append(detail)
            
            # 批量保存数据
            if summaries:
                await self.repository.save_summaries(list(summaries.values()))
            if details:
                await self.repository.save_details(details)
        except Exception:
            # 批量处理失败，尝试单条处理
            for event in events:
                try:
                    await self._process_single_event(event)
                except Exception:
                    pass
        
    async def _process_single_event(self, event: any):
        """单条处理事件"""
        try:
            if isinstance(event, ExecutionStartEvent):
                summary = self._create_summary_from_start_event(event)
                await self.repository.save_summary(summary)
            elif isinstance(event, ExecutionEndEvent):
                summary = self._update_summary_from_end_event(event, None)
                if summary:
                    await self.repository.save_summary(summary)
            elif isinstance(event, ModelCallEvent):
                detail = self._create_detail_from_model_event(event)
                await self.repository.save_detail(detail)
            elif isinstance(event, ToolCallEvent):
                detail = self._create_detail_from_tool_event(event)
                await self.repository.save_detail(detail)
        except Exception:
            pass
        
    def _create_summary_from_start_event(self, event: ExecutionStartEvent) -> AgentExecutionSummary:
        """从执行开始事件创建汇总记录"""
        return AgentExecutionSummary(
            trace_id=event.trace_context.trace_id,
            user_id=event.trace_context.user_id,
            session_id=event.trace_context.session_id,
            agent_id=event.trace_context.agent_id,
            execution_start_time=event.trace_context.start_time,
            metadata={
                'sampling_rate': 1.0 if event.trace_context.is_enabled() else 0.0,
                'is_sampled': event.trace_context.is_enabled()
            }
        )
    
    def _update_summary_from_end_event(self, event: ExecutionEndEvent, existing_summary: Optional[AgentExecutionSummary]) -> AgentExecutionSummary:
        """从执行结束事件更新汇总记录"""
        if existing_summary:
            summary = existing_summary
        else:
            summary = AgentExecutionSummary(
                trace_id=event.trace_context.trace_id,
                user_id=event.trace_context.user_id,
                session_id=event.trace_context.session_id,
                agent_id=event.trace_context.agent_id,
                execution_start_time=event.trace_context.start_time
            )
        
        summary.execution_end_time = event.trace_context.end_time
        summary.total_execution_time = event.trace_context.get_duration()
        summary.total_input_tokens = event.total_input_tokens
        summary.total_output_tokens = event.total_output_tokens
        summary.total_tokens = event.total_tokens
        summary.tool_call_count = event.tool_call_count
        summary.total_tool_execution_time = event.total_tool_execution_time
        summary.execution_success = event.execution_success
        summary.error_phase = event.error_phase
        summary.error_message = event.error_message
        summary.is_fallback_used = event.is_fallback_used
        summary.fallback_reason = event.fallback_reason
        summary.fallback_from_endpoint = event.fallback_from_endpoint
        summary.fallback_to_endpoint = event.fallback_to_endpoint
        
        return summary
    
    def _create_detail_from_model_event(self, event: ModelCallEvent) -> AgentExecutionDetail:
        """从模型调用事件创建详细记录"""
        # 脱敏处理
        masked_response = DataMasker.mask(event.ai_response) if event.ai_response else None
        
        # 压缩长文本
        if masked_response and len(masked_response) > 1000:
            compressed = gzip.compress(masked_response.encode())
            masked_response = f"<compressed>{base64.b64encode(compressed).decode()}</compressed>"
        
        return AgentExecutionDetail(
            trace_id=event.trace_context.trace_id,
            step_id=f"step_{str(uuid.uuid4())[:8]}",
            timestamp=event.timestamp,
            message_type="MODEL_CALL",
            message_content=masked_response,
            model_endpoint=event.model_endpoint,
            provider_name=event.provider_name,
            input_tokens=event.input_tokens,
            output_tokens=event.output_tokens,
            total_tokens=event.total_tokens,
            model_call_time=event.model_call_time,
            is_fallback_used=event.is_fallback_used,
            fallback_reason=event.fallback_reason,
            fallback_from_endpoint=event.fallback_from_endpoint,
            fallback_to_endpoint=event.fallback_to_endpoint,
            user_id=event.trace_context.user_id
        )
    
    def _create_detail_from_tool_event(self, event: ToolCallEvent) -> AgentExecutionDetail:
        """从工具调用事件创建详细记录"""
        # 脱敏处理
        masked_args = DataMasker.mask(event.tool_request_args)
        masked_response = DataMasker.mask(event.tool_response_data)
        
        # 压缩长文本
        if len(masked_args) > 1000:
            compressed = gzip.compress(masked_args.encode())
            masked_args = f"<compressed>{base64.b64encode(compressed).decode()}</compressed>"
        
        if len(masked_response) > 1000:
            compressed = gzip.compress(masked_response.encode())
            masked_response = f"<compressed>{base64.b64encode(compressed).decode()}</compressed>"
        
        return AgentExecutionDetail(
            trace_id=event.trace_context.trace_id,
            step_id=f"step_{str(uuid.uuid4())[:8]}",
            timestamp=event.timestamp,
            message_type="TOOL_CALL",
            tool_name=event.tool_name,
            tool_request_args=masked_args,
            tool_response_data=masked_response,
            tool_execution_time=event.tool_execution_time,
            tool_success=event.tool_success,
            is_fallback_used=event.is_fallback_used,
            fallback_reason=event.fallback_reason,
            fallback_from_endpoint=event.fallback_from_endpoint,
            fallback_to_endpoint=event.fallback_to_endpoint,
            user_id=event.trace_context.user_id
        )
