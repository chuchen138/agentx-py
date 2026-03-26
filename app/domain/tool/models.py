from pydantic import BaseModel, Field
from typing import List, Optional, Type, Dict, Any
from enum import Enum

class ToolType(str, Enum):
    RAG_SEARCH = "RAG_SEARCH"
    FILE_OPERATION = "FILE_OPERATION"
    DATA_PROCESSING = "DATA_PROCESSING"
    SYSTEM = "SYSTEM"

class PermissionLevel(str, Enum):
    PUBLIC = "PUBLIC"
    USER = "USER"
    ADMIN = "ADMIN"

class ToolDefinition(BaseModel):
    name: str = Field(..., description="工具的唯一标识符")
    description: str = Field(..., description="工具的功能描述")
    tool_type: ToolType = Field(..., description="工具的类型分类")
    version: str = Field(..., description="工具版本")
    provider_id: str = Field(..., description="工具的提供者 ID")
    tags: List[str] = Field(default_factory=list, description="工具的标签列表")
    permission: PermissionLevel = Field(..., description="工具需要的权限级别")
    parameters: Type[BaseModel] = Field(..., description="工具所需的参数定义")
    output: Any = Field(..., description="工具返回的数据结构定义")
    
    async def execute(self, params: dict) -> Any:
        raise NotImplementedError("Subclasses must implement execute method")

# 调用model_rebuild()确保所有模型完全定义
ToolDefinition.model_rebuild()

class BaseTool(BaseModel):
    @classmethod
    def to_definition(cls) -> ToolDefinition:
        raise NotImplementedError("Subclasses must implement to_definition method")

class ToolResult(BaseModel):
    success: bool = Field(..., description="执行是否成功")
    data: Optional[Any] = Field(None, description="执行结果数据")
    error: Optional[str] = Field(None, description="错误信息")
    duration: float = Field(..., description="执行耗时（秒）")

class RagSearchParameters(BaseModel):
    query: str = Field(..., description="检索查询文本", min_length=1)
    dataset_id: str = Field(..., description="数据集 ID")
    top_k: int = Field(default=5, ge=1, le=20, description="返回结果数量")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="相似度阈值")
    use_rerank: bool = Field(default=False, description="是否启用重排序")
    use_hybrid: bool = Field(default=True, description="是否使用混合检索")

class RagSearchResult(BaseModel):
    content: str = Field(..., description="文档内容")
    score: float = Field(..., description="相似度分数")
    metadata: dict = Field(default_factory=dict, description="元数据")
    document_id: str = Field(..., description="文档 ID")

class FileReadParameters(BaseModel):
    file_path: str = Field(..., description="文件路径", pattern=r"^[a-zA-Z0-9_/.\-]+")
    max_size: int = Field(default=1048576, description="最大文件大小（字节）", ge=1)
    encoding: str = Field(default="utf-8", description="文件编码")

class FileReadResult(BaseModel):
    content: str = Field(..., description="文件内容")
    size: int = Field(..., description="文件大小（字节）")
    lines: int = Field(..., description="文件行数")

class FileWriteParameters(BaseModel):
    file_path: str = Field(..., description="文件路径", pattern=r"^[a-zA-Z0-9_/.\-]+")
    content: str = Field(..., description="文件内容")
    encoding: str = Field(default="utf-8", description="文件编码")
    overwrite: bool = Field(default=False, description="是否覆盖已存在文件")

class FileWriteResult(BaseModel):
    success: bool = Field(..., description="写入是否成功")
    size: int = Field(..., description="写入大小（字节）")

class FileDeleteParameters(BaseModel):
    file_path: str = Field(..., description="文件路径", pattern=r"^[a-zA-Z0-9_/.\-]+")

class FileDeleteResult(BaseModel):
    success: bool = Field(..., description="删除是否成功")

class FileListParameters(BaseModel):
    directory: str = Field(..., description="目录路径", pattern=r"^[a-zA-Z0-9_/.\-]+")
    pattern: str = Field(default="*", description="文件匹配模式")
    recursive: bool = Field(default=False, description="是否递归遍历")

class FileListResult(BaseModel):
    files: List[str] = Field(..., description="文件列表")
    directories: List[str] = Field(..., description="目录列表")

class SystemInfoParameters(BaseModel):
    details: bool = Field(default=False, description="是否返回详细信息")

class SystemInfoResult(BaseModel):
    os: str = Field(..., description="操作系统")
    version: str = Field(..., description="系统版本")
    cpu: int = Field(..., description="CPU 核心数")
    memory: int = Field(..., description="内存大小（MB）")
    disk: Dict[str, int] = Field(..., description="磁盘使用情况")

class DataParseParameters(BaseModel):
    data: str = Field(..., description="要解析的数据")
    format: str = Field(..., description="数据格式", pattern=r"^(json|yaml|xml)$")

class DataParseResult(BaseModel):
    parsed: Any = Field(..., description="解析后的数据")
    format: str = Field(..., description="数据格式")
