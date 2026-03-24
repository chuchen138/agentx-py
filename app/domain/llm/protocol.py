from abc import ABC, abstractmethod
from typing import Optional
from app.domain.llm.config import ProviderConfig
from app.domain.llm.enums import ProviderProtocol


class ChatRequest:
    """聊天请求"""
    def __init__(self, messages, model, temperature=0.7, max_tokens=1000):
        self.messages = messages
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens


class ChatResponse:
    """聊天响应"""
    def __init__(self, content, model, usage=None):
        self.content = content
        self.model = model
        self.usage = usage


class EmbeddingRequest:
    """嵌入请求"""
    def __init__(self, input_text, model):
        self.input_text = input_text
        self.model = model


class EmbeddingResponse:
    """嵌入响应"""
    def __init__(self, embeddings, model, usage=None):
        self.embeddings = embeddings
        self.model = model
        self.usage = usage


class ProtocolAdapter(ABC):
    """协议适配器抽象基类"""
    
    @abstractmethod
    async def send_chat_request(self, config: ProviderConfig, request: ChatRequest) -> ChatResponse:
        """发送聊天请求"""
        pass
    
    @abstractmethod
    async def send_embedding_request(self, config: ProviderConfig, request: EmbeddingRequest) -> EmbeddingResponse:
        """发送嵌入请求"""
        pass
    
    @abstractmethod
    def validate_config(self, config: ProviderConfig) -> bool:
        """验证配置"""
        pass


class OpenAIProtocolAdapter(ProtocolAdapter):
    """OpenAI协议适配器"""
    
    async def send_chat_request(self, config: ProviderConfig, request: ChatRequest) -> ChatResponse:
        """发送聊天请求"""
        # 这里使用llama-index或直接httpx实现
        # 暂时返回模拟响应
        return ChatResponse(
            content="This is a mock response",
            model=request.model,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )
    
    async def send_embedding_request(self, config: ProviderConfig, request: EmbeddingRequest) -> EmbeddingResponse:
        """发送嵌入请求"""
        # 暂时返回模拟响应
        return EmbeddingResponse(
            embeddings=[[0.1] * 1536],
            model=request.model,
            usage={"prompt_tokens": 5, "total_tokens": 5}
        )
    
    def validate_config(self, config: ProviderConfig) -> bool:
        """验证配置"""
        if not config.api_key:
            print("apikey 认证失败: API key 不能为空")
            return False
        if config.base_url and not config.base_url.startswith("https://"):
            print("apikey 认证失败: Base URL 必须使用 https")
            return False
        # 检查 API key 格式
        if not config.api_key.strip():
            print("apikey 认证失败: API key 不能只包含空白字符")
            return False
        return True


class MoonshotProtocolAdapter(ProtocolAdapter):
    """Moonshot协议适配器"""
    
    async def send_chat_request(self, config: ProviderConfig, request: ChatRequest) -> ChatResponse:
        """发送聊天请求"""
        # 暂时返回模拟响应
        return ChatResponse(
            content="This is a mock response",
            model=request.model,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )
    
    async def send_embedding_request(self, config: ProviderConfig, request: EmbeddingRequest) -> EmbeddingResponse:
        """发送嵌入请求"""
        # 暂时返回模拟响应
        return EmbeddingResponse(
            embeddings=[[0.1] * 1536],
            model=request.model,
            usage={"prompt_tokens": 5, "total_tokens": 5}
        )
    
    def validate_config(self, config: ProviderConfig) -> bool:
        """验证配置"""
        return bool(config.api_key)


class AzureOpenAIProtocolAdapter(ProtocolAdapter):
    """Azure OpenAI协议适配器"""
    
    async def send_chat_request(self, config: ProviderConfig, request: ChatRequest) -> ChatResponse:
        """发送聊天请求"""
        # 暂时返回模拟响应
        return ChatResponse(
            content="This is a mock response",
            model=request.model,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )
    
    async def send_embedding_request(self, config: ProviderConfig, request: EmbeddingRequest) -> EmbeddingResponse:
        """发送嵌入请求"""
        # 暂时返回模拟响应
        return EmbeddingResponse(
            embeddings=[[0.1] * 1536],
            model=request.model,
            usage={"prompt_tokens": 5, "total_tokens": 5}
        )
    
    def validate_config(self, config: ProviderConfig) -> bool:
        """验证配置"""
        return bool(config.api_key) and bool(config.base_url)


class CustomProtocolAdapter(ProtocolAdapter):
    """自定义协议适配器"""
    
    async def send_chat_request(self, config: ProviderConfig, request: ChatRequest) -> ChatResponse:
        """发送聊天请求"""
        # 暂时返回模拟响应
        return ChatResponse(
            content="This is a mock response",
            model=request.model,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )
    
    async def send_embedding_request(self, config: ProviderConfig, request: EmbeddingRequest) -> EmbeddingResponse:
        """发送嵌入请求"""
        # 暂时返回模拟响应
        return EmbeddingResponse(
            embeddings=[[0.1] * 1536],
            model=request.model,
            usage={"prompt_tokens": 5, "total_tokens": 5}
        )
    
    def validate_config(self, config: ProviderConfig) -> bool:
        """验证配置"""
        return bool(config.api_key) and bool(config.base_url)


class ProtocolAdapterFactory:
    """协议适配器工厂"""
    _adapters = {
        ProviderProtocol.OPENAI: OpenAIProtocolAdapter(),
        ProviderProtocol.MOONSHOT: MoonshotProtocolAdapter(),
        ProviderProtocol.AZURE_OPENAI: AzureOpenAIProtocolAdapter(),
        ProviderProtocol.CUSTOM: CustomProtocolAdapter(),
    }
    
    @classmethod
    def get_adapter(cls, protocol: ProviderProtocol) -> ProtocolAdapter:
        """获取适配器"""
        return cls._adapters.get(protocol, CustomProtocolAdapter())
