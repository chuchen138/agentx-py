from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta

from app.domain.workflow.repository import WorkflowRepository, TaskRepository


class WorkflowCleanupScheduler:
    """工作流清理调度器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WorkflowCleanupScheduler, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._scheduler = BackgroundScheduler()
            self._workflow_repository = None
            self._task_repository = None
            self._initialized = False
    
    def initialize(self, workflow_repository: WorkflowRepository, task_repository: TaskRepository):
        """初始化调度器"""
        self._workflow_repository = workflow_repository
        self._task_repository = task_repository
        self._initialized = True
        self._setup_jobs()
    
    def _setup_jobs(self):
        """设置定时任务"""
        # 每天凌晨2点执行清理
        self._scheduler.add_job(
            self.cleanup_expired_workflows,
            trigger=CronTrigger(hour=2, minute=0),
            id='cleanup_expired_workflows',
            name='清理过期工作流',
            replace_existing=True
        )
        
        # 每天凌晨2:30执行清理无主任务
        self._scheduler.add_job(
            self.cleanup_orphan_tasks,
            trigger=CronTrigger(hour=2, minute=30),
            id='cleanup_orphan_tasks',
            name='清理无主任务',
            replace_existing=True
        )
    
    def start(self):
        """启动调度器"""
        if self._initialized and not self._scheduler.running:
            self._scheduler.start()
    
    def shutdown(self, wait: bool = True):
        """关闭调度器"""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=wait)
    
    def cleanup_expired_workflows(self):
        """清理过期工作流"""
        if not self._initialized:
            return
        
        # 清理30天前的已完成工作流
        cutoff_date = datetime.now() - timedelta(days=30)
        
        # 这里需要实现清理逻辑
        # 暂时只打印日志
        print(f"Cleaning up expired workflows before {cutoff_date}")
    
    def cleanup_orphan_tasks(self):
        """清理无主任务"""
        if not self._initialized:
            return
        
        # 清理没有对应工作流的任务
        # 这里需要实现清理逻辑
        # 暂时只打印日志
        print("Cleaning up orphan tasks")


# 全局调度器实例
workflow_cleanup_scheduler = WorkflowCleanupScheduler()
