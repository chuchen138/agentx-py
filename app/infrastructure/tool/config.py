from pydantic_settings import BaseSettings
from typing import List

class ToolSettings(BaseSettings):
    # 工具启用开关
    enabled: bool = True
    
    # 注册表缓存配置
    cache_ttl: int = 300  # 5 分钟
    cache_size: int = 1000
    
    # RAG 检索参数配置
    rag_default_top_k: int = 5
    rag_max_top_k: int = 20
    rag_similarity_threshold: float = 0.7
    rag_use_rerank: bool = False
    rag_hybrid_weight: float = 0.5
    
    # 工具执行参数配置
    tool_timeout: int = 30  # 秒
    max_concurrency: int = 100
    retry_count: int = 3
    
    # 黑名单配置
    blacklist: List[str] = []
    
    # 日志配置
    log_level: str = "INFO"
    log_sample_rate: float = 1.0
    
    class Config:
        env_prefix = "TOOL_"
        env_file = ".env"

# 全局配置实例
tool_settings = ToolSettings()
