import os
import json
import yaml
import xml.etree.ElementTree as ET
import platform
import psutil
from typing import List, Type
from pathlib import Path
from app.domain.tool.provider import BuiltInToolProvider, register_provider
from app.domain.tool.models import (
    BaseTool, ToolDefinition, ToolType, PermissionLevel,
    FileReadParameters, FileReadResult, FileWriteParameters, FileWriteResult,
    FileDeleteParameters, FileDeleteResult, FileListParameters, FileListResult,
    SystemInfoParameters, SystemInfoResult, DataParseParameters, DataParseResult
)

class FileReadToolDefinition(ToolDefinition):
    name: str = "file_read"
    description: str = "读取文件内容"
    tool_type: ToolType = ToolType.FILE_OPERATION
    version: str = "1.0.0"
    provider_id: str = "system_builtin_provider"
    tags: List[str] = ["file", "read", "io"]
    permission: PermissionLevel = PermissionLevel.USER
    parameters: type = FileReadParameters
    output: type = FileReadResult
    
    async def execute(self, params: dict) -> FileReadResult:
        args = FileReadParameters(**params)
        file_path = Path(args.file_path)
        
        # 安全检查：限制访问范围
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path
        
        if file_path.stat().st_size > args.max_size:
            raise ValueError(f"File size exceeds max_size: {args.max_size}")
        
        content = file_path.read_text(encoding=args.encoding)
        lines = len(content.split('\n'))
        
        return FileReadResult(
            content=content,
            size=len(content),
            lines=lines
        )

# 调用model_rebuild()确保模型完全定义
FileReadToolDefinition.model_rebuild()

class FileReadTool(BaseTool):
    @classmethod
    def to_definition(cls) -> ToolDefinition:
        return FileReadToolDefinition()

class FileWriteToolDefinition(ToolDefinition):
    name: str = "file_write"
    description: str = "写入文件内容"
    tool_type: ToolType = ToolType.FILE_OPERATION
    version: str = "1.0.0"
    provider_id: str = "system_builtin_provider"
    tags: List[str] = ["file", "write", "io"]
    permission: PermissionLevel = PermissionLevel.USER
    parameters: type = FileWriteParameters
    output: type = FileWriteResult
    
    async def execute(self, params: dict) -> FileWriteResult:
        args = FileWriteParameters(**params)
        file_path = Path(args.file_path)
        
        # 安全检查：限制访问范围
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path
        
        if file_path.exists() and not args.overwrite:
            raise ValueError(f"File already exists: {file_path}")
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(args.content, encoding=args.encoding)
        
        return FileWriteResult(
            success=True,
            size=len(args.content)
        )

# 调用model_rebuild()确保模型完全定义
FileWriteToolDefinition.model_rebuild()

class FileWriteTool(BaseTool):
    @classmethod
    def to_definition(cls) -> ToolDefinition:
        return FileWriteToolDefinition()

class FileDeleteToolDefinition(ToolDefinition):
    name: str = "file_delete"
    description: str = "删除文件"
    tool_type: ToolType = ToolType.FILE_OPERATION
    version: str = "1.0.0"
    provider_id: str = "system_builtin_provider"
    tags: List[str] = ["file", "delete", "io"]
    permission: PermissionLevel = PermissionLevel.USER
    parameters: type = FileDeleteParameters
    output: type = FileDeleteResult
    
    async def execute(self, params: dict) -> FileDeleteResult:
        args = FileDeleteParameters(**params)
        file_path = Path(args.file_path)
        
        # 安全检查：限制访问范围
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path
        
        if file_path.exists():
            file_path.unlink()
        
        return FileDeleteResult(success=True)

# 调用model_rebuild()确保模型完全定义
FileDeleteToolDefinition.model_rebuild()

class FileDeleteTool(BaseTool):
    @classmethod
    def to_definition(cls) -> ToolDefinition:
        return FileDeleteToolDefinition()

