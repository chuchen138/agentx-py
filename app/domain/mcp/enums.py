from enum import Enum


class ToolType(Enum):
    GLOBAL = "GLOBAL"
    USER = "USER"
    EXTERNAL = "EXTERNAL"


class MCPProtocolVersion(Enum):
    V1_0 = "1.0"
    V2_0 = "2.0"
