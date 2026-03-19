import pytest
from app.application.file.factory.file_storage_strategy_factory import strategy_factory
from app.domain.file.file_type import FileType
from app.application.file.strategy.avatar_file_storage_strategy import AvatarFileStorageStrategy
from app.application.file.strategy.general_file_storage_strategy import GeneralFileStorageStrategy
from app.application.file.strategy.rag_file_storage_strategy import RagFileStorageStrategy


def test_strategy_factory_get_strategy():
    """测试策略工厂获取策略"""
    # 测试获取头像策略
    avatar_strategy = strategy_factory.get_strategy(FileType.AVATAR)
    assert isinstance(avatar_strategy, AvatarFileStorageStrategy)
    
    # 测试获取通用策略
    general_strategy = strategy_factory.get_strategy(FileType.GENERAL)
    assert isinstance(general_strategy, GeneralFileStorageStrategy)
    
    # 测试获取RAG策略
    rag_strategy = strategy_factory.get_strategy(FileType.RAG)
    assert isinstance(rag_strategy, RagFileStorageStrategy)
    
    # 测试默认策略（当文件类型不存在时）
    # 注意：这里需要创建一个不存在的FileType枚举值，或者修改策略工厂以支持未知类型
    # 暂时跳过这个测试，因为FileType枚举是固定的


def test_strategy_factory_get_all_strategies():
    """测试策略工厂获取所有策略"""
    strategies = strategy_factory.get_all_strategies()
    assert len(strategies) == 3
    assert FileType.AVATAR in strategies
    assert FileType.GENERAL in strategies
    assert FileType.RAG in strategies


def test_strategy_factory_get_default_strategy():
    """测试策略工厂获取默认策略"""
    default_strategy = strategy_factory.get_default_strategy()
    assert isinstance(default_strategy, GeneralFileStorageStrategy)
