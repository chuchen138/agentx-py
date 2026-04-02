from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, and_
from ..execution_trace.models import AgentExecutionSummaryModel, AgentExecutionDetailModel
from app.domain.execution_trace.entities import AgentExecutionSummary, AgentExecutionDetail


class ExecutionTraceRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        
    async def save_summary(self, summary: AgentExecutionSummary) -> None:
        """保存执行汇总记录"""
        model = self._convert_summary_to_model(summary)
        async with self.db_session as session:
            try:
                # 检查是否已存在
                existing = await session.execute(
                    select(AgentExecutionSummaryModel).where(
                        AgentExecutionSummaryModel.trace_id == summary.trace_id
                    )
                )
                existing_model = existing.scalar_one_or_none()
                
                if existing_model:
                    # 更新现有记录
                    for key, value in model.__dict__.items():
                        if key != '_sa_instance_state':
                            setattr(existing_model, key, value)
                else:
                    # 创建新记录
                    session.add(model)
                
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def save_summaries(self, summaries: List[AgentExecutionSummary]) -> None:
        """批量保存执行汇总记录"""
        models = [self._convert_summary_to_model(summary) for summary in summaries]
        async with self.db_session as session:
            try:
                # 批量插入或更新
                for model in models:
                    existing = await session.execute(
                        select(AgentExecutionSummaryModel).where(
                            AgentExecutionSummaryModel.trace_id == model.trace_id
                        )
                    )
                    existing_model = existing.scalar_one_or_none()
                    
                    if existing_model:
                        for key, value in model.__dict__.items():
                            if key != '_sa_instance_state':
                                setattr(existing_model, key, value)
                    else:
                        session.add(model)
                
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def save_detail(self, detail: AgentExecutionDetail) -> None:
        """保存执行详细记录"""
        model = self._convert_detail_to_model(detail)
        async with self.db_session as session:
            try:
                session.add(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def save_details(self, details: List[AgentExecutionDetail]) -> None:
        """批量保存执行详细记录"""
        models = [self._convert_detail_to_model(detail) for detail in details]
        async with self.db_session as session:
            try:
                session.add_all(models)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def get_summary_by_trace_id(self, trace_id: str) -> Optional[AgentExecutionSummary]:
        """根据追踪 ID 获取执行汇总记录"""
        async with self.db_session as session:
            result = await session.execute(
                select(AgentExecutionSummaryModel).where(
                    AgentExecutionSummaryModel.trace_id == trace_id
                )
            )
            model = result.scalar_one_or_none()
            if model:
                return self._convert_model_to_summary(model)
            return None
    
    async def get_details_by_trace_id(self, trace_id: str) -> List[AgentExecutionDetail]:
        """根据追踪 ID 获取执行详细记录"""
        async with self.db_session as session:
            result = await session.execute(
                select(AgentExecutionDetailModel).where(
                    AgentExecutionDetailModel.trace_id == trace_id
                ).order_by(AgentExecutionDetailModel.timestamp)
            )
            models = result.scalars().all()
            return [self._convert_model_to_detail(model) for model in models]
    
    async def get_summaries_by_user_id(
        self,
        user_id: str,
        limit: int = 15,
        offset: int = 0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AgentExecutionSummary]:
        """根据用户 ID 获取执行汇总记录（分页）"""
        async with self.db_session as session:
            query = select(AgentExecutionSummaryModel).where(
                AgentExecutionSummaryModel.user_id == user_id
            )
            
            if start_time:
                query = query.where(AgentExecutionSummaryModel.execution_start_time >= start_time)
            if end_time:
                query = query.where(AgentExecutionSummaryModel.execution_start_time <= end_time)
            
            query = query.order_by(desc(AgentExecutionSummaryModel.execution_start_time))
            query = query.limit(limit).offset(offset)
            
            result = await session.execute(query)
            models = result.scalars().all()
            return [self._convert_model_to_summary(model) for model in models]
    
    async def get_summaries_by_session_id(self, session_id: str) -> List[AgentExecutionSummary]:
        """根据会话 ID 获取执行汇总记录"""
        async with self.db_session as session:
            result = await session.execute(
                select(AgentExecutionSummaryModel).where(
                    AgentExecutionSummaryModel.session_id == session_id
                ).order_by(desc(AgentExecutionSummaryModel.execution_start_time))
            )
            models = result.scalars().all()
            return [self._convert_model_to_summary(model) for model in models]
    
    async def get_failed_summaries(
        self,
        user_id: Optional[str] = None,
        limit: int = 15,
        offset: int = 0
    ) -> List[AgentExecutionSummary]:
        """获取失败的执行汇总记录"""
        async with self.db_session as session:
            query = select(AgentExecutionSummaryModel).where(
                AgentExecutionSummaryModel.execution_success == False
            )
            
            if user_id:
                query = query.where(AgentExecutionSummaryModel.user_id == user_id)
            
            query = query.order_by(desc(AgentExecutionSummaryModel.execution_start_time))
            query = query.limit(limit).offset(offset)
            
            result = await session.execute(query)
            models = result.scalars().all()
            return [self._convert_model_to_summary(model) for model in models]
    
    def _convert_summary_to_model(self, summary: AgentExecutionSummary) -> AgentExecutionSummaryModel:
        """将领域实体转换为数据库模型"""
        return AgentExecutionSummaryModel(
            trace_id=summary.trace_id,
            user_id=summary.user_id,
            session_id=summary.session_id,
            agent_id=summary.agent_id,
            execution_start_time=summary.execution_start_time,
            execution_end_time=summary.execution_end_time,
            total_execution_time=summary.total_execution_time,
            total_input_tokens=summary.total_input_tokens,
            total_output_tokens=summary.total_output_tokens,
            total_tokens=summary.total_tokens,
            tool_call_count=summary.tool_call_count,
            total_tool_execution_time=summary.total_tool_execution_time,
            execution_success=summary.execution_success,
            error_phase=summary.error_phase,
            error_message=summary.error_message,
            is_fallback_used=summary.is_fallback_used,
            fallback_reason=summary.fallback_reason,
            fallback_from_endpoint=summary.fallback_from_endpoint,
            fallback_to_endpoint=summary.fallback_to_endpoint,
            metadata_=summary.metadata
        )
    
    def _convert_model_to_summary(self, model: AgentExecutionSummaryModel) -> AgentExecutionSummary:
        """将数据库模型转换为领域实体"""
        return AgentExecutionSummary(
            trace_id=model.trace_id,
            user_id=model.user_id,
            session_id=model.session_id,
            agent_id=model.agent_id,
            execution_start_time=model.execution_start_time,
            execution_end_time=model.execution_end_time,
            total_execution_time=model.total_execution_time,
            total_input_tokens=model.total_input_tokens,
            total_output_tokens=model.total_output_tokens,
            total_tokens=model.total_tokens,
            tool_call_count=model.tool_call_count,
            total_tool_execution_time=model.total_tool_execution_time,
            execution_success=model.execution_success,
            error_phase=model.error_phase,
            error_message=model.error_message,
            is_fallback_used=model.is_fallback_used,
            fallback_reason=model.fallback_reason,
            fallback_from_endpoint=model.fallback_from_endpoint,
            fallback_to_endpoint=model.fallback_to_endpoint,
            metadata=model.metadata_ or {}
        )
    
    def _convert_detail_to_model(self, detail: AgentExecutionDetail) -> AgentExecutionDetailModel:
        """将领域实体转换为数据库模型"""
        return AgentExecutionDetailModel(
            trace_id=detail.trace_id,
            step_id=detail.step_id,
            timestamp=detail.timestamp,
            message_type=detail.message_type,
            message_content=detail.message_content,
            message_tokens=detail.message_tokens,
            model_endpoint=detail.model_endpoint,
            provider_name=detail.provider_name,
            input_tokens=detail.input_tokens,
            output_tokens=detail.output_tokens,
            total_tokens=detail.total_tokens,
            model_call_time=detail.model_call_time,
            tool_name=detail.tool_name,
            tool_request_args=detail.tool_request_args,
            tool_response_data=detail.tool_response_data,
            tool_execution_time=detail.tool_execution_time,
            tool_success=detail.tool_success,
            is_fallback_used=detail.is_fallback_used,
            fallback_reason=detail.fallback_reason,
            fallback_from_endpoint=detail.fallback_from_endpoint,
            fallback_to_endpoint=detail.fallback_to_endpoint,
            user_id=detail.user_id,
            metadata_=detail.metadata
        )
    
    def _convert_model_to_detail(self, model: AgentExecutionDetailModel) -> AgentExecutionDetail:
        """将数据库模型转换为领域实体"""
        return AgentExecutionDetail(
            trace_id=model.trace_id,
            step_id=model.step_id,
            timestamp=model.timestamp,
            message_type=model.message_type,
            message_content=model.message_content,
            message_tokens=model.message_tokens,
            model_endpoint=model.model_endpoint,
            provider_name=model.provider_name,
            input_tokens=model.input_tokens,
            output_tokens=model.output_tokens,
            total_tokens=model.total_tokens,
            model_call_time=model.model_call_time,
            tool_name=model.tool_name,
            tool_request_args=model.tool_request_args,
            tool_response_data=model.tool_response_data,
            tool_execution_time=model.tool_execution_time,
            tool_success=model.tool_success,
            is_fallback_used=model.is_fallback_used,
            fallback_reason=model.fallback_reason,
            fallback_from_endpoint=model.fallback_from_endpoint,
            fallback_to_endpoint=model.fallback_to_endpoint,
            user_id=model.user_id,
            metadata=model.metadata_ or {}
        )
