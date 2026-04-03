from enum import Enum


class RepeatType(str, Enum):
    """重复类型枚举"""
    IMMEDIATE = "immediate"      # 立即执行
    INTERVAL = "interval"        # 间隔重复
    DAILY = "daily"              # 每日重复
    WEEKLY = "weekly"            # 每周重复
    CUSTOM = "custom"            # 自定义 Cron