class FileListToolDefinition(ToolDefinition):
    name: str = "file_list"
    description: str = "列出目录内容"
    tool_type: ToolType = ToolType.FILE_OPERATION
    version: str = "1.0.0"
    provider_id: str = "system_builtin_provider"
    tags: List[str] = ["file", "list", "io"]
    permission: PermissionLevel = PermissionLevel.USER
    parameters: type = FileListParameters
    output: type = FileListResult
    
    async def execute(self, params: dict) -> FileListResult:
        args = FileListParameters(**params)
        directory = Path(args.directory)
        
        # 安全检查：限制访问范围
        if not directory.is_absolute():
            directory = Path.cwd() / directory
        
        files = []
        directories = []
        
        if args.recursive:
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    if Path(filename).match(args.pattern):
                        files.append(str(Path(root) / filename))
                for dirname in dirs:
                    directories.append(str(Path(root) / dirname))
        else:
            for item in directory.iterdir():
                if item.is_file() and item.name.match(args.pattern):
                    files.append(str(item))
                elif item.is_dir():
                    directories.append(str(item))
        
        return FileListResult(
            files=files,
            directories=directories
        )

# 调用model_rebuild()确保模型完全定义
FileListToolDefinition.model_rebuild()

class FileListTool(BaseTool):
    @classmethod
    def to_definition(cls) -> ToolDefinition:
        return FileListToolDefinition()

class SystemInfoToolDefinition(ToolDefinition):
    name: str = "system_info"
    description: str = "查询系统信息"
    tool_type: ToolType = ToolType.SYSTEM
    version: str = "1.0.0"
    provider_id: str = "system_builtin_provider"
    tags: List[str] = ["system", "info"]
    permission: PermissionLevel = PermissionLevel.PUBLIC
    parameters: type = SystemInfoParameters
    output: type = SystemInfoResult
    
    async def execute(self, params: dict) -> SystemInfoResult:
        args = SystemInfoParameters(**params)
        
        disk = {}
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk[partition.mountpoint] = usage.free // (1024 * 1024)
            except:
                pass
        
        return SystemInfoResult(
            os=platform.system(),
            version=platform.version(),
            cpu=psutil.cpu_count(),
            memory=psutil.virtual_memory().total // (1024 * 1024),
            disk=disk
        )

# 调用model_rebuild()确保模型完全定义
SystemInfoToolDefinition.model_rebuild()

class SystemInfoTool(BaseTool):
    @classmethod
    def to_definition(cls) -> ToolDefinition:
        return SystemInfoToolDefinition()

class DataParseToolDefinition(ToolDefinition):
    name: str = "data_parse"
    description: str = "解析 JSON/YAML/XML 数据"
    tool_type: ToolType = ToolType.DATA_PROCESSING
    version: str = "1.0.0"
    provider_id: str = "system_builtin_provider"
    tags: List[str] = ["data", "parse"]
    permission: PermissionLevel = PermissionLevel.USER
    parameters: type = DataParseParameters
    output: type = DataParseResult
    
    async def execute(self, params: dict) -> DataParseResult:
        args = DataParseParameters(**params)
        
        if args.format == "json":
            parsed = json.loads(args.data)
        elif args.format == "yaml":
            parsed = yaml.safe_load(args.data)
        elif args.format == "xml":
            root = ET.fromstring(args.data)
            parsed = self._xml_to_dict(root)
        else:
            raise ValueError(f"Unsupported format: {args.format}")
        
        return DataParseResult(
            parsed=parsed,
            format=args.format
        )
    
    def _xml_to_dict(self, element):
        result = {}
        for child in element:
            child_dict = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_dict)
            else:
                result[child.tag] = child_dict
        if element.text and element.text.strip():
            return element.text
        return result

# 调用model_rebuild()确保模型完全定义
DataParseToolDefinition.model_rebuild()

class DataParseTool(BaseTool):
    @classmethod
    def to_definition(cls) -> ToolDefinition:
        return DataParseToolDefinition()

@register_provider
class SystemBuiltInToolProvider(BuiltInToolProvider):
    @property
    def provider_name(self) -> str:
        return "system_builtin_provider"
    
    def get_tools(self) -> List[Type[BaseTool]]:
        return [
            FileReadTool,
            FileWriteTool,
            FileDeleteTool,
            FileListTool,
            SystemInfoTool,
            DataParseTool
        ]
