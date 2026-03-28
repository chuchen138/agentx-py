from typing import List, Optional, Dict, Any
from datetime import date, datetime
from app.domain.agent.entities import AgentEntity, AgentVersionEntity, AgentWidgetEntity, WorkspaceAgentEntity, LLMModelConfig, PublishStatusEnum
from app.domain.agent.repositories import AgentRepository, VersionRepository, WidgetRepository, WorkspaceRepository, LLMModelConfigRepository

class InMemoryAgentRepository(AgentRepository):
    def __init__(self):
        self.agents = {}
    
    def create(self, agent: AgentEntity) -> AgentEntity:
        self.agents[agent.id] = agent
        return agent
    
    def update(self, agent: AgentEntity) -> AgentEntity:
        if agent.id in self.agents:
            self.agents[agent.id] = agent
        return agent
    
    def delete(self, agent_id: str) -> bool:
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False
    
    def find_by_id(self, agent_id: str) -> Optional[AgentEntity]:
        return self.agents.get(agent_id)
    
    def find_by_user_id(self, user_id: str, filters: dict) -> List[AgentEntity]:
        agents = [agent for agent in self.agents.values() if agent.user_id == user_id]
        if filters.get('name'):
            name_pattern = filters['name'].lower()
            agents = [agent for agent in agents if name_pattern in agent.name.lower()]
        if filters.get('enabled') is not None:
            agents = [agent for agent in agents if agent.enabled == filters['enabled']]
        return agents
    
    def find_by_name(self, user_id: str, name_pattern: str) -> List[AgentEntity]:
        name_pattern = name_pattern.lower()
        return [agent for agent in self.agents.values() 
                if agent.user_id == user_id and name_pattern in agent.name.lower()]
    
    def find_published_agents(self) -> List[AgentEntity]:
        return [agent for agent in self.agents.values() if agent.enabled]
    
    def find_agent_names(self, ids: List[str]) -> Dict[str, str]:
        return {id: self.agents[id].name for id in ids if id in self.agents}

class InMemoryVersionRepository(VersionRepository):
    def __init__(self):
        self.versions = {}
        self.agent_versions = {}
    
    def create(self, version: AgentVersionEntity) -> AgentVersionEntity:
        self.versions[version.id] = version
        if version.agent_id not in self.agent_versions:
            self.agent_versions[version.agent_id] = []
        self.agent_versions[version.agent_id].append(version)
        return version
    
    def find_by_agent_id(self, agent_id: str) -> List[AgentVersionEntity]:
        return self.agent_versions.get(agent_id, [])
    
    def find_latest_version(self, agent_id: str) -> Optional[AgentVersionEntity]:
        versions = self.agent_versions.get(agent_id, [])
        if not versions:
            return None
        return max(versions, key=lambda v: v.created_at)
    
    def find_by_version_number(self, agent_id: str, version_number: str) -> Optional[AgentVersionEntity]:
        versions = self.agent_versions.get(agent_id, [])
        for version in versions:
            if version.version_number == version_number:
                return version
        return None
    
    def find_published_version(self, agent_id: str) -> Optional[AgentVersionEntity]:
        versions = self.agent_versions.get(agent_id, [])
        for version in versions:
            if version.publish_status == PublishStatusEnum.PUBLISHED:
                return version
        return None
    
    def count_reviewing_versions(self) -> int:
        return sum(1 for version in self.versions.values() 
                  if version.publish_status == PublishStatusEnum.REVIEWING)
    
    def find_versions_for_review(self, status: PublishStatusEnum) -> List[AgentVersionEntity]:
        return [version for version in self.versions.values() 
                if version.publish_status == status]

