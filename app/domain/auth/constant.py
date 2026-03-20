from enum import Enum


class FeatureType(str, Enum):
    """功能类型枚举"""
    LOGIN = "LOGIN"
    REGISTER = "REGISTER"


class AuthFeatureKey(str, Enum):
    """认证功能键枚举"""
    NORMAL_LOGIN = "NORMAL_LOGIN"
    GITHUB_LOGIN = "GITHUB_LOGIN"
    COMMUNITY_LOGIN = "COMMUNITY_LOGIN"
    USER_REGISTER = "USER_REGISTER"


class SsoProvider(str, Enum):
    """SSO 提供商枚举"""
    COMMUNITY = "COMMUNITY"
    GITHUB = "GITHUB"
    GOOGLE = "GOOGLE"
    WECHAT = "WECHAT"
