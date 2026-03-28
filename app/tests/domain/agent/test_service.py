from app.domain.agent.services import AgentDomainService, VersionDomainService, WidgetDomainService, WorkspaceDomainService, CreateAgentCommand
from app.infrastructure.agent.repositories import InMemoryAgentRepository, InMemoryVersionRepository, InMemoryWidgetRepository, InMemoryWorkspaceRepository, InMemoryLLMModelConfigRepository

# 测试智能体领域服务
def test_agent_domain_service():
    # 初始化仓储
    agent_repo = InMemoryAgentRepository()
    version_repo = InMemoryVersionRepository()
    
    # 初始化领域服务
    agent_service = AgentDomainService(agent_repo, version_repo, None)
    
    # 测试创建智能体
    create_cmd = CreateAgentCommand(
        name="测试智能体",
        description="这是一个测试智能体",
        system_prompt="你是一个测试智能体",
        welcome_message="欢迎使用测试智能体"
    )
    agent = agent_service.create_agent("user_123", create_cmd)
    assert agent.name == "测试智能体"
    assert agent.description == "这是一个测试智能体"
    
    # 测试查询智能体
    found_agent = agent_repo.find_by_id(agent.id)
    assert found_agent is not None
    assert found_agent.id == agent.id
    
    # 测试更新智能体
    agent.name = "更新后的测试智能体"
    updated_agent = agent_repo.update(agent)
    assert updated_agent.name == "更新后的测试智能体"
    
    # 测试删除智能体
    delete_result = agent_service.delete_agent(agent.id)
    assert delete_result == True
    assert agent_repo.find_by_id(agent.id) is None

# 测试版本领域服务
def test_version_domain_service():
    # 初始化仓储
    agent_repo = InMemoryAgentRepository()
    version_repo = InMemoryVersionRepository()
    
    # 初始化领域服务
    agent_service = AgentDomainService(agent_repo, version_repo, None)
    version_service = VersionDomainService(version_repo, agent_repo)
    
    # 创建智能体
    create_cmd = CreateAgentCommand(name="测试智能体")
    agent = agent_service.create_agent("user_123", create_cmd)
    
    # 测试发布版本
    version = version_service.publish_new_version(agent.id, "初始版本")
    assert version.version_number == "1.0.0"
    assert version.agent_id == agent.id
    
    # 测试查询版本历史
    versions = version_repo.find_by_agent_id(agent.id)
    assert len(versions) == 1
    assert versions[0].id == version.id

# 测试 Widget 领域服务
def test_widget_domain_service():
    # 初始化仓储
    widget_repo = InMemoryWidgetRepository()
    
    # 初始化领域服务
    widget_service = WidgetDomainService(widget_repo)
    
    # 测试创建 Widget
    from app.domain.agent.services import CreateWidgetCommand
    from app.domain.agent.entities import WidgetTypeEnum
    
    create_cmd = CreateWidgetCommand(
        name="测试 Widget",
        widget_type=WidgetTypeEnum.AGENT,
        model_id="gpt-4",
        model_provider="openai"
    )
    widget = widget_service.create_widget("agent_123", create_cmd)
    assert widget.name == "测试 Widget"
    assert widget.agent_id == "agent_123"
    
    # 测试域名验证
    widget.allowed_domains = ["www.example.com", "*.test.com"]
    assert widget_service.validate_domain_access(widget, "www.example.com") == True
    assert widget_service.validate_domain_access(widget, "api.test.com") == True
    assert widget_service.validate_domain_access(widget, "www.other.com") == False

# 测试工作空间领域服务
def test_workspace_domain_service():
    # 初始化仓储
    workspace_repo = InMemoryWorkspaceRepository()
    agent_repo = InMemoryAgentRepository()
    llm_config_repo = InMemoryLLMModelConfigRepository()
    
    # 初始化领域服务
    workspace_service = WorkspaceDomainService(workspace_repo, agent_repo, llm_config_repo)
    agent_service = AgentDomainService(agent_repo, InMemoryVersionRepository(), None)
    
    # 创建智能体
    create_cmd = CreateAgentCommand(name="测试智能体")
    agent = agent_service.create_agent("user_123", create_cmd)
    
    # 测试添加到工作空间
    workspace_agent = workspace_service.add_to_workspace("user_123", agent.id)
    assert workspace_agent.user_id == "user_123"
    assert workspace_agent.agent_id == agent.id
    
    # 测试从工作空间移除
    remove_result = workspace_service.remove_from_workspace("user_123", agent.id)
    assert remove_result == True
