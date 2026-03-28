from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.application.agent.services import AgentAppService, VersionAppService, WidgetAppService, WorkspaceAppService, AgentDTO, VersionDTO, WidgetDTO, WorkspaceAgentDTO, LLMModelConfigDTO, AgentFilter
from app.domain.agent.services import CreateAgentCommand, UpdateAgentCommand, CreateWidgetCommand
from app.domain.agent.entities import WidgetTypeEnum, TokenOverflowStrategyEnum, LLMModelConfig

router = APIRouter(prefix="/agents", tags=["智能体管理"])

class CreateAgentRequest(BaseModel):
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    tool_ids: Optional[List[str]] = None
    knowledge_base_ids: Optional[List[str]] = None
    tool_preset_params: Optional[Dict[str, Any]] = None
    support_multimodal: bool = False

class UpdateAgentRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    tool_ids: Optional[List[str]] = None
    knowledge_base_ids: Optional[List[str]] = None
    tool_preset_params: Optional[Dict[str, Any]] = None
    support_multimodal: Optional[bool] = None

class PublishVersionRequest(BaseModel):
    change_log: str

class ReviewVersionRequest(BaseModel):
    approved: bool
    reason: str

class CreateWidgetRequest(BaseModel):
    name: str
    widget_type: WidgetTypeEnum
    model_id: str
    model_provider: str
    allowed_domains: Optional[List[str]] = None
    daily_call_limit: int = -1

class UpdateLLMConfigRequest(BaseModel):
    model_id: str
    provider: str
    temperature: float = 0.7
    top_p: float = 0.7
    top_k: int = 50
    max_tokens: Optional[int] = None
    strategy_type: TokenOverflowStrategyEnum = TokenOverflowStrategyEnum.NONE
    reserve_ratio: Optional[float] = None
    summary_threshold: Optional[int] = None

from app.infrastructure.agent.repositories import InMemoryAgentRepository, InMemoryVersionRepository, InMemoryWidgetRepository, InMemoryWorkspaceRepository, InMemoryLLMModelConfigRepository
# from app.infrastructure.agent.langchain.adapter import LangChainAdapter
from app.domain.agent.services import AgentDomainService, VersionDomainService, WidgetDomainService, WorkspaceDomainService

# 初始化仓储
agent_repo = InMemoryAgentRepository()
version_repo = InMemoryVersionRepository()
widget_repo = InMemoryWidgetRepository()
workspace_repo = InMemoryWorkspaceRepository()
llm_config_repo = InMemoryLLMModelConfigRepository()

# 初始化 LangChain 适配器
# langchain_adapter = LangChainAdapter(api_key="your-api-key-here")

# 初始化领域服务
def get_agent_domain_service():
    return AgentDomainService(agent_repo, version_repo, None)

def get_version_domain_service():
    return VersionDomainService(version_repo, agent_repo)

def get_widget_domain_service():
    return WidgetDomainService(widget_repo)

def get_workspace_domain_service():
    return WorkspaceDomainService(workspace_repo, agent_repo, llm_config_repo)

# 初始化应用服务
def get_agent_app_service():
    return AgentAppService(get_agent_domain_service())

def get_version_app_service():
    return VersionAppService(get_version_domain_service())

def get_widget_app_service():
    return WidgetAppService(get_widget_domain_service())

def get_workspace_app_service():
    return WorkspaceAppService(get_workspace_domain_service())

def get_current_user():
    return "user_123"

@router.post("", response_model=AgentDTO)
def create_agent(
    request: CreateAgentRequest,
    user_id: str = Depends(get_current_user),
    agent_app_service: AgentAppService = Depends(get_agent_app_service)
):
    cmd = CreateAgentCommand(
        name=request.name,
        description=request.description,
        avatar_url=request.avatar_url,
        system_prompt=request.system_prompt,
        welcome_message=request.welcome_message,
        tool_ids=request.tool_ids,
        knowledge_base_ids=request.knowledge_base_ids,
        tool_preset_params=request.tool_preset_params,
        support_multimodal=request.support_multimodal
    )
    return agent_app_service.create_agent(cmd, user_id)

@router.get("/{agent_id}", response_model=AgentDTO)
def get_agent(
    agent_id: str,
    user_id: str = Depends(get_current_user),
    agent_app_service: AgentAppService = Depends(get_agent_app_service)
):
    return agent_app_service.get_agent(agent_id, user_id)

@router.get("", response_model=Dict[str, Any])
def list_agents(
    name: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    agent_app_service: AgentAppService = Depends(get_agent_app_service)
):
    filters = AgentFilter(name=name, enabled=enabled, page=page, page_size=page_size)
    return agent_app_service.list_agents(user_id, filters)

@router.put("/{agent_id}", response_model=AgentDTO)
def update_agent(
    agent_id: str,
    request: UpdateAgentRequest,
    user_id: str = Depends(get_current_user),
    agent_app_service: AgentAppService = Depends(get_agent_app_service)
):
    cmd = UpdateAgentCommand(
        name=request.name,
        description=request.description,
        avatar_url=request.avatar_url,
        system_prompt=request.system_prompt,
        welcome_message=request.welcome_message,
        tool_ids=request.tool_ids,
        knowledge_base_ids=request.knowledge_base_ids,
        tool_preset_params=request.tool_preset_params,
        support_multimodal=request.support_multimodal
    )
    return agent_app_service.update_agent(agent_id, cmd, user_id)

