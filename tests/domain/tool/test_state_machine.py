import pytest
from unittest.mock import Mock, MagicMock
from app.domain.tool.state_machine.state_machine import ToolStateMachine, StateProcessor
from app.domain.tool.model import ToolEntity
from app.domain.tool.enums import ToolStatus


class TestToolStateMachine:
    @pytest.fixture
    def state_machine(self):
        return ToolStateMachine()

    @pytest.fixture
    def mock_tool(self):
        tool = Mock(spec=ToolEntity)
        tool.status = ToolStatus.WAITING_REVIEW.value
        return tool

    def test_can_transition_valid(self, state_machine):
        # 测试有效的状态转换
        assert state_machine.can_transition(ToolStatus.WAITING_REVIEW.value, ToolStatus.FETCHING_TOOLS.value) is True
        assert state_machine.can_transition(ToolStatus.FETCHING_TOOLS.value, ToolStatus.GITHUB_URL_VALIDATION.value) is True
        assert state_machine.can_transition(ToolStatus.GITHUB_URL_VALIDATION.value, ToolStatus.DEPLOYING.value) is True
        assert state_machine.can_transition(ToolStatus.DEPLOYING.value, ToolStatus.PUBLISHING.value) is True
        assert state_machine.can_transition(ToolStatus.PUBLISHING.value, ToolStatus.PUBLISHED.value) is True

    def test_can_transition_invalid(self, state_machine):
        # 测试无效的状态转换
        assert state_machine.can_transition(ToolStatus.WAITING_REVIEW.value, ToolStatus.PUBLISHED.value) is False
        assert state_machine.can_transition(ToolStatus.PUBLISHED.value, ToolStatus.DEPLOYING.value) is False
        assert state_machine.can_transition(ToolStatus.REJECTED.value, ToolStatus.WAITING_REVIEW.value) is False

    async def test_transition_to_valid(self, state_machine, mock_tool):
        # 测试有效的状态转换
        result = await state_machine.transition_to(mock_tool, ToolStatus.FETCHING_TOOLS.value)
        assert result is True
        assert mock_tool.status == ToolStatus.FETCHING_TOOLS.value

    async def test_transition_to_invalid(self, state_machine, mock_tool):
        # 测试无效的状态转换
        result = await state_machine.transition_to(mock_tool, ToolStatus.PUBLISHED.value)
        assert result is False
        assert mock_tool.status == ToolStatus.WAITING_REVIEW.value  # 状态不应改变

    async def test_process_without_processor(self, state_machine, mock_tool):
        # 测试没有注册处理器的情况
        result = await state_machine.process(mock_tool)
        assert result is False

    async def test_process_with_processor(self, state_machine, mock_tool):
        # 创建一个测试处理器
        class TestProcessor(StateProcessor):
            async def process(self, tool):
                return ToolStatus.FETCHING_TOOLS

        # 注册处理器
        state_machine.register_processor(ToolStatus.WAITING_REVIEW.value, TestProcessor())

        # 测试处理过程
        result = await state_machine.process(mock_tool)
        assert result is True
        assert mock_tool.status == ToolStatus.FETCHING_TOOLS.value

    async def test_process_with_exception(self, state_machine, mock_tool):
        # 创建一个会抛出异常的处理器
        class TestProcessor(StateProcessor):
            async def process(self, tool):
                raise Exception("Test error")

        # 注册处理器
        state_machine.register_processor(ToolStatus.WAITING_REVIEW.value, TestProcessor())

        # 测试处理过程
        result = await state_machine.process(mock_tool)
        assert result is False
        assert mock_tool.status == ToolStatus.REJECTED.value
        assert mock_tool.reject_reason == "Test error"
        assert mock_tool.failed_step_status == ToolStatus.REJECTED.value
