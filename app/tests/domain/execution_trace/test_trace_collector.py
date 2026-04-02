import asyncio
import pytest
from app.domain.execution_trace.trace_collector import TraceCollector
from app.domain.execution_trace.event_publisher import EventPublisher
from app.domain.execution_trace.trace_context import TraceContext


class TestTraceCollector:
    @pytest.fixture
    def event_publisher(self):
        return EventPublisher()
    
    @pytest.fixture
    def trace_collector(self, event_publisher):
        return TraceCollector(event_publisher)
    
    def test_start_trace(self, trace_collector):
        """测试开始追踪"""
        trace_context = trace_collector.start_trace(
            user_id="user_123",
            session_id="session_456",
            agent_id="agent_789",
            user_message="Test message"
        )
        
        assert trace_context is not None
        assert trace_context.is_enabled()
        assert trace_context.user_id == "user_123"
        assert trace_context.session_id == "session_456"
        assert trace_context.agent_id == "agent_789"
    
    def test_record_model_call(self, trace_collector):
        """测试记录模型调用"""
        trace_context = trace_collector.start_trace(
            user_id="user_123",
            session_id="session_456",
            agent_id="agent_789"
        )
        
        # 记录模型调用
        trace_collector.record_model_call(
            trace_context=trace_context,
            model_endpoint="gpt-4-turbo",
            provider_name="openai",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            model_call_time=1000,
            ai_response="Test response"
        )
        
        # 验证事件队列中有模型调用事件
        assert trace_collector.event_publisher.qsize() > 0
    
    def test_record_tool_call(self, trace_collector):
        """测试记录工具调用"""
        trace_context = trace_collector.start_trace(
            user_id="user_123",
            session_id="session_456",
            agent_id="agent_789"
        )
        
        # 记录工具调用
        trace_collector.record_tool_call(
            trace_context=trace_context,
            tool_name="weather_query",
            tool_request_args="{\"city\": \"Beijing\"}",
            tool_response_data="{\"temperature\": 25}",
            tool_execution_time=500,
            tool_success=True
        )
        
        # 验证事件队列中有工具调用事件
        assert trace_collector.event_publisher.qsize() > 0
    
    def test_complete_trace(self, trace_collector):
        """测试完成追踪"""
        trace_context = trace_collector.start_trace(
            user_id="user_123",
            session_id="session_456",
            agent_id="agent_789"
        )
        
        # 完成追踪
        trace_collector.complete_trace(
            trace_context=trace_context,
            execution_success=True,
            total_input_tokens=100,
            total_output_tokens=50,
            total_tokens=150,
            tool_call_count=1,
            total_tool_execution_time=500
        )
        
        # 验证事件队列中有执行结束事件
        assert trace_collector.event_publisher.qsize() > 0
    
    def test_disabled_trace(self, trace_collector):
        """测试禁用的追踪"""
        # 禁用追踪器
        trace_collector.enabled = False
        
        trace_context = trace_collector.start_trace(
            user_id="user_123",
            session_id="session_456",
            agent_id="agent_789"
        )
        
        assert not trace_context.is_enabled()
