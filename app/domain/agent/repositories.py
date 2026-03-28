from typing import List, Optional, Dict, Any
from datetime import date
from .entities import AgentEntity, AgentVersionEntity, AgentWidgetEntity, WorkspaceAgentEntity, LLMModelConfig, PublishStatusEnum

class AgentRepository:
    def create(self, agent: AgentEntity) -> AgentEntity:
        raise NotImplementedError
    
    def update(self, agent: AgentEntity) -> AgentEntity:
        raise NotImplementedError
    
    def delete(self, agent_id: str) -> bool:
        raise NotImplementedError
    
    def find_by_id(self, agent_id: str) -> Optional[AgentEntity]:
        raise NotImplementedError
    
    def find_by_user_id(self, user_id: str, filters: dict) -> List[AgentEntity]:
        raise NotImplementedError
    
    def find_by_name(self, user_id: str, name_pattern: str) -> List[AgentEntity]:
        raise NotImplementedError
    
    def find_published_agents(self) -> List[AgentEntity]:
        raise NotImplementedError
    
    def find_agent_names(self, ids: List[str]) -> Dict[str, str]:
        raise NotImplementedError

class VersionRepository:
    def create(self, version: AgentVersionEntity) -> AgentVersionEntity:
        raise NotImplementedError
    
    def find_by_agent_id(self, agent_id: str) -> List[AgentVersionEntity]:
        raise NotImplementedError
    
    def find_latest_version(self, agent_id: str) -> Optional[AgentVersionEntity]:
        raise NotImplementedError
    
    def find_by_version_number(self, agent_id: str, version_number: str) -> Optional[AgentVersionEntity]:
        raise NotImplementedError
    
    def find_published_version(self, agent_id: str) -> Optional[AgentVersionEntity]:
        raise NotImplementedError
    
    def count_reviewing_versions(self) -> int:
        raise NotImplementedError
    
    def find_versions_for_review(self, status: PublishStatusEnum) -> List[AgentVersionEntity]:
        raise NotImplementedError

class WidgetRepository:
    def create(self, widget: AgentWidgetEntity) -> AgentWidgetEntity:
        raise NotImplementedError
    
    def update(self, widget: AgentWidgetEntity) -> AgentWidgetEntity:
        raise NotImplementedError
    
    def delete(self, widget_id: str) -> bool:
        raise NotImplementedError
    
    def find_by_id(self, widget_id: str) -> Optional[AgentWidgetEntity]:
        raise NotImplementedError
    
    def find_by_agent_id(self, agent_id: str) -> List[AgentWidgetEntity]:
        raise NotImplementedError
    
    def find_by_public_id(self, public_id: str) -> Optional[AgentWidgetEntity]:
        raise NotImplementedError
    
    def increment_daily_calls(self, widget_id: str, date: date) -> int:
        raise NotImplementedError
    
    def get_daily_calls(self, widget_id: str, date: date) -> int:
        raise NotImplementedError

class WorkspaceRepository:
    def add_agent(self, workspace_agent: WorkspaceAgentEntity) -> WorkspaceAgentEntity:
        raise NotImplementedError
    
    def remove_agent(self, user_id: str, agent_id: str) -> bool:
        raise NotImplementedError
    
    def find_by_user_id(self, user_id: str) -> List[WorkspaceAgentEntity]:
        raise NotImplementedError
    
    def find_by_user_and_agent(self, user_id: str, agent_id: str) -> Optional[WorkspaceAgentEntity]:
        raise NotImplementedError

class LLMModelConfigRepository:
    def create_or_update(self, config: LLMModelConfig, user_id: str, agent_id: str) -> LLMModelConfig:
        raise NotImplementedError
    
    def find_by_user_and_agent(self, user_id: str, agent_id: str) -> Optional[LLMModelConfig]:
        raise NotImplementedError
