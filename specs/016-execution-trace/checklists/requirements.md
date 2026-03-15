## 实施
- [ ] 1.1 创建执行追踪实体和数据模型
     【目标对象】`app/domain/trace/model/`
     【修改目的】定义执行追踪相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】`AgentX/domain/trace/model/AgentExecutionSummaryEntity.java`, `AgentX/domain/trace/model/AgentExecutionDetailEntity.java`
     【修改内容】
        - 创建 AgentExecutionSummary 模型（agent_execution_summary 表）
        - 定义字段：id, user_id, session_id, agent_id, execution_start_time, execution_end_time, total_execution_time, total_input_tokens, total_output_tokens, total_tokens, tool_call_count, total_tool_execution_time, status, created_at
        - 创建 AgentExecutionDetail 模型（agent_execution_details 表）
        - 定义字段：id, summary_id, user_id, agent_id, step_name, step_type, start_time, end_time, duration, input_data, output_data, error_message, created_at
        - 实现 Pydantic Schema（AgentExecutionSummaryDTO, AgentExecutionDetailDTO, ExecutionTraceDTO, QueryExecutionHistoryRequest, AgentTraceListRequest, SessionTraceListRequest）

- [ ] 1.2 实现执行追踪仓储模式
     【目标对象】`app/domain/trace/repository.py`
     【修改目的】定义执行追踪数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 AgentExecutionSummaryRepository 接口
        - 定义 AgentExecutionDetailRepository 接口
        - 实现 SQLAlchemy AgentExecutionSummaryRepository
        - 实现 SQLAlchemy AgentExecutionDetailRepository
        - 实现 CRUD 操作（创建、查询）
        - 实现按用户ID查询方法（getByUserId, getPageByUserId）
        - 实现按会话ID查询方法（getBySessionId）
        - 实现按时间范围查询方法（getByTimeRange）
        - 实现分页查询方法
        - 实现统计查询方法

- [ ] 1.3 实现执行追踪领域服务
     【目标对象】`app/domain/trace/service.py`
     【修改目的】封装执行追踪相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】AgentExecutionSummaryRepository, AgentExecutionDetailRepository
     【修改内容】
        - 实现执行汇总记录创建逻辑
        - 实现执行详情记录创建逻辑
        - 实现执行查询业务逻辑
        - 实现执行统计业务逻辑
        - 实现执行数据聚合逻辑

- [ ] 1.4 实现追踪数据收集器
     【目标对象】`app/domain/trace/collector/`
     【修改目的】实现执行数据实时收集
     【修改方式】实现收集器模式 + AOP 装饰器
     【相关依赖】AgentExecutionSummaryRepository, AgentExecutionDetailRepository, asyncio.Queue
     【修改内容】
        - 创建 TraceCollector
        - **埋点位置**：
           - LLM 调用前后：使用装饰器包装 model_chat() 方法
           - 工具调用 wrapper：在 tool_executor 中植入埋点
           - Agent 执行开始/结束：在 conversation_manager 中植入埋点
        - **异步上报机制**：
           - 使用 asyncio.Queue 作为缓冲队列（容量：10000）
           - 后台消费者异步处理（asyncio.create_task)
           - 批量持久化：每 100 条或每 5 秒批量写入一次
           - 失败重试：指数退避重试（最多 3 次）
        - 实现执行上下文记录
        - 实现工具调用记录
        - 实现 LLM 调用记录
        - 实现执行错误记录
        - 实现执行时间统计
        - **采样逻辑**：
           - 按 Trace ID 哈希计算是否采样
           - 错误/失败请求强制全量采集
           - VIP 用户白名单全量采集

- [ ] 1.5 实现执行追踪应用服务层
     【目标对象】`app/application/trace/`
     【修改目的】编排执行追踪相关的用例
     【修改方式】实现应用服务
     【相关依赖】AgentExecutionTraceDomainService, AgentDomainService, SessionDomainService
     【修改内容】
        - 实现 AgentExecutionTraceAppService（执行追踪管理）
        - 实现获取执行链路方法（getExecutionTrace）
        - 实现获取用户执行历史方法（getUserExecutionHistory）
        - 实现获取会话执行历史方法（getSessionExecutionHistory）
        - 实现按时间范围查询方法（getUserExecutionsByTimeRange）
        - 实现执行统计方法（getExecutionStatistics, getSessionStatistics）

