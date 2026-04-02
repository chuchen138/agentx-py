from typing import List, Optional, Dict, Any
from datetime import datetime
from app.domain.execution_trace.trace_collector import TraceCollector
from app.domain.execution_trace.trace_context import TraceContext
from app.domain.execution_trace.entities import AgentExecutionSummary, AgentExecutionDetail
from app.infrastructure.execution_trace.repository import ExecutionTraceRepository


class AgentExecutionTraceAppService:
    def __init__(self, trace_collector: TraceCollector, repository: ExecutionTraceRepository):
        self.trace_collector = trace_collector
        self.repository = repository
        
    def start_trace(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
        user_message: Optional[str] = None,
        user_message_id: Optional[str] = None
    ) -> TraceContext:
        """开始执行追踪"""
        return self.trace_collector.start_trace(
            user_id=user_id,
            session_id=session_id,
            agent_id=agent_id,
            user_message=user_message,
            user_message_id=user_message_id
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
        self.trace_collector.record_model_call(
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
        self.trace_collector.record_tool_call(
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
        """完成执行追踪"""
        self.trace_collector.complete_trace(
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
    
    async def get_execution_trace(self, trace_id: str, user_id: str) -> Dict[str, Any]:
        """获取完整的执行链路信息"""
        # 获取汇总信息
        summary = await self.repository.get_summary_by_trace_id(trace_id)
        if not summary:
            return None
        
        # 权限检查：普通用户只能查看自己的执行数据
        if summary.user_id != user_id:
            return None
        
        # 获取详细信息
        details = await self.repository.get_details_by_trace_id(trace_id)
        
        return {
            "summary": summary.dict(),
            "steps": [detail.dict() for detail in details]
        }
    
    async def get_user_execution_history(
        self,
        user_id: str,
        limit: int = 15,
        offset: int = 0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AgentExecutionSummary]:
        """分页查询用户的执行历史"""
        return await self.repository.get_summaries_by_user_id(
            user_id=user_id,
            limit=limit,
            offset=offset,
            start_time=start_time,
            end_time=end_time
        )
    
    async def get_session_execution_history(self, session_id: str, user_id: str) -> List[AgentExecutionSummary]:
        """查询会话的执行历史"""
        summaries = await self.repository.get_summaries_by_session_id(session_id)
        # 权限检查：普通用户只能查看自己的执行数据
        return [summary for summary in summaries if summary.user_id == user_id]
    
    async def get_failed_executions(
        self,
        user_id: str,
        limit: int = 15,
        offset: int = 0
    ) -> List[AgentExecutionSummary]:
        """查询用户的失败执行记录"""
        return await self.repository.get_failed_summaries(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
    
    async def get_execution_statistics(
        self,
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取用户的执行统计信息"""
        # 获取指定时间范围内的执行记录
        summaries = await self.repository.get_summaries_by_user_id(
            user_id=user_id,
            limit=1000,  # 限制查询数量
            start_time=start_time,
            end_time=end_time
        )
        
        if not summaries:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "average_execution_time": 0,
                "total_tokens": 0,
                "average_tokens": 0,
                "total_tool_calls": 0,
                "average_tool_calls": 0
            }
        
        # 计算统计数据
        total_executions = len(summaries)
        successful_executions = sum(1 for s in summaries if s.execution_success)
        failed_executions = total_executions - successful_executions
        
        total_execution_time = sum(s.total_execution_time or 0 for s in summaries)
        average_execution_time = total_execution_time / total_executions if total_executions > 0 else 0
        
        total_tokens = sum(s.total_tokens for s in summaries)
        average_tokens = total_tokens / total_executions if total_executions > 0 else 0
        
        total_tool_calls = sum(s.tool_call_count for s in summaries)
        average_tool_calls = total_tool_calls / total_executions if total_executions > 0 else 0
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "average_execution_time": average_execution_time,
            "total_tokens": total_tokens,
            "average_tokens": average_tokens,
            "total_tool_calls": total_tool_calls,
            "average_tool_calls": average_tool_calls
        }
