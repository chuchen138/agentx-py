from typing import List, Optional, Dict, Any
from datetime import date, datetime
from .entities import AgentEntity, AgentVersionEntity, AgentWidgetEntity, WorkspaceAgentEntity, LLMModelConfig, PublishStatusEnum, WidgetTypeEnum, TokenOverflowStrategyEnum
from .repositories import AgentRepository, VersionRepository, WidgetRepository, WorkspaceRepository, LLMModelConfigRepository

class CreateAgentCommand:
    def __init__(self, name: str, description: Optional[str] = None, 
                 avatar_url: Optional[str] = None, system_prompt: Optional[str] = None, 
                 welcome_message: Optional[str] = None, tool_ids: Optional[List[str]] = None, 
                 knowledge_base_ids: Optional[List[str]] = None, 
                 tool_preset_params: Optional[Dict[str, Any]] = None, 
                 support_multimodal: bool = False):
        self.name = name
        self.description = description
        self.avatar_url = avatar_url
        self.system_prompt = system_prompt
        self.welcome_message = welcome_message
        self.tool_ids = tool_ids or []
        self.knowledge_base_ids = knowledge_base_ids or []
        self.tool_preset_params = tool_preset_params or {}
        self.support_multimodal = support_multimodal

class UpdateAgentCommand:
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None, 
                 avatar_url: Optional[str] = None, system_prompt: Optional[str] = None, 
                 welcome_message: Optional[str] = None, tool_ids: Optional[List[str]] = None, 
                 knowledge_base_ids: Optional[List[str]] = None, 
                 tool_preset_params: Optional[Dict[str, Any]] = None, 
                 support_multimodal: Optional[bool] = None):
        self.name = name
        self.description = description
        self.avatar_url = avatar_url
        self.system_prompt = system_prompt
        self.welcome_message = welcome_message
        self.tool_ids = tool_ids
        self.knowledge_base_ids = knowledge_base_ids
        self.tool_preset_params = tool_preset_params
        self.support_multimodal = support_multimodal

class CreateWidgetCommand:
    def __init__(self, name: str, widget_type: WidgetTypeEnum, model_id: str, 
                 model_provider: str, allowed_domains: Optional[List[str]] = None, 
                 daily_call_limit: int = -1):
        self.name = name
        self.widget_type = widget_type
        self.model_id = model_id
        self.model_provider = model_provider
        self.allowed_domains = allowed_domains or []
        self.daily_call_limit = daily_call_limit

class AgentInfo:
    def __init__(self, name: str, description: str, tools: List[Dict[str, str]]):
        self.name = name
        self.description = description
        self.tools = tools

class AgentDomainService:
    def __init__(self, agent_repo: AgentRepository, version_repo: VersionRepository, langchain_adapter=None):
        self.agent_repo = agent_repo
        self.version_repo = version_repo
        self.langchain_adapter = langchain_adapter
    
    def create_agent(self, user_id: str, create_cmd: CreateAgentCommand) -> AgentEntity:
        agent = AgentEntity(
            user_id=user_id,
            name=create_cmd.name,
            description=create_cmd.description,
            avatar_url=create_cmd.avatar_url,
            system_prompt=create_cmd.system_prompt,
            welcome_message=create_cmd.welcome_message,
            tool_ids=create_cmd.tool_ids,
            knowledge_base_ids=create_cmd.knowledge_base_ids,
            tool_preset_params=create_cmd.tool_preset_params,
            support_multimodal=create_cmd.support_multimodal
        )
        return self.agent_repo.create(agent)
    
    def update_agent(self, agent_id: str, update_cmd: UpdateAgentCommand) -> AgentEntity:
        agent = self.agent_repo.find_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        if update_cmd.name:
            agent.name = update_cmd.name
        if update_cmd.description is not None:
            agent.description = update_cmd.description
        if update_cmd.avatar_url is not None:
            agent.avatar_url = update_cmd.avatar_url
        if update_cmd.system_prompt is not None:
            agent.system_prompt = update_cmd.system_prompt
        if update_cmd.welcome_message is not None:
            agent.welcome_message = update_cmd.welcome_message
        if update_cmd.tool_ids is not None:
            agent.tool_ids = update_cmd.tool_ids
        if update_cmd.knowledge_base_ids is not None:
            agent.knowledge_base_ids = update_cmd.knowledge_base_ids
        if update_cmd.tool_preset_params is not None:
            agent.tool_preset_params = update_cmd.tool_preset_params
        if update_cmd.support_multimodal is not None:
            agent.support_multimodal = update_cmd.support_multimodal
        
        agent.updated_at = datetime.now()
        return self.agent_repo.update(agent)
    
    def delete_agent(self, agent_id: str) -> bool:
        agent = self.agent_repo.find_by_id(agent_id)
        if not agent:
            return False
        
        published_version = self.version_repo.find_published_version(agent_id)
        if published_version:
            raise ValueError("Cannot delete agent with published versions")
        
        return self.agent_repo.delete(agent_id)
    
    def validate_tool_permissions(self, tool_ids: List[str], user_id: str) -> bool:
        return True
    
    def generate_system_prompt(self, agent_info: AgentInfo) -> str:
        if self.langchain_adapter:
            tools_summary = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in agent_info.tools])
            prompt_template = """请为智能体生成一个结构化的系统提示词。

智能体名称：{name}
智能体描述：{description}
智能体能力：
{tools}

请按照以下 XML 格式输出：
<role_and_personality>
角色和个性定义
</role_and_personality>

<capabilities_summary>
能力摘要
</capabilities_summary>

<rules_and_framework>
服务规则和问题解决框架
</rules_and_framework>"""
            
            chain = self.langchain_adapter.create_chain(prompt_template)
            result = self.langchain_adapter.run_chain(chain, {
                "name": agent_info.name,
                "description": agent_info.description,
                "tools": tools_summary
            })
            return result
        else:
            tools_summary = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in agent_info.tools])
            prompt = f"<role_and_personality>\n你是{agent_info.name}，{agent_info.description}。\n</role_and_personality>\n\n<capabilities_summary>\n你具备以下能力：\n{tools_summary}\n</capabilities_summary>\n\n<rules_and_framework>\n服务规则：\n1. 始终使用简洁明了的语言\n2. 遇到不清楚的问题时，主动询问用户\n3. 无法回答的问题，引导用户联系人工客服\n4. 严格遵守公司隐私政策\n\n问题解决框架：\n1. 思考：分析用户问题，识别关键信息\n2. 行动：调用相应工具获取数据\n3. 观察：根据工具返回结果组织回答\n4. 确认：确保用户问题得到解决\n</rules_and_framework>"
            return prompt

