from typing import Optional
from app.domain.mcp.models import ContainerInfo


class MockContainerService:
    def get_review_container(self) -> ContainerInfo:
        """
        获取审核容器
        
        Returns:
            ContainerInfo: 容器信息
        """
        # 模拟返回审核容器信息
        return ContainerInfo(
            container_id="review-container-1",
            name="review-container",
            status="running",
            host="localhost",
            port=8080
        )
    
    def get_or_create_user_container(self, user_id: str) -> ContainerInfo:
        """
        获取或创建用户容器
        
        Args:
            user_id: 用户 ID
            
        Returns:
            ContainerInfo: 容器信息
        """
        # 模拟返回用户容器信息
        return ContainerInfo(
            container_id=f"user-container-{user_id}",
            name=f"user-container-{user_id}",
            status="running",
            host="localhost",
            port=8081
        )
    
    def get_server_for_tool(self, tool_name: str) -> Optional[dict]:
        """
        获取工具对应的外部服务器信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[dict]: 服务器信息
        """
        # 模拟返回外部服务器信息
        return {
            "server_url": "http://external-mcp-server:8080"
        }