@router.delete("/{agent_id}")
def delete_agent(
    agent_id: str,
    user_id: str = Depends(get_current_user),
    agent_app_service: AgentAppService = Depends(get_agent_app_service)
):
    return {"success": agent_app_service.delete_agent(agent_id, user_id)}

@router.patch("/{agent_id}/status", response_model=AgentDTO)
def toggle_agent_status(
    agent_id: str,
    enabled: bool,
    user_id: str = Depends(get_current_user),
    agent_app_service: AgentAppService = Depends(get_agent_app_service)
):
    return agent_app_service.toggle_agent_status(agent_id, enabled, user_id)

@router.post("/{agent_id}/versions", response_model=VersionDTO)
def publish_version(
    agent_id: str,
    request: PublishVersionRequest,
    user_id: str = Depends(get_current_user),
    version_app_service: VersionAppService = Depends(get_version_app_service)
):
    return version_app_service.publish_version(agent_id, request.change_log, user_id)

@router.get("/{agent_id}/versions", response_model=List[VersionDTO])
def get_version_history(
    agent_id: str,
    user_id: str = Depends(get_current_user),
    version_app_service: VersionAppService = Depends(get_version_app_service)
):
    return version_app_service.get_version_history(agent_id, user_id)

@router.get("/{agent_id}/versions/latest", response_model=VersionDTO)
def get_latest_version(
    agent_id: str,
    version_app_service: VersionAppService = Depends(get_version_app_service)
):
    return version_app_service.get_latest_version(agent_id)

@router.post("/versions/{version_id}/review", response_model=VersionDTO)
def review_version(
    version_id: str,
    request: ReviewVersionRequest,
    reviewer_id: str = Depends(get_current_user),
    version_app_service: VersionAppService = Depends(get_version_app_service)
):
    return version_app_service.review_version(version_id, request.approved, request.reason, reviewer_id)

@router.post("/{agent_id}/widgets", response_model=WidgetDTO)
def create_widget(
    agent_id: str,
    request: CreateWidgetRequest,
    user_id: str = Depends(get_current_user),
    widget_app_service: WidgetAppService = Depends(get_widget_app_service)
):
    cmd = CreateWidgetCommand(
        name=request.name,
        widget_type=request.widget_type,
        model_id=request.model_id,
        model_provider=request.model_provider,
        allowed_domains=request.allowed_domains,
        daily_call_limit=request.daily_call_limit
    )
    return widget_app_service.create_widget(agent_id, cmd, user_id)

@router.post("/widgets/{public_id}/validate")
def validate_widget_access(
    public_id: str,
    referer_domain: str,
    widget_app_service: WidgetAppService = Depends(get_widget_app_service)
):
    return {"allowed": widget_app_service.validate_domain_access(public_id, referer_domain)}

@router.post("/widgets/{public_id}/check-limit")
def check_widget_limit(
    public_id: str,
    widget_app_service: WidgetAppService = Depends(get_widget_app_service)
):
    return {"within_limit": widget_app_service.check_daily_limit(public_id)}

@router.post("/widgets/{public_id}/increment-calls")
def increment_widget_calls(
    public_id: str,
    widget_app_service: WidgetAppService = Depends(get_widget_app_service)
):
    return {"current_calls": widget_app_service.increment_daily_calls(public_id)}

@router.post("/workspace/add")
def add_to_workspace(
    agent_id: str,
    user_id: str = Depends(get_current_user),
    workspace_app_service: WorkspaceAppService = Depends(get_workspace_app_service)
):
    return workspace_app_service.add_to_workspace(user_id, agent_id)

@router.post("/workspace/remove")
def remove_from_workspace(
    agent_id: str,
    user_id: str = Depends(get_current_user),
    workspace_app_service: WorkspaceAppService = Depends(get_workspace_app_service)
):
    return {"success": workspace_app_service.remove_from_workspace(user_id, agent_id)}

@router.get("/workspace/list", response_model=List[WorkspaceAgentDTO])
def get_workspace_agents(
    user_id: str = Depends(get_current_user),
    workspace_app_service: WorkspaceAppService = Depends(get_workspace_app_service)
):
    return workspace_app_service.get_workspace_agents(user_id)

@router.put("/workspace/{agent_id}/model-config", response_model=LLMModelConfigDTO)
def update_model_config(
    agent_id: str,
    request: UpdateLLMConfigRequest,
    user_id: str = Depends(get_current_user),
    workspace_app_service: WorkspaceAppService = Depends(get_workspace_app_service)
):
    config = LLMModelConfig(
        model_id=request.model_id,
        provider=request.provider,
        temperature=request.temperature,
        top_p=request.top_p,
        top_k=request.top_k,
        max_tokens=request.max_tokens,
        strategy_type=request.strategy_type,
        reserve_ratio=request.reserve_ratio,
        summary_threshold=request.summary_threshold
    )
    return workspace_app_service.update_model_config(user_id, agent_id, config)