class InMemoryWidgetRepository(WidgetRepository):
    def __init__(self):
        self.widgets = {}
        self.agent_widgets = {}
        self.public_id_index = {}
        self.daily_calls = {}
    
    def create(self, widget: AgentWidgetEntity) -> AgentWidgetEntity:
        self.widgets[widget.id] = widget
        if widget.agent_id not in self.agent_widgets:
            self.agent_widgets[widget.agent_id] = []
        self.agent_widgets[widget.agent_id].append(widget)
        self.public_id_index[widget.public_id] = widget.id
        return widget
    
    def update(self, widget: AgentWidgetEntity) -> AgentWidgetEntity:
        if widget.id in self.widgets:
            self.widgets[widget.id] = widget
        return widget
    
    def delete(self, widget_id: str) -> bool:
        if widget_id in self.widgets:
            widget = self.widgets[widget_id]
            del self.widgets[widget_id]
            if widget.agent_id in self.agent_widgets:
                self.agent_widgets[widget.agent_id] = [w for w in self.agent_widgets[widget.agent_id] if w.id != widget_id]
            if widget.public_id in self.public_id_index:
                del self.public_id_index[widget.public_id]
            return True
        return False
    
    def find_by_id(self, widget_id: str) -> Optional[AgentWidgetEntity]:
        return self.widgets.get(widget_id)
    
    def find_by_agent_id(self, agent_id: str) -> List[AgentWidgetEntity]:
        return self.agent_widgets.get(agent_id, [])
    
    def find_by_public_id(self, public_id: str) -> Optional[AgentWidgetEntity]:
        widget_id = self.public_id_index.get(public_id)
        return self.widgets.get(widget_id)
    
    def increment_daily_calls(self, widget_id: str, date: date) -> int:
        key = f"{widget_id}_{date.isoformat()}"
        if key not in self.daily_calls:
            self.daily_calls[key] = 0
        self.daily_calls[key] += 1
        return self.daily_calls[key]
    
    def get_daily_calls(self, widget_id: str, date: date) -> int:
        key = f"{widget_id}_{date.isoformat()}"
        return self.daily_calls.get(key, 0)

class InMemoryWorkspaceRepository(WorkspaceRepository):
    def __init__(self):
        self.workspace_agents = {}
        self.user_agents = {}
    
    def add_agent(self, workspace_agent: WorkspaceAgentEntity) -> WorkspaceAgentEntity:
        self.workspace_agents[workspace_agent.id] = workspace_agent
        if workspace_agent.user_id not in self.user_agents:
            self.user_agents[workspace_agent.user_id] = {}
        self.user_agents[workspace_agent.user_id][workspace_agent.agent_id] = workspace_agent.id
        return workspace_agent
    
    def remove_agent(self, user_id: str, agent_id: str) -> bool:
        if user_id in self.user_agents and agent_id in self.user_agents[user_id]:
            workspace_agent_id = self.user_agents[user_id][agent_id]
            del self.workspace_agents[workspace_agent_id]
            del self.user_agents[user_id][agent_id]
            return True
        return False
    
    def find_by_user_id(self, user_id: str) -> List[WorkspaceAgentEntity]:
        if user_id not in self.user_agents:
            return []
        return [self.workspace_agents[wid] for wid in self.user_agents[user_id].values()]
    
    def find_by_user_and_agent(self, user_id: str, agent_id: str) -> Optional[WorkspaceAgentEntity]:
        if user_id in self.user_agents and agent_id in self.user_agents[user_id]:
            workspace_agent_id = self.user_agents[user_id][agent_id]
            return self.workspace_agents.get(workspace_agent_id)
        return None

class InMemoryLLMModelConfigRepository(LLMModelConfigRepository):
    def __init__(self):
        self.configs = {}
    
    def create_or_update(self, config: LLMModelConfig, user_id: str, agent_id: str) -> LLMModelConfig:
        key = f"{user_id}_{agent_id}"
        self.configs[key] = config
        return config
    
    def find_by_user_and_agent(self, user_id: str, agent_id: str) -> Optional[LLMModelConfig]:
        key = f"{user_id}_{agent_id}"
        return self.configs.get(key)
