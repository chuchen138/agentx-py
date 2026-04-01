from typing import List, Dict, Any, Optional
import uuid

from app.domain.workflow.constant.task_type import TaskType
from app.domain.workflow.task_manager import TaskManager


class AnalysisResult:
    """分析结果"""
    def __init__(self, is_complex: bool, intent: str, complexity_score: float):
        self.is_complex = is_complex
        self.intent = intent
        self.complexity_score = complexity_score


class TaskDefinition:
    """任务定义"""
    def __init__(self, task_name: str, task_type: TaskType, description: str, priority: int = 0, depends_on: List[str] = None):
        self.task_name = task_name
        self.task_type = task_type
        self.description = description
        self.priority = priority
        self.depends_on = depends_on or []


class SplitResult:
    """拆分结果"""
    def __init__(self, tasks: List[TaskDefinition], is_complex: bool):
        self.tasks = tasks
        self.is_complex = is_complex


class TaskSplitHandler:
    """任务拆分处理器"""
    
    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
    
    def analyze_request(self, user_message: str, context: Dict[str, Any]) -> AnalysisResult:
        """分析用户请求"""
        # 这里应该使用LLM分析用户意图
        # 暂时模拟分析结果
        is_complex = len(user_message) > 50 or "分析" in user_message or "查询" in user_message
        intent = "数据分析" if "分析" in user_message else "信息查询" if "查询" in user_message else "其他"
        complexity_score = min(len(user_message) / 100, 1.0)
        
        return AnalysisResult(
            is_complex=is_complex,
            intent=intent,
            complexity_score=complexity_score
        )
    
    def identify_complexity(self, analysis_result: AnalysisResult) -> bool:
        """识别任务复杂度"""
        return analysis_result.is_complex or analysis_result.complexity_score > 0.5
    
    def split_into_tasks(self, analysis_result: AnalysisResult) -> List[TaskDefinition]:
        """拆分为子任务"""
        tasks = []
        
        if analysis_result.intent == "数据分析":
            # 数据分析任务拆分
            tasks.append(TaskDefinition(
                task_name="获取数据",
                task_type=TaskType.INFORMATION_RETRIEVAL,
                description="从数据源获取需要分析的数据",
                priority=1
            ))
            tasks.append(TaskDefinition(
                task_name="分析数据",
                task_type=TaskType.DATA_ANALYSIS,
                description="对获取的数据进行分析处理",
                priority=2,
                depends_on=[tasks[0].task_name]  # 依赖第一个任务
            ))
            tasks.append(TaskDefinition(
                task_name="生成报告",
                task_type=TaskType.REPORT_GENERATION,
                description="基于分析结果生成报告",
                priority=3,
                depends_on=[tasks[1].task_name]  # 依赖第二个任务
            ))
        elif analysis_result.intent == "信息查询":
            # 信息查询任务拆分
            tasks.append(TaskDefinition(
                task_name="查询信息",
                task_type=TaskType.MULTI_QUERY,
                description="从多个来源查询相关信息",
                priority=1
            ))
            tasks.append(TaskDefinition(
                task_name="汇总结果",
                task_type=TaskType.REPORT_GENERATION,
                description="汇总查询结果并生成回答",
                priority=2,
                depends_on=[tasks[0].task_name]  # 依赖第一个任务
            ))
        else:
            # 其他任务
            tasks.append(TaskDefinition(
                task_name="执行任务",
                task_type=TaskType.CUSTOM,
                description="执行用户请求的任务",
                priority=1
            ))
        
        return tasks
    
    def set_task_dependencies(self, tasks: List[TaskDefinition]) -> List[Dict[str, Any]]:
        """设置任务依赖关系"""
        task_mapping = {task.task_name: str(uuid.uuid4()) for task in tasks}
        task_definitions = []
        
        for task in tasks:
            depends_on = [task_mapping[dep] for dep in task.depends_on if dep in task_mapping]
            task_definitions.append({
                "task_name": task.task_name,
                "task_type": task.task_type.value,
                "description": task.description,
                "priority": task.priority,
                "depends_on": depends_on
            })
        
        return task_definitions
    
    def handle(self, user_message: str, context: Dict[str, Any], workflow_id: str) -> SplitResult:
        """处理任务拆分"""
        # 分析请求
        analysis_result = self.analyze_request(user_message, context)
        
        # 识别复杂度
        is_complex = self.identify_complexity(analysis_result)
        
        if not is_complex:
            # 简单任务，不需要拆分
            return SplitResult(tasks=[], is_complex=False)
        
        # 拆分为子任务
        tasks = self.split_into_tasks(analysis_result)
        
        # 设置任务依赖
        task_definitions = self.set_task_dependencies(tasks)
        
        # 创建任务
        created_tasks = []
        for task_def in task_definitions:
            created_task = self.task_manager.create_task(workflow_id, task_def)
            created_tasks.append(created_task)
        
        return SplitResult(tasks=tasks, is_complex=True)
