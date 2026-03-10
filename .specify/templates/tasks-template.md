---

description: "功能实现的任务列表模板"
---

# 任务：[功能名称]

**输入**: 来自 `/specs/[###-feature-name]/` 的设计文档
**前提条件**: plan.md（必需）、spec.md（用户故事必需）、research.md、data-model.md、contracts/

**测试**: 下面的示例包含测试任务。测试是可选的——仅在功能规范中明确要求时包含它们。

**组织**: 任务按用户故事分组，以便每个故事可以独立实现和测试。

## 格式：`[ID] [P?] [Story] 描述`

- **[P]**: 可以并行运行（不同的文件，无依赖）
- **[Story]**: 此任务属于哪个用户故事（例如，US1、US2、US3）
- 在描述中包含确切的文件路径

## 路径约定

- **单一项目**: `src/`、`tests/` 在仓库根目录
- **Web 应用**: `backend/src/`、`frontend/src/`
- **移动端**: `api/src/`、`ios/src/` 或 `android/src/`
- 下面显示的路径假设为单一项目——根据 plan.md 结构进行调整

<!-- 
  ============================================================================
  重要提示：下面的任务是仅用于说明的示例任务。
  
  /speckit.tasks 命令 MUST 用基于以下内容的实际任务替换这些：
  - 来自 spec.md 的用户故事（及其优先级 P1、P2、P3...）
  - 来自 plan.md 的功能要求
  - 来自 data-model.md 的实体
  - 来自 contracts/ 的端点
  
  任务 MUST 按用户故事组织，以便每个故事可以：
  - 独立实现
  - 独立测试
  - 作为 MVP 增量交付
  
  不要在生成的 tasks.md 文件中保留这些示例任务。
  ============================================================================
-->

## 阶段 1：设置（共享基础设施）

**目的**: 项目初始化和基本结构

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize [language] project with [framework] dependencies
- [ ] T003 [P] Configure linting and formatting tools

---

## 阶段 2：基础（阻塞性前提条件）

**目的**: 在任何用户故事可以实现之前 MUST 完成的核心基础设施

**⚠️ 关键**: 在此阶段完成之前，任何用户故事工作都无法开始

基础任务示例（根据你的项目调整）：

- [ ] T004 Setup database schema and migrations framework
- [ ] T005 [P] Implement authentication/authorization framework
- [ ] T006 [P] Setup API routing and middleware structure
- [ ] T007 Create base models/entities that all stories depend on
- [ ] T008 Configure error handling and logging infrastructure
- [ ] T009 Setup environment configuration management

**检查点**: 基础就绪——现在可以并行开始用户故事实现

---

## 阶段 3：用户故事 1 - [标题]（优先级：P1）🎯 MVP

**目标**: [简要描述这个故事交付的内容]

**独立测试**: [如何验证这个故事单独工作]

### 用户故事 1 的测试（可选——仅在请求测试时）⚠️

> **注意**: 首先编写这些测试，确保它们在实现之前失败**

- [ ] T010 [P] [US1] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T011 [P] [US1] Integration test for [user journey] in tests/integration/test_[name].py

### 用户故事 1 的实现

- [ ] T012 [P] [US1] Create [Entity1] model in src/models/[entity1].py
- [ ] T013 [P] [US1] Create [Entity2] model in src/models/[entity2].py
- [ ] T014 [US1] Implement [Service] in src/services/[service].py (depends on T012, T013)
- [ ] T015 [US1] Implement [endpoint/feature] in src/[location]/[file].py
- [ ] T016 [US1] Add validation and error handling
- [ ] T017 [US1] Add logging for user story 1 operations

**检查点**: 此时，用户故事 1 应该完全功能并可独立测试

---

## 阶段 4：用户故事 2 - [标题]（优先级：P2）

**目标**: [简要描述这个故事交付的内容]

**独立测试**: [如何验证这个故事单独工作]

### 用户故事 2 的测试（可选——仅在请求测试时）⚠️

- [ ] T018 [P] [US2] 契约测试，针对 [端点]，位于 tests/contract/test_[name].py
- [ ] T019 [P] [US2] 集成测试，针对 [用户旅程]，位于 tests/integration/test_[name].py

### 用户故事 2 的实现

- [ ] T020 [P] [US2] 在 src/models/[entity].py 中创建 [Entity] 模型
- [ ] T021 [US2] 在 src/services/[service].py 中实现 [Service]
- [ ] T022 [US2] 在 src/[location]/[file].py 中实现 [端点/功能]
- [ ] T023 [US2] 与用户故事 1 的组件集成（如果需要）

**检查点**: 此时，用户故事 1 和 2 都应该可以独立工作

---