- [ ] 1.6 实现执行追踪转换器
     【目标对象】`app/application/trace/`
     【修改目的】实现实体与 DTO 之间的转换
     【修改方式】实现 Assembler 模式
     【相关依赖】AgentExecutionSummary 模型, AgentExecutionDetail 模型, ExecutionTraceDTO
     【修改内容】
        - 创建 AgentExecutionTraceAssembler
        - 实现 toSummaryDTO 方法（从汇总实体转换为 DTO）
        - 实现 toDetailDTO 方法（从详情实体转换为 DTO）
        - 实现 toSummaryDTOs 方法（批量转换）
        - 实现 toExecutionTraceDTO 方法（聚合汇总和详情）

- [ ] 1.7 创建 API 路由（FastAPI）
     【目标对象】`app/api/v1/trace/`
     【修改目的】暴露执行追踪相关的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】AgentExecutionTraceAppService
     【修改内容】
        - `GET /api/v1/traces/{traceId}` - 获取执行链路详情
        - `GET /api/v1/traces/user` - 获取用户执行历史（分页）
        - `GET /api/v1/traces/session/{sessionId}` - 获取会话执行历史
        - `GET /api/v1/traces/timerange` - 按时间范围查询执行记录
        - `GET /api/v1/traces/statistics` - 获取执行统计信息
        - `GET /api/v1/traces/session-statistics` - 获取会话执行统计

- [ ] 1.8 实现执行追踪事件监听器
     【目标对象】`app/application/trace/listener/`
     【修改目的】处理执行追踪相关事件
     【修改方式】实现事件监听器
     【相关依赖】TraceCollector
     【修改内容】
        - 创建 TraceEventListener
        - 实现 Agent 执行开始事件处理
        - 实现 Agent 执行结束事件处理
        - 实现工具调用事件处理
        - 实现 LLM 调用事件处理
        - 集成 TraceCollector 记录执行数据

- [ ] 1.9 实现执行统计服务
     【目标对象】`app/application/trace/`
     【修改目的】提供执行统计功能
     【修改方式】实现统计服务 + 物化视图
     【相关依赖】AgentExecutionSummaryRepository, Redis
     【修改内容】
        - **聚合方式**：
           - 实时聚合：使用 SQLAlchemy 聚合查询（COUNT, AVG, SUM）
           - 定时聚合：每小时计算物化视图（PostgreSQL Materialized View）
           - ClickHouse 聚合：长期方案使用 ClickHouse 的 SummingMergeTree
        - 实现按用户统计执行次数和平均耗时
        - 实现按会话统计执行次数和平均耗时
        - **按时间维度统计 Token 消耗**：
           - 日级聚合：每天凌晨计算前一天的统计数据
           - 周级聚合：每周一计算上一周的统计数据
           - 月级聚合：每月 1 号计算上个月的统计数据
        - 实现工具调用次数统计
        - 实现执行成功率统计
        - **降级统计**：
           - 按降级原因分组统计
           - 按模型端点统计降级频率
           - 降级持续时间计算
        - 实现统计报表生成
        - **导出支持**：CSV、Excel 格式导出

- [ ] 1.10 编写单元测试
     【目标对象】`tests/test_trace_service.py`
     【修改目的】确保执行追踪功能正确性
     【修改方式】使用 pytest
     【相关依赖】AgentExecutionTraceAppService
     【修改内容】
        - 测试执行汇总记录创建
        - 测试执行详情记录创建
        - 测试执行查询
        - 测试按用户查询
        - 测试按会话查询
        - 测试按时间范围查询
        - 测试执行统计
        - 测试追踪数据收集

- [ ] 1.11 编写集成测试
     【目标对象】`tests/integration/test_trace_api.py`
     【修改目的】确保执行追踪 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, AgentExecutionTraceAppService
     【修改内容】
        - 测试执行链路详情 API
        - 测试用户执行历史 API
        - 测试会话执行历史 API
        - 测试按时间范围查询 API
        - 测试执行统计 API
        - 测试会话统计 API
        - 测试分页查询 API