class VersionDomainService:
    def __init__(self, version_repo: VersionRepository, agent_repo: AgentRepository):
        self.version_repo = version_repo
        self.agent_repo = agent_repo
    
    def publish_new_version(self, agent_id: str, change_log: str) -> AgentVersionEntity:
        agent = self.agent_repo.find_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        versions = self.version_repo.find_by_agent_id(agent_id)
        version_number = self._calculate_next_version(versions)
        
        snapshot = agent.create_snapshot()
        version = AgentVersionEntity(
            agent_id=agent_id,
            version_number=version_number,
            agent_name_snapshot=snapshot["name"],
            system_prompt_snapshot=snapshot["system_prompt"],
            tool_ids_snapshot=snapshot["tool_ids"],
            knowledge_base_ids_snapshot=snapshot["knowledge_base_ids"],
            change_log=change_log
        )
        
        return self.version_repo.create(version)
    
    def _calculate_next_version(self, versions: List[AgentVersionEntity]) -> str:
        if not versions:
            return "1.0.0"
        
        latest_version = max(versions, key=lambda v: v.created_at)
        major, minor, patch = map(int, latest_version.version_number.split('.'))
        return f"{major}.{minor}.{patch + 1}"
    
    def submit_for_review(self, version_id: str) -> None:
        pass
    
    def approve_version(self, version_id: str, reviewer_id: str) -> None:
        pass
    
    def reject_version(self, version_id: str, rejection_reason: str, reviewer_id: str) -> None:
        pass
    
    def remove_version(self, version_id: str) -> None:
        pass

class WidgetDomainService:
    def __init__(self, widget_repo: WidgetRepository):
        self.widget_repo = widget_repo
    
    def create_widget(self, agent_id: str, create_cmd: CreateWidgetCommand) -> AgentWidgetEntity:
        widget = AgentWidgetEntity(
            agent_id=agent_id,
            name=create_cmd.name,
            widget_type=create_cmd.widget_type,
            model_id=create_cmd.model_id,
            model_provider=create_cmd.model_provider,
            allowed_domains=create_cmd.allowed_domains,
            daily_call_limit=create_cmd.daily_call_limit
        )
        return self.widget_repo.create(widget)
    
    def validate_domain_access(self, widget: AgentWidgetEntity, referer_domain: str) -> bool:
        if not widget.allowed_domains:
            return True
        
        for domain in widget.allowed_domains:
            if domain == referer_domain:
                return True
            if domain.startswith('*') and referer_domain.endswith(domain[1:]):
                return True
        
        return False
    
    def check_daily_limit(self, widget: AgentWidgetEntity, current_date: date) -> bool:
        if widget.daily_call_limit == -1:
            return True
        
        current_calls = self.widget_repo.get_daily_calls(widget.id, current_date)
        return current_calls < widget.daily_call_limit
    
    def generate_embed_code(self, widget: AgentWidgetEntity) -> str:
        return f"<script src='https://cdn.agentx.io/widget/{widget.public_id}.js'></script>"

class WorkspaceDomainService:
    def __init__(self, workspace_repo: WorkspaceRepository, agent_repo: AgentRepository, llm_config_repo: LLMModelConfigRepository):
        self.workspace_repo = workspace_repo
        self.agent_repo = agent_repo
        self.llm_config_repo = llm_config_repo
    
    def add_to_workspace(self, user_id: str, agent_id: str) -> WorkspaceAgentEntity:
        agent = self.agent_repo.find_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        existing = self.workspace_repo.find_by_user_and_agent(user_id, agent_id)
        if existing:
            raise ValueError("Agent already in workspace")
        
        workspace_agent = WorkspaceAgentEntity(user_id=user_id, agent_id=agent_id)
        return self.workspace_repo.add_agent(workspace_agent)
    
    def remove_from_workspace(self, user_id: str, agent_id: str) -> bool:
        return self.workspace_repo.remove_agent(user_id, agent_id)
    
    def update_model_config(self, user_id: str, agent_id: str, config: LLMModelConfig) -> LLMModelConfig:
        config.validate()
        return self.llm_config_repo.create_or_update(config, user_id, agent_id)
