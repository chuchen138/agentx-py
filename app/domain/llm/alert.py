from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel
from abc import ABC, abstractmethod
import asyncio
import time
from datetime import datetime


class AlertLevel(Enum):
    """告警级别"""
    P0 = "P0"  # 严重
    P1 = "P1"  # 高
    P2 = "P2"  # 中
    P3 = "P3"  # 低


class AlertChannel(Enum):
    """告警渠道"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    DINGTALK = "dingtalk"
    WECHAT = "wechat"
    WEBHOOK = "webhook"


class Alert(BaseModel):
    """告警"""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: str
    source: str
    details: Optional[Dict] = None


class AlertConfig(BaseModel):
    """告警配置"""
    enabled: bool = True
    channels: List[AlertChannel] = [AlertChannel.EMAIL]
    convergence_window_minutes: int = 5
    max_alerts_per_hour: int = 10


class AlertChannelProvider(ABC):
    """告警渠道提供者抽象基类"""
    
    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """发送告警
        
        Args:
            alert: 告警
        
        Returns:
            bool: 是否发送成功
        """
        pass


class EmailAlertProvider(AlertChannelProvider):
    """邮件告警提供者"""
    
    async def send_alert(self, alert: Alert) -> bool:
        """发送邮件告警
        
        Args:
            alert: 告警
        
        Returns:
            bool: 是否发送成功
        """
        # 模拟发送邮件
        print(f"Sending email alert: {alert.title}")
        await asyncio.sleep(0.1)
        return True


class SMSAlertProvider(AlertChannelProvider):
    """短信告警提供者"""
    
    async def send_alert(self, alert: Alert) -> bool:
        """发送短信告警
        
        Args:
            alert: 告警
        
        Returns:
            bool: 是否发送成功
        """
        # 模拟发送短信
        print(f"Sending SMS alert: {alert.title}")
        await asyncio.sleep(0.1)
        return True


class SlackAlertProvider(AlertChannelProvider):
    """Slack告警提供者"""
    
    async def send_alert(self, alert: Alert) -> bool:
        """发送Slack告警
        
        Args:
            alert: 告警
        
        Returns:
            bool: 是否发送成功
        """
        # 模拟发送Slack消息
        print(f"Sending Slack alert: {alert.title}")
        await asyncio.sleep(0.1)
        return True


class DingTalkAlertProvider(AlertChannelProvider):
    """钉钉告警提供者"""
    
    async def send_alert(self, alert: Alert) -> bool:
        """发送钉钉告警
        
        Args:
            alert: 告警
        
        Returns:
            bool: 是否发送成功
        """
        # 模拟发送钉钉消息
        print(f"Sending DingTalk alert: {alert.title}")
        await asyncio.sleep(0.1)
        return True


class WeChatAlertProvider(AlertChannelProvider):
    """企业微信告警提供者"""
    
    async def send_alert(self, alert: Alert) -> bool:
        """发送企业微信告警
        
        Args:
            alert: 告警
        
        Returns:
            bool: 是否发送成功
        """
        # 模拟发送企业微信消息
        print(f"Sending WeChat alert: {alert.title}")
        await asyncio.sleep(0.1)
        return True


class WebhookAlertProvider(AlertChannelProvider):
    """Webhook告警提供者"""
    
    async def send_alert(self, alert: Alert) -> bool:
        """发送Webhook告警
        
        Args:
            alert: 告警
        
        Returns:
            bool: 是否发送成功
        """
        # 模拟发送Webhook
        print(f"Sending Webhook alert: {alert.title}")
        await asyncio.sleep(0.1)
        return True


class AlertService:
    """告警服务"""
    
    def __init__(self, config: AlertConfig = AlertConfig()):
        """初始化告警服务
        
        Args:
            config: 告警配置
        """
        self.config = config
        self.alert_providers: Dict[AlertChannel, AlertChannelProvider] = {
            AlertChannel.EMAIL: EmailAlertProvider(),
            AlertChannel.SMS: SMSAlertProvider(),
            AlertChannel.SLACK: SlackAlertProvider(),
            AlertChannel.DINGTALK: DingTalkAlertProvider(),
            AlertChannel.WECHAT: WeChatAlertProvider(),
            AlertChannel.WEBHOOK: WebhookAlertProvider()
        }
        self.alert_history: List[Alert] = []
        self.alert_count_last_hour = 0
        self.last_hour_start = time.time()
    
    async def send_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        source: str,
        details: Optional[Dict] = None
    ) -> bool:
        """发送告警
        
        Args:
            level: 告警级别
            title: 告警标题
            message: 告警消息
            source: 告警来源
            details: 告警详情
        
        Returns:
            bool: 是否发送成功
        """
        # 检查是否启用告警
        if not self.config.enabled:
            return False
        
        # 检查告警频率限制
        if not self._check_rate_limit():
            print("Alert rate limit exceeded")
            return False
        
        # 检查是否需要收敛
        if self._should_converge(level, title, message):
            print("Alert converged")
            return False
        
        # 创建告警
        alert = Alert(
            id=f"alert-{int(time.time())}-{hash(title) % 1000}",
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now().isoformat(),
            source=source,
            details=details
        )
        
        # 发送告警到配置的渠道
        tasks = []
        for channel in self.config.channels:
            if channel in self.alert_providers:
                tasks.append(self.alert_providers[channel].send_alert(alert))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success = all(isinstance(result, bool) and result for result in results)
        
        # 记录告警历史
        self.alert_history.append(alert)
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        return success
    
    def _check_rate_limit(self) -> bool:
        """检查告警频率限制
        
        Returns:
            bool: 是否允许发送告警
        """
        current_time = time.time()
        if current_time - self.last_hour_start > 3600:
            # 新的一小时，重置计数
            self.last_hour_start = current_time
            self.alert_count_last_hour = 0
        
        if self.alert_count_last_hour >= self.config.max_alerts_per_hour:
            return False
        
        self.alert_count_last_hour += 1
        return True
    
    def _should_converge(self, level: AlertLevel, title: str, message: str) -> bool:
        """检查是否需要收敛告警
        
        Args:
            level: 告警级别
            title: 告警标题
            message: 告警消息
        
        Returns:
            bool: 是否需要收敛
        """
        window_start = time.time() - (self.config.convergence_window_minutes * 60)
        
        # 查找最近窗口内的相似告警
        for alert in reversed(self.alert_history):
            alert_time = datetime.fromisoformat(alert.timestamp).timestamp()
            if alert_time < window_start:
                break
            
            if (alert.level == level and 
                alert.title == title and 
                alert.message == message):
                return True
        
        return False
    
    async def send_p0_alert(self, title: str, message: str, source: str, details: Optional[Dict] = None):
        """发送P0级告警
        
        Args:
            title: 告警标题
            message: 告警消息
            source: 告警来源
            details: 告警详情
        """
        await self.send_alert(AlertLevel.P0, title, message, source, details)
    
    async def send_p1_alert(self, title: str, message: str, source: str, details: Optional[Dict] = None):
        """发送P1级告警
        
        Args:
            title: 告警标题
            message: 告警消息
            source: 告警来源
            details: 告警详情
        """
        await self.send_alert(AlertLevel.P1, title, message, source, details)
    
    async def send_p2_alert(self, title: str, message: str, source: str, details: Optional[Dict] = None):
        """发送P2级告警
        
        Args:
            title: 告警标题
            message: 告警消息
            source: 告警来源
            details: 告警详情
        """
        await self.send_alert(AlertLevel.P2, title, message, source, details)
    
    async def send_p3_alert(self, title: str, message: str, source: str, details: Optional[Dict] = None):
        """发送P3级告警
        
        Args:
            title: 告警标题
            message: 告警消息
            source: 告警来源
            details: 告警详情
        """
        await self.send_alert(AlertLevel.P3, title, message, source, details)
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """获取告警历史
        
        Args:
            limit: 限制数量
        
        Returns:
            List[Alert]: 告警历史
        """
        return self.alert_history[-limit:]
    
    def clear_alert_history(self):
        """清空告警历史"""
        self.alert_history.clear()
    
    def update_config(self, config: AlertConfig):
        """更新告警配置
        
        Args:
            config: 新的告警配置
        """
        self.config = config