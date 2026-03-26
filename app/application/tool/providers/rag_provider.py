from typing import List, Type
from app.domain.tool.provider import BuiltInToolProvider, register_provider
from app.domain.tool.models import (
    BaseTool, ToolDefinition, ToolType, PermissionLevel,
    RagSearchParameters, RagSearchResult, ToolResult
)

class RagSearchToolDefinition(ToolDefinition):
    name: str = "rag_search"
    description: str = "基于向量相似度的知识库检索"
    tool_type: ToolType = ToolType.RAG_SEARCH
    version: str = "1.0.0"
    provider_id: str = "rag_builtin_provider"
    tags: List[str] = ["rag", "search", "vector"]
    permission: PermissionLevel = PermissionLevel.USER
    parameters: type = RagSearchParameters
    output: type = List[RagSearchResult]
    
    async def execute(self, params: dict) -> List[RagSearchResult]:
        # 这里应该调用 RAGSearchAppService
        # 暂时返回模拟数据
        return [
            RagSearchResult(
                content="这是测试文档内容1",
                score=0.95,
                metadata={"source": "test1.txt"},
                document_id="doc1"
            ),
            RagSearchResult(
                content="这是测试文档内容2",
                score=0.87,
                metadata={"source": "test2.txt"},
                document_id="doc2"
            )
        ]

# 调用model_rebuild()确保模型完全定义
RagSearchToolDefinition.model_rebuild()

class RagSearchTool(BaseTool):
    @classmethod
    def to_definition(cls) -> ToolDefinition:
        return RagSearchToolDefinition()

class RagHybridSearchToolDefinition(ToolDefinition):
    name: str = "rag_hybrid_search"
    description: str = "基于混合检索的知识库查询"
    tool_type: ToolType = ToolType.RAG_SEARCH
    version: str = "1.0.0"
    provider_id: str = "rag_builtin_provider"
    tags: List[str] = ["rag", "search", "hybrid"]
    permission: PermissionLevel = PermissionLevel.USER
    parameters: type = RagSearchParameters
    output: type = List[RagSearchResult]
    
    async def execute(self, params: dict) -> List[RagSearchResult]:
        # 这里应该调用 RAGSearchAppService 进行混合检索
        # 暂时返回模拟数据
        return [
            RagSearchResult(
                content="混合检索结果1",
                score=0.92,
                metadata={"source": "hybrid1.txt"},
                document_id="hybrid1"
            )
        ]

# 调用model_rebuild()确保模型完全定义
RagHybridSearchToolDefinition.model_rebuild()

class RagHybridSearchTool(BaseTool):
    @classmethod
    def to_definition(cls) -> ToolDefinition:
        return RagHybridSearchToolDefinition()

class RagKeywordSearchToolDefinition(ToolDefinition):
    name: str = "rag_keyword_search"
    description: str = "基于关键词的知识库检索"
    tool_type: ToolType = ToolType.RAG_SEARCH
    version: str = "1.0.0"
    provider_id: str = "rag_builtin_provider"
    tags: List[str] = ["rag", "search", "keyword"]
    permission: PermissionLevel = PermissionLevel.USER
    parameters: type = RagSearchParameters
    output: type = List[RagSearchResult]
    
    async def execute(self, params: dict) -> List[RagSearchResult]:
        # 这里应该调用 RAGSearchAppService 进行关键词检索
        # 暂时返回模拟数据
        return [
            RagSearchResult(
                content="关键词检索结果1",
                score=0.85,
                metadata={"source": "keyword1.txt"},
                document_id="keyword1"
            )
        ]

# 调用model_rebuild()确保模型完全定义
RagKeywordSearchToolDefinition.model_rebuild()

class RagKeywordSearchTool(BaseTool):
    @classmethod
    def to_definition(cls) -> ToolDefinition:
        return RagKeywordSearchToolDefinition()

@register_provider
class RagBuiltInToolProvider(BuiltInToolProvider):
    @property
    def provider_name(self) -> str:
        return "rag_builtin_provider"
    
    def get_tools(self) -> List[Type[BaseTool]]:
        return [
            RagSearchTool,
            RagHybridSearchTool,
            RagKeywordSearchTool
        ]
