from typing import List, Optional, Dict, Any
from datetime import date
from pydantic import BaseModel, Field
from app.domain.agent.entities import AgentEntity, AgentVersionEntity, AgentWidgetEntity, WorkspaceAgentEntity, LLMModelConfig, PublishStatusEnum, WidgetTypeEnum, TokenOverflowStrategyEnum
from app.domain.agent.services import AgentDomainService, VersionDomainService, WidgetDomainService, WorkspaceDomainService, CreateAgentCommand, UpdateAgentCommand, CreateWidgetCommand

class AgentDTO(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    tool_ids: List[str] = []
    knowledge_base_ids: List[str] = []
    tool_preset_params: Dict[str, Any] = {}
    current_version_id: Optional[str] = None
    enabled: bool
    support_multimodal: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

class VersionDTO(BaseModel):
    id: str
    agent_id: str
    version_number: str
    agent_name_snapshot: str
    system_prompt_snapshot: Optional[str] = None
    tool_ids_snapshot: List[str] = []
    knowledge_base_ids_snapshot: List[str] = []
    change_log: Optional[str] = None
    publish_status: PublishStatusEnum
    review_rejection_reason: Optional[str] = None
    reviewer_id: Optional[str] = None
    published_at: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True

class WidgetDTO(BaseModel):
    id: str
    agent_id: str
    public_id: str
    name: str
    widget_type: WidgetTypeEnum
    model_id: str
    model_provider: str
    allowed_domains: List[str] = []
    daily_call_limit: int = -1
    enabled: bool
    embed_code: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

class WorkspaceAgentDTO(BaseModel):
    id: str
    user_id: str
    agent_id: str
    custom_name: Optional[str] = None
    added_at: str
    
    class Config:
        from_attributes = True

class LLMModelConfigDTO(BaseModel):
    model_id: str
    provider: str
    temperature: float = 0.7
    top_p: float = 0.7
    top_k: int = 50
    max_tokens: Optional[int] = None
    strategy_type: TokenOverflowStrategyEnum = TokenOverflowStrategyEnum.NONE
    reserve_ratio: Optional[float] = None
    summary_threshold: Optional[int] = None
    
    class Config:
        from_attributes = True

class AgentFilter(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    page: int = 1
    page_size: int = 10

class AgentAppService:
    def __init__(self, agent_domain_service: AgentDomainService):
        self.agent_domain_service = agent_domain_service
    
    def create_agent(self, cmd: CreateAgentCommand, user_id: str) -> AgentDTO:
        agent = self.agent_domain_service.create_agent(user_id, cmd)
        return self._to_agent_dto(agent)
    
    def update_agent(self, agent_id: str, cmd: UpdateAgentCommand, user_id: str) -> AgentDTO:
        agent = self.agent_domain_service.update_agent(agent_id, cmd)
        return self._to_agent_dto(agent)
    
    def delete_agent(self, agent_id: str, user_id: str) -> bool:
        return self.agent_domain_service.delete_agent(agent_id)
    
    def get_agent(self, agent_id: str, user_id: str) -> AgentDTO:
        agent = self.agent_domain_service.agent_repo.find_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        return self._to_agent_dto(agent)
    
    def list_agents(self, user_id: str, filters: AgentFilter) -> Dict[str, Any]:
        agents = self.agent_domain_service.agent_repo.find_by_user_id(user_id, {
            "name": filters.name,
            "enabled": filters.enabled
        })
        total = len(agents)
        start = (filters.page - 1) * filters.page_size
        end = start + filters.page_size
        paginated_agents = agents[start:end]
        
        return {
            "total": total,
            "page": filters.page,
            "page_size": filters.page_size,
            "items": [self._to_agent_dto(agent) for agent in paginated_agents]
        }
    
    def toggle_agent_status(self, agent_id: str, enabled: bool, user_id: str) -> AgentDTO:
        agent = self.agent_domain_service.agent_repo.find_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        if enabled:
            agent.enable()
        else:
            agent.disable()
        
        updated_agent = self.agent_domain_service.agent_repo.update(agent)
        return self._to_agent_dto(updated_agent)
    
    def _to_agent_dto(self, agent: AgentEntity) -> AgentDTO:
        return AgentDTO(
            id=agent.id,
            user_id=agent.user_id,
            name=agent.name,
            description=agent.description,
            avatar_url=agent.avatar_url,
            system_prompt=agent.system_prompt,
            welcome_message=agent.welcome_message,
            tool_ids=agent.tool_ids,
            knowledge_base_ids=agent.knowledge_base_ids,
            tool_preset_params=agent.tool_preset_params,
            current_version_id=agent.current_version_id,
            enabled=agent.enabled,
            support_multimodal=agent.support_multimodal,
            created_at=agent.created_at.isoformat(),
            updated_at=agent.updated_at.isoformat()
        )

class VersionAppService:
    def __init__(self, version_domain_service: VersionDomainService):
        self.version_domain_service = version_domain_service
    
    def publish_version(self, agent_id: str, change_log: str, user_id: str) -> VersionDTO:
        version = self.version_domain_service.publish_new_version(agent_id, change_log)
        return self._to_version_dto(version)
    
    def review_version(self, version_id: str, approved: bool, reason: str, reviewer_id: str) -> VersionDTO:
        if approved:
            self.version_domain_service.approve_version(version_id, reviewer_id)
        else:
            self.version_domain_service.reject_version(version_id, reason, reviewer_id)
        
        version = self.version_domain_service.version_repo.find_by_id(version_id)
        return self._to_version_dto(version)
    
    def get_version_history(self, agent_id: str, user_id: str) -> List[VersionDTO]:
        versions = self.version_domain_service.version_repo.find_by_agent_id(agent_id)
        return [self._to_version_dto(version) for version in versions]
    
    def get_latest_version(self, agent_id: str) -> VersionDTO:
        version = self.version_domain_service.version_repo.find_latest_version(agent_id)
        if not version:
            raise ValueError(f"No versions found for agent: {agent_id}")
        return self._to_version_dto(version)
    
    def _to_version_dto(self, version: AgentVersionEntity) -> VersionDTO:
        return VersionDTO(
            id=version.id,
            agent_id=version.agent_id,
            version_number=version.version_number,
            agent_name_snapshot=version.agent_name_snapshot,
            system_prompt_snapshot=version.system_prompt_snapshot,
            tool_ids_snapshot=version.tool_ids_snapshot,
            knowledge_base_ids_snapshot=version.knowledge_base_ids_snapshot,
            change_log=version.change_log,
            publish_status=version.publish_status,
            review_rejection_reason=version.review_rejection_reason,
            reviewer_id=version.reviewer_id,
            published_at=version.published_at.isoformat() if version.published_at else None,
            created_at=version.created_at.isoformat()
        )

class WidgetAppService:
    def __init__(self, widget_domain_service: WidgetDomainService):
        self.widget_domain_service = widget_domain_service
    
    def create_widget(self, agent_id: str, cmd: CreateWidgetCommand, user_id: str) -> WidgetDTO:
        widget = self.widget_domain_service.create_widget(agent_id, cmd)
        return self._to_widget_dto(widget)
    
    def validate_domain_access(self, public_id: str, referer_domain: str) -> bool:
        widget = self.widget_domain_service.widget_repo.find_by_public_id(public_id)
        if not widget or not widget.enabled:
            return False
        return self.widget_domain_service.validate_domain_access(widget, referer_domain)
    
    def check_daily_limit(self, public_id: str) -> bool:
        widget = self.widget_domain_service.widget_repo.find_by_public_id(public_id)
        if not widget:
            return False
        return self.widget_domain_service.check_daily_limit(widget, date.today())
    
    def increment_daily_calls(self, public_id: str) -> int:
        widget = self.widget_domain_service.widget_repo.find_by_public_id(public_id)
        if not widget:
            raise ValueError(f"Widget not found: {public_id}")
        return self.widget_domain_service.widget_repo.increment_daily_calls(widget.id, date.today())
    
    def _to_widget_dto(self, widget: AgentWidgetEntity) -> WidgetDTO:
        return WidgetDTO(
            id=widget.id,
            agent_id=widget.agent_id,
            public_id=widget.public_id,
            name=widget.name,
            widget_type=widget.widget_type,
            model_id=widget.model_id,
            model_provider=widget.model_provider,
            allowed_domains=widget.allowed_domains,
            daily_call_limit=widget.daily_call_limit,
            enabled=widget.enabled,
            embed_code=widget.embed_code,
            created_at=widget.created_at.isoformat(),
            updated_at=widget.updated_at.isoformat()
        )

class WorkspaceAppService:
    def __init__(self, workspace_domain_service: WorkspaceDomainService):
        self.workspace_domain_service = workspace_domain_service
    
    def add_to_workspace(self, user_id: str, agent_id: str) -> WorkspaceAgentDTO:
        workspace_agent = self.workspace_domain_service.add_to_workspace(user_id, agent_id)
        return self._to_workspace_agent_dto(workspace_agent)
    
    def remove_from_workspace(self, user_id: str, agent_id: str) -> bool:
        return self.workspace_domain_service.remove_from_workspace(user_id, agent_id)
    
    def update_model_config(self, user_id: str, agent_id: str, config: LLMModelConfig) -> LLMModelConfigDTO:
        updated_config = self.workspace_domain_service.update_model_config(user_id, agent_id, config)
        return self._to_llm_config_dto(updated_config)
    
    def get_workspace_agents(self, user_id: str) -> List[WorkspaceAgentDTO]:
        agents = self.workspace_domain_service.workspace_repo.find_by_user_id(user_id)
        return [self._to_workspace_agent_dto(agent) for agent in agents]
    
    def _to_workspace_agent_dto(self, workspace_agent: WorkspaceAgentEntity) -> WorkspaceAgentDTO:
        return WorkspaceAgentDTO(
            id=workspace_agent.id,
            user_id=workspace_agent.user_id,
            agent_id=workspace_agent.agent_id,
            custom_name=workspace_agent.custom_name,
            added_at=workspace_agent.added_at.isoformat()
        )
    
    def _to_llm_config_dto(self, config: LLMModelConfig) -> LLMModelConfigDTO:
        return LLMModelConfigDTO(
            model_id=config.model_id,
            provider=config.provider,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            max_tokens=config.max_tokens,
            strategy_type=config.strategy_type,
            reserve_ratio=config.reserve_ratio,
            summary_threshold=config.summary_threshold
        )
