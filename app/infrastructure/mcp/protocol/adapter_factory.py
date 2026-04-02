from app.domain.mcp.enums import MCPProtocolVersion
from app.domain.mcp.protocol_adapter import MCPProtocolAdapter
from app.infrastructure.mcp.protocol.v1_0_adapter import MCPv1_0Adapter


class MCPAdapterFactory:
    @staticmethod
    def create_adapter(version: MCPProtocolVersion) -> MCPProtocolAdapter:
        """
        根据协议版本创建适配器
        
        Args:
            version: MCP 协议版本
            
        Returns:
            MCPProtocolAdapter: 协议适配器实例
        """
        if version == MCPProtocolVersion.V1_0:
            return MCPv1_0Adapter()
        elif version == MCPProtocolVersion.V2_0:
            # 未来实现 V2.0 适配器
            return MCPv1_0Adapter()
        else:
            raise ValueError(f"Unsupported MCP protocol version: {version.value}")
