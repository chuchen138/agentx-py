from typing import Dict, Optional
from app.domain.file.file_type import FileType
from app.application.file.strategy.file_storage_strategy import FileStorageStrategy
from app.application.file.strategy.avatar_file_storage_strategy import AvatarFileStorageStrategy
from app.application.file.strategy.general_file_storage_strategy import GeneralFileStorageStrategy
from app.application.file.strategy.rag_file_storage_strategy import RagFileStorageStrategy


class FileStorageStrategyFactory:
    """文件存储策略工厂"""

    def __init__(self):
        # 初始化策略映射
        self.strategies: Dict[FileType, FileStorageStrategy] = {
            FileType.AVATAR: AvatarFileStorageStrategy(),
            FileType.GENERAL: GeneralFileStorageStrategy(),
            FileType.RAG: RagFileStorageStrategy(),
        }
        # 默认策略
        self.default_strategy = GeneralFileStorageStrategy()

    def get_strategy(self, file_type: FileType) -> FileStorageStrategy:
        """根据文件类型获取策略"""
        return self.strategies.get(file_type, self.default_strategy)

    def register_strategy(self, file_type: FileType, strategy: FileStorageStrategy) -> None:
        """注册新策略"""
        self.strategies[file_type] = strategy

    def unregister_strategy(self, file_type: FileType) -> None:
        """注销策略"""
        if file_type in self.strategies:
            del self.strategies[file_type]

    def get_all_strategies(self) -> Dict[FileType, FileStorageStrategy]:
        """获取所有策略"""
        return self.strategies.copy()

    def get_default_strategy(self) -> FileStorageStrategy:
        """获取默认策略"""
        return self.default_strategy


# 全局策略工厂实例
strategy_factory = FileStorageStrategyFactory()
