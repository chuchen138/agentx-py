import uuid
from typing import Optional, Dict, Any
from app.domain.user.model import UserSettingsModel, UserSettingsConfig
from app.domain.user.service import UserSettingsDomainService

class UserSettingsAppService:
    """用户设置应用服务"""
    
    def __init__(self, settings_domain_service: UserSettingsDomainService):
        self.settings_domain_service = settings_domain_service
    
    def get_user_settings(self, user_id: uuid.UUID) -> Optional[UserSettingsModel]:
        """获取用户设置"""
        return self.settings_domain_service.get_user_settings(user_id)
    
    def update_user_settings(self, user_id: uuid.UUID, settings_config: UserSettingsConfig) -> UserSettingsModel:
        """更新用户设置"""
        return self.settings_domain_service.update_user_settings(user_id, settings_config)
    
    def reset_user_settings(self, user_id: uuid.UUID) -> UserSettingsModel:
        """重置为默认设置"""
        return self.settings_domain_service.reset_user_settings(user_id)
    
    def get_setting_value(self, user_id: uuid.UUID, setting_key: str) -> Optional[Any]:
        """获取单个设置项"""
        settings = self.settings_domain_service.get_user_settings(user_id)
        if not settings:
            return None
        
        # 递归查找设置值
        def get_nested_value(config: Dict[str, Any], key: str) -> Optional[Any]:
            keys = key.split('.')
            value = config
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return None
            return value
        
        return get_nested_value(settings.setting_config, setting_key)
    
    def update_setting_value(self, user_id: uuid.UUID, setting_key: str, value: Any) -> UserSettingsModel:
        """更新单个设置项"""
        settings = self.settings_domain_service.get_user_settings(user_id)
        if not settings:
            # 如果设置不存在，创建默认设置
            default_config = UserSettingsConfig()
            settings = self.settings_domain_service.update_user_settings(user_id, default_config)
        
        # 递归更新设置值
        def update_nested_value(config: Dict[str, Any], key: str, new_value: Any) -> Dict[str, Any]:
            keys = key.split('.')
            if len(keys) == 1:
                config[keys[0]] = new_value
            else:
                if keys[0] not in config:
                    config[keys[0]] = {}
                update_nested_value(config[keys[0]], '.'.join(keys[1:]), new_value)
            return config
        
        updated_config = update_nested_value(settings.setting_config, setting_key, value)
        settings_config = UserSettingsConfig(**updated_config)
        return self.settings_domain_service.update_user_settings(user_id, settings_config)
