#!/usr/bin/env python3
"""系统测试脚本"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    try:
        from app.domain.user.model import UserModel, UserSettingsModel
        from app.domain.user.repository import SQLAlchemyUserRepository, SQLAlchemyUserSettingsRepository
        from app.domain.user.service import UserDomainService, UserSettingsDomainService
        from app.application.user.user_app_service import UserAppService
        from app.application.user.login_app_service import LoginAppService
        from app.application.user.sso_app_service import SsoAppService
        from app.application.user.user_settings_app