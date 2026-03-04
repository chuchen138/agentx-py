# OpenSpec 配置说明

本目录包含 AgentX 项目的 OpenSpec 配置和变更管理。

## 目录结构

```
openspec/
├── config.yaml          # OpenSpec 全局配置
├── specs/               # 规范文件目录
│   └── <capability>/    # 每个能力一个目录
│       └── spec.md      # 能力规范文档
├── changes/             # 变更提案目录
│   ├── <change-name>/   # 变更工作区
│   │   ├── .openspec.yaml  # 变更配置
│   │   ├── proposal.md     # 变更提案 (what & why)
│   │   ├── design.md       # 设计方案 (how)
│   │   ├── tasks.md        # 实现任务列表
│   │   └── specs/          # 增量规范 (可选)
│   │       └── <capability>/
│   │           └── spec.md
│   └── archive/         # 已归档的变更
│       └── YYYY-MM-DD-<change-name>/
└── README.md            # 本文件
```

## 快速开始

### 1. 创建变更提案

使用 `/openspec-propose` 命令快速创建变更提案:

```
/openspec-propose <change-name>
```

或直接描述你想构建的内容。

### 2. 实现变更

使用 `/openspec-apply` 命令开始实现:

```
/openspec-apply <change-name>
```

### 3. 探索模式

使用 `/openspec-explore` 进行探索和思考:

```
/openspec-explore [change-name]
```

### 4. 归档变更

完成后使用 `/openspec-archive` 归档:

```
/openspec-archive <change-name>
```

## 配置说明

### config.yaml

- **schema**: 使用的工作流程 (spec-driven)
- **context**: 项目背景信息，包括技术栈、架构、开发实践
- **rules**: 每个伪影的规则约束

## 工作流程

### Spec-Driven 工作流程

1. **Proposal** (proposal.md)
   - 问题描述
   - 解决方案概述
   - 目标和非目标
   - 成功标准

2. **Design** (design.md)
   - 架构设计
   - API 合同
   - 数据库模式变更
   - 安全考虑

3. **Tasks** (tasks.md)
   - 实现任务列表
   - 任务依赖关系
   - 验收标准

4. **Implementation**
   - 按任务逐步实现
   - 更新任务状态
   - 代码审查

5. **Archive**
   - 归档变更
   - 同步增量规范到主规范

## 最佳实践

- 保持变更小而专注
- 在实现前充分思考和设计
- 使用探索模式厘清复杂问题
- 及时归档已完成的变更
- 维护规范的时效性

## 常用命令

```bash
# 列出所有变更
openspec list

# 查看变更状态
openspec status --change <name>

# 获取伪影创建指令
openspec instructions <artifact> --change <name>

# 应用变更任务
openspec instructions apply --change <name>

# 归档变更
openspec archive <name>
```

## 匿名统计

OpenSpec 收集匿名使用统计以改进产品。如需禁用:

```bash
export OPENSPEC_TELEMETRY=0
```