## 阶段 5：用户故事 3 - [标题]（优先级：P3）

**目标**: [简要描述这个故事交付的内容]

**独立测试**: [如何验证这个故事单独工作]

### 用户故事 3 的测试（可选——仅在请求测试时）⚠️

- [ ] T024 [P] [US3] 契约测试，针对 [端点]，位于 tests/contract/test_[name].py
- [ ] T025 [P] [US3] 集成测试，针对 [用户旅程]，位于 tests/integration/test_[name].py

### 用户故事 3 的实现

- [ ] T026 [P] [US3] 在 src/models/[entity].py 中创建 [Entity] 模型
- [ ] T027 [US3] 在 src/services/[service].py 中实现 [Service]
- [ ] T028 [US3] 在 src/[location]/[file].py 中实现 [端点/功能]

**检查点**: 现在所有用户故事都应该可以独立工作

---

[根据需要添加更多用户故事阶段，遵循相同的模式]

---

## 阶段 N：完善与跨领域关注点

**目的**: 影响多个用户故事的改进

- [ ] TXXX [P] Documentation updates in docs/
- [ ] TXXX Code cleanup and refactoring
- [ ] TXXX Performance optimization across all stories
- [ ] TXXX [P] Additional unit tests (if requested) in tests/unit/
- [ ] TXXX Security hardening
- [ ] TXXX Run quickstart.md validation

---

## 依赖关系与执行顺序

### 阶段依赖关系

- **设置（阶段 1）**: 无依赖——可以立即开始
- **基础（阶段 2）**: 依赖于设置完成——阻塞所有用户故事
- **用户故事（阶段 3+）**: 都依赖于基础阶段完成
  - 然后用户故事可以并行进行（如果有人员）
  - 或者按优先级顺序依次进行（P1 → P2 → P3）
- **完善（最后阶段）**: 依赖于所有期望的用户故事完成

### 用户故事依赖关系

- **用户故事 1（P1）**: 基础阶段后开始（阶段 2）——对其他故事无依赖
- **用户故事 2（P2）**: 基础阶段后开始（阶段 2）——可以与 US1 集成但应可独立测试
- **用户故事 3（P3）**: 基础阶段后开始（阶段 2）——可以与 US1/US2 集成但应可独立测试

### 每个用户故事内部

- 测试（如果包含）MUST 在实现之前编写并失败
- 模型在服务之前
- 服务在端点之前
- 核心实现在集成之前
- 故事完成后再进入下一个优先级

### 并行机会

- 所有标记为 [P] 的设置任务可以并行运行
- 所有标记为 [P] 的基础任务可以并行运行（在阶段 2 内）
- 一旦基础阶段完成，所有用户故事可以并行开始（如果团队容量允许）
- 用户故事的所有标记为 [P] 的测试可以并行运行
- 故事内标记为 [P] 的模型可以并行运行
- 不同的用户故事可以由不同的团队成员并行工作

---

## 并行示例：用户故事 1

```bash
# 一起启动用户故事 1 的所有测试（如果请求测试）：
任务："[端点] 的契约测试，位于 tests/contract/test_[name].py"
任务："[用户旅程] 的集成测试，位于 tests/integration/test_[name].py"

# 一起启动用户故事 1 的所有模型：
任务："在 src/models/[entity1].py 中创建 [Entity1] 模型"
任务："在 src/models/[entity2].py 中创建 [Entity2] 模型"
```

---

## 实现策略

### 优先 MVP（仅用户故事 1）

1. 完成阶段 1：设置
2. 完成阶段 2：基础（关键——阻塞所有故事）
3. 完成阶段 3：用户故事 1
4. **停止并验证**: 独立测试用户故事 1
5. 如果准备好就部署/演示

### 增量交付

1. 完成设置 + 基础 → 基础就绪
2. 添加用户故事 1 → 独立测试 → 部署/演示（MVP！）
3. 添加用户故事 2 → 独立测试 → 部署/演示
4. 添加用户故事 3 → 独立测试 → 部署/演示
5. 每个故事增加价值而不破坏之前的故事

### 并行团队策略

有多个开发人员时：

1. 团队一起完成设置 + 基础
2. 基础完成后：
   - 开发者 A：用户故事 1
   - 开发者 B：用户故事 2
   - 开发者 C：用户故事 3
3. 故事独立完成并集成

---

## 注意事项

- [P] 任务 = 不同的文件，无依赖
- [Story] 标签将任务映射到特定用户故事以进行跟踪
- 每个用户故事应该可以独立完整和测试
- 在实现之前验证测试失败
- 每个任务或逻辑组后提交
- 在任何检查点停止以独立验证故事
- 避免：模糊的任务、相同文件冲突、破坏独立性的跨故事依赖