- [ ] 1.12 实现执行追踪缓存策略
     【目标对象】`app/infrastructure/cache/`
     【修改目的】提高执行追踪查询性能
     【修改方式】使用 Redis 缓存 + 分层缓存
     【相关依赖】Redis
     【修改内容】
        - **分层缓存策略**：
           - L1 缓存：内存缓存（最近 100 条活跃会话）
           - L2 缓存：Redis 缓存（最近 24 小时数据）
           - L3 存储：PostgreSQL（全量数据）
        - 实现执行记录缓存装饰器
        - 实现统计信息缓存
        - **缓存过期和刷新策略**：
           - 热点数据：5 分钟过期
           - 统计数据：1 小时过期
           - 写入时主动失效
        - 实现缓存穿透保护（布隆过滤器）
        - **采样数据缓存**：
           - 开发环境：不缓存（实时查询）
           - 生产环境：强制缓存

- [ ] 1.13 实现批量持久化和数据压缩
     【目标对象】`app/infrastructure/trace/`
     【修改目的】提高写入性能，降低存储成本
     【修改方式】批量写入 + 数据压缩
     【相关依赖】SQLAlchemy, gzip
     【修改内容】
        - **批量持久化**：
           - 批量大小：100 条或每 5 秒
           - 使用 SQLAlchemy bulk_insert_mappings
           - 失败重试：指数退避（1s, 2s, 4s）
           - 死信队列：重试失败后进入 DLQ
        - **数据压缩**：
           - 工具调用参数和响应 gzip 压缩
           - 长文本输出压缩（>1KB）
           - 压缩率监控（目标 60%-80%）
        - **截断策略**：
           - 单字段超过 50KB 自动截断
           - 标记 is_truncated=True
           - 记录原始长度

- [ ] 1.14 实现安全过滤和权限控制
     【目标对象】`app/api/v1/trace/`, `app/domain/trace/repository.py`
     【修改目的】确保数据访问安全
     【修改方式】行级安全 + 查询过滤
     【相关依赖】FastAPI Depends, SQLAlchemy
     【修改内容】
        - **数据库行级安全（RLS）**：
           - PostgreSQL RLS 策略：`WHERE user_id = current_user_id`
           - 管理员例外：`OR is_admin = true`
        - **查询时强制过滤**：
           - 所有查询自动注入 user_id 条件
           - 防止越权查询（ID 遍历攻击）
        - **审计日志记录**：
           - 记录查询者 ID、查询目标用户 ID、查询时间
           - 记录查询条件和返回结果数量
           - 异常访问检测（频繁跨用户查询）
        - **敏感字段脱敏**：
           - API 响应层统一脱敏处理
           - 脱敏规则可配置化

--- [ ] 1.13 实现执行链路可视化数据支持
     【目标对象】`app/application/trace/`
     【修改目的】为执行链路可视化提供数据支持
     【修改方式】实现可视化数据服务
     【相关依赖】AgentExecutionDetailRepository, Redis
     【修改内容】
        - **前端数据格式**：
           - Tree JSON：用于展示执行步骤的层级关系
           - Timeline JSON：用于时间线展示
           - Graph JSON：用于调用链图谱
        - **实现执行步骤层级关系构建**：
           - 父子步骤关系映射（parent_step_id）
           - 步骤深度计算（depth_level）
           - 分支路径标识（用于并行工具调用）
        - **实现执行时间线数据生成**：
           - 绝对时间戳序列
           - 相对耗时（相对于执行开始时间）
           - 关键事件标记（模型调用、工具调用、错误发生）
        - **实现工具调用链路数据生成**：
           - 工具调用依赖图
           - 工具调用耗时对比柱状图数据
           - 工具调用成功率饼图数据
        - **实现 LLM 调用链路数据生成**：
           - Token 消耗趋势图数据
           - 模型响应时间折线图数据
           - 模型成本分布饼图数据
        - **实现性能热点分析数据生成**：
           - 慢步骤识别（超过 P95 耗时）
           - 资源消耗 TOP10 步骤
           - 瓶颈步骤建议优化点
