from enum import Enum


class WorkflowState(Enum):
    """工作流状态枚举"""
    INIT = "INIT"  # 初始化
    ANALYZING = "ANALYZING"  # 分析中
    SPLITTING = "SPLITTING"  # 拆分中
    EXECUTING = "EXECUTING"  # 执行中
    SUMMARIZING = "SUMMARIZING"  # 摘要中
    COMPLETED = "COMPLETED"  # 完成
    FAILED = "FAILED"  # 失败


# 状态转换规则表
STATE_TRANSITIONS = {
    WorkflowState.INIT: [WorkflowState.ANALYZING],
    WorkflowState.ANALYZING: [WorkflowState.SPLITTING, WorkflowState.COMPLETED],
    WorkflowState.SPLITTING: [WorkflowState.EXECUTING, WorkflowState.FAILED],
    WorkflowState.EXECUTING: [
        WorkflowState.EXECUTING,  # 继续执行更多任务
        WorkflowState.SUMMARIZING,
        WorkflowState.COMPLETED
    ],
    WorkflowState.SUMMARIZING: [WorkflowState.COMPLETED, WorkflowState.FAILED],
}


def can_transition(from_state: WorkflowState, to_state: WorkflowState) -> bool:
    """验证状态转换是否合法"""
    return to_state in STATE_TRANSITIONS.get(from_state, [])
