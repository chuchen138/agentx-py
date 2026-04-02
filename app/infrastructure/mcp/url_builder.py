from app.domain.mcp.models import ContainerInfo


class MCPUrlBuilder:
    def build_review_container_url(self, container: ContainerInfo) -> str:
        """
        构建审核容器的 SSE URL
        
        Args:
            container: 容器信息
            
        Returns:
            str: SSE URL
        """
        return f"http://{container.host}:{container.port}/api/v1/mcp/sse"
    
    def build_user_container_url(self, container: ContainerInfo) -> str:
        """
        构建用户容器的 SSE URL
        
        Args:
            container: 容器信息
            
        Returns:
            str: SSE URL
        """
        return f"http://{container.host}:{container.port}/api/v1/mcp/sse"
    
    def build_external_server_url(self, server_url: str) -> str:
        """
        构建外部服务器的 SSE URL
        
        Args:
            server_url: 服务器 URL
            
        Returns:
            str: SSE URL
        """
        if not server_url.endswith('/'):
            server_url += '/'
        return f"{server_url}api/v1/mcp/sse"
