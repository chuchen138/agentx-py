from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid

class PublishStatusEnum(str, Enum):
    REVIEWING = "REVIEWING"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"
    REMOVED = "REMOVED"

class WidgetTypeEnum(str, Enum):
    AGENT = "AGENT"
    RAG = "RAG"

class TokenOverflowStrategyEnum(str, Enum):
    NONE = "NONE"
    SLIDING_WINDOW = "SLIDING_WINDOW"
    SUMMARY = "SUMMARY"

class AgentEntity:
    def __init__(self, user_id: str, name: str, description: Optional[str] = None, 
                 avatar_url: Optional[str] = None, system_prompt: Optional[str] = None, 
                 welcome_message: Optional[str] = None, tool_ids: Optional[List[str]] = None, 
                 knowledge_base_ids: Optional[List[str]] = None, 
                 tool_preset_params: Optional[Dict[str, Any]] = None, 
                 enabled: bool = True, support_multimodal: bool = False):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.name = name
        self.description = description
        self.avatar_url = avatar_url
        self.system_prompt = system_prompt
        self.welcome_message = welcome_message
        self.tool_ids = tool_ids or []
        self.knowledge_base_ids = knowledge_base_ids or []
        self.tool_preset_params = tool_preset_params or {}
        self.current_version_id = None
        self.enabled = enabled
        self.support_multimodal = support_multimodal
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_tool(self, tool_id: str):
        if tool_id not in self.tool_ids:
            self.tool_ids.append(tool_id)
            self.updated_at = datetime.now()
    
    def remove_tool(self, tool_id: str):
        if tool_id in self.tool_ids:
            self.tool_ids.remove(tool_id)
            self.updated_at = datetime.now()
    
    def add_knowledge_base(self, kb_id: str):
        if kb_id not in self.knowledge_base_ids:
            self.knowledge_base_ids.append(kb_id)
            self.updated_at = datetime.now()
    
    def remove_knowledge_base(self, kb_id: str):
        if kb_id in self.knowledge_base_ids:
            self.knowledge_base_ids.remove(kb_id)
            self.updated_at = datetime.now()
    
    def enable(self):
        self.enabled = True
        self.updated_at = datetime.now()
    
    def disable(self):
        self.enabled = False
        self.updated_at = datetime.now()
    
    def create_snapshot(self):
        return {
            "name": self.name,
            "system_prompt": self.system_prompt,
            "tool_ids": self.tool_ids.copy(),
            "knowledge_base_ids": self.knowledge_base_ids.copy()
        }

class AgentVersionEntity:
    def __init__(self, agent_id: str, version_number: str, agent_name_snapshot: str, 
                 system_prompt_snapshot: Optional[str] = None, tool_ids_snapshot: Optional[List[str]] = None, 
                 knowledge_base_ids_snapshot: Optional[List[str]] = None, change_log: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.agent_id = agent_id
        self.version_number = version_number
        self.agent_name_snapshot = agent_name_snapshot
        self.system_prompt_snapshot = system_prompt_snapshot
        self.tool_ids_snapshot = tool_ids_snapshot or []
        self.knowledge_base_ids_snapshot = knowledge_base_ids_snapshot or []
        self.change_log = change_log
        self.publish_status = PublishStatusEnum.REVIEWING
        self.review_rejection_reason = None
        self.reviewer_id = None
        self.published_at = None
        self.created_at = datetime.now()

class AgentWidgetEntity:
    def __init__(self, agent_id: str, name: str, widget_type: WidgetTypeEnum, 
                 model_id: str, model_provider: str, allowed_domains: Optional[List[str]] = None, 
                 daily_call_limit: int = -1, enabled: bool = True):
        self.id = str(uuid.uuid4())
        self.agent_id = agent_id
        self.public_id = ''.join(str(uuid.uuid4()).split('-')[:4])
        self.name = name
        self.widget_type = widget_type
        self.model_id = model_id
        self.model_provider = model_provider
        self.allowed_domains = allowed_domains or []
        self.daily_call_limit = daily_call_limit
        self.enabled = enabled
        self.embed_code = f"<script src='https://cdn.agentx.io/widget/{self.public_id}.js'></script>"
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

class WorkspaceAgentEntity:
    def __init__(self, user_id: str, agent_id: str, custom_name: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.agent_id = agent_id
        self.custom_name = custom_name
        self.added_at = datetime.now()

class LLMModelConfig:
    def __init__(self, model_id: str, provider: str, temperature: float = 0.7, 
                 top_p: float = 0.7, top_k: int = 50, max_tokens: Optional[int] = None, 
                 strategy_type: TokenOverflowStrategyEnum = TokenOverflowStrategyEnum.NONE, 
                 reserve_ratio: Optional[float] = None, summary_threshold: Optional[int] = None):
        self.model_id = model_id
        self.provider = provider
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_tokens = max_tokens
        self.strategy_type = strategy_type
        self.reserve_ratio = reserve_ratio
        self.summary_threshold = summary_threshold
    
    def validate(self):
        if not 0 <= self.temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        if not 0 <= self.top_p <= 1:
            raise ValueError("Top P must be between 0 and 1")
        if self.strategy_type == TokenOverflowStrategyEnum.SLIDING_WINDOW and self.reserve_ratio is None:
            raise ValueError("Reserve ratio is required for SLIDING_WINDOW strategy")
        if self.strategy_type == TokenOverflowStrategyEnum.SUMMARY and self.summary_threshold is None:
            raise ValueError("Summary threshold is required for SUMMARY strategy")
        return True
