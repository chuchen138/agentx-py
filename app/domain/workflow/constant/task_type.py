from enum import Enum


class TaskType(Enum):
    """任务类型枚举"""
    DATA_ANALYSIS = "DATA_ANALYSIS"  # 数据分析
    MULTI_QUERY = "MULTI_QUERY"  # 多查询
    INFORMATION_RETRIEVAL = "INFORMATION_RETRIEVAL"  # 信息查询
    REPORT_GENERATION = "REPORT_GENERATION"  # 报告生成
    TOOL_EXECUTION = "TOOL_EXECUTION"  # 工具执行
    CUSTOM = "CUSTOM"  # 自定义


# 任务类型与处理器的映射
TASK_TYPE_HANDLER_MAPPING = {
    TaskType.DATA_ANALYSIS: "DataAnalysisTaskExecutor",
    TaskType.MULTI_QUERY: "MultiQueryTaskExecutor",
    TaskType.INFORMATION_RETRIEVAL: "InformationRetrievalTaskExecutor",
    TaskType.REPORT_GENERATION: "ReportGenerationTaskExecutor",
    TaskType.TOOL_EXECUTION: "ToolExecutionTaskExecutor",
    TaskType.CUSTOM: "CustomTaskExecutor",
}
