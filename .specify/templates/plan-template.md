# 实现计划：[功能名称]

**分支**: `[###-feature-name]` | **日期**: [日期] | **规范**: [链接]
**输入**: 来自 `/specs/[###-feature-name]/spec.md` 的功能规范

**注意**: 此文件由 `/speckit.plan` 命令填充。执行流程见 `.specify/templates/plan-template.md`。

## 摘要

[从功能规范中提取：主要需求 + 来自研究的技术方法]

## 技术上下文

<!--
  必需操作：用本项目的技术细节替换本节的内容。
  这里的结构以建议的方式呈现，以指导迭代过程。
-->

**语言/版本**: [例如，Python 3.11、Swift 5.9、Rust 1.75 或 NEEDS CLARIFICATION]  
**主要依赖**: [例如，FastAPI、UIKit、LLVM 或 NEEDS CLARIFICATION]  
**存储**: [如果适用，例如，PostgreSQL、CoreData、文件或 N/A]  
**测试**: [例如，pytest、XCTest、cargo test 或 NEEDS CLARIFICATION]  
**目标平台**: [例如，Linux 服务器、iOS 15+、WASM 或 NEEDS CLARIFICATION]
**项目类型**: [例如，库/cli/web 服务/移动应用/编译器/桌面应用或 NEEDS CLARIFICATION]  
**性能目标**: [领域特定，例如，1000 req/s、10k lines/sec、60 fps 或 NEEDS CLARIFICATION]  
**约束**: [领域特定，例如，<200ms p95、<100MB 内存、离线可用或 NEEDS CLARIFICATION]  
**规模/范围**: [领域特定，例如，10k 用户、1M LOC、50 个界面或 NEEDS CLARIFICATION]

## 章程检查

*门禁：必须在阶段 0 研究之前通过。在阶段 1 设计后重新检查。*

[根据章程文件确定的门禁]

## 项目结构

### 文档（本功能）

```text
specs/[###-feature]/
├── plan.md              # 本文件（/speckit.plan 命令输出）
├── research.md          # 阶段 0 输出（/speckit.plan 命令）
├── data-model.md        # 阶段 1 输出（/speckit.plan 命令）
├── quickstart.md        # 阶段 1 输出（/speckit.plan 命令）
├── contracts/           # 阶段 1 输出（/speckit.plan 命令）
└── tasks.md             # 阶段 2 输出（/speckit.tasks 命令 - 不由 /speckit.plan 创建）
```

### 源代码（仓库根目录）
<!--
  必需操作：用具体的布局替换下面的占位符树。
  删除未使用的选项并用真实路径扩展所选结构
  （例如，apps/admin、packages/something）。交付的计划不得
  包含选项标签。
-->

```text
# [如果未使用请删除] 选项 1：单一项目（默认）
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [如果未使用请删除] 选项 2：Web 应用（检测到 "frontend" + "backend" 时）
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [如果未使用请删除] 选项 3：移动端 + API（检测到 "iOS/Android" 时）
api/
└── [与上面的 backend 相同]

ios/ 或 android/
└── [平台特定结构：功能模块、UI 流程、平台测试]
```

**结构决策**: [记录所选结构并引用上面捕获的真实目录]

## 复杂性跟踪

> **仅在章程检查有违规且必须证明合理性时填写**

| 违规 | 为什么需要 | 拒绝的更简单替代方案因为 |
|-----------|------------|-------------------------------------|
| [例如，第 4 个项目] | [当前需求] | [为什么 3 个项目不够] |
| [例如，Repository 模式] | [具体问题] | [为什么直接数据库访问不够] |
