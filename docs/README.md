# Docs

This directory contains design notes, system documentation, and a Chinese project explanation. The files here are not runtime code; they are reference documents that explain the architecture, agent behavior, and engineering decisions behind FulfillCrew.

## Files

### `system_design.md`

A concise system architecture overview. It shows the four-layer flow:

```text
React Frontend -> FastAPI Backend -> Multi-Agent System -> Demand and Fraud ML Modules
```

It also notes that the first implementation keeps data in memory, with the next natural upgrade being SQLite or PostgreSQL persistence.

### `agent_design.md`

Describes the simplified Contract Net Protocol used by the multi-agent order workflow. It lists the seven-step pipeline from Order Agent receiving the checkout request to Inventory Agent reserving stock after the winning warehouse is selected.

### `neural_network_models.md`

Documents the ML model layer: demand prediction (regression), fraud detection (binary classification), and product category classification (supervised text classification). It maps each module to its ELEC320 course topic and describes the intended training-mode vs online-mode split.

### `deployment.md`

Docker and deployment guidance. It references the `Dockerfile` and `docker-compose.yml` at the repository root and explains how the backend and frontend can be containerised and deployed to a cloud VM.

### `course_mapping.md`

Explains how the three university modules (COMP315 Cloud Computing, COMP310 Multi-Agent Systems, ELEC320 Neural Networks) are mapped into the running system. This document is the basis for the `/agents/course-map` API endpoint and the course intelligence dashboard on the frontend.

### `中文项目介绍.md`

A detailed Chinese-language project introduction for students and reviewers. It covers the project origin, the engineering decisions, the agent workflow, the ML model layer, and suggestions for how to extend the project. It is intended for Chinese-speaking GitHub visitors and classroom presentations.

## How to Use This Directory

- **For reviewers:** Read `system_design.md` and `agent_design.md` first to understand the architecture, then `course_mapping.md` to see how coursework is applied.
- **For students:** Read `中文项目介绍.md` and `course_mapping.md` to understand the project philosophy, then check the code to see how each concept is implemented.
- **For deployers:** Read `deployment.md` and the repository root `docker-compose.yml` to understand the containerisation strategy.

## Contribution Notes

When you add a major new feature (e.g., a new agent, a real trained ML model, a database layer), add a short design note here that explains the decision and the trade-offs. This keeps the repository readable and production-minded.

---

# 文档（Docs）

本目录包含设计笔记、系统文档和中文项目说明。这些文件不是运行时代码，而是解释 FulfillCrew 架构、智能体行为和工程决策的参考文档。

## 文件说明

### `system_design.md`

简洁的系统架构概览。展示四层数据流：

```text
React 前端 -> FastAPI 后端 -> 多智能体系统 -> 需求预测与欺诈检测 ML 模块
```

同时说明第一版使用内存级数据存储，下一个自然升级是使用 SQLite 或 PostgreSQL 持久化。

### `agent_design.md`

描述多智能体订单工作流使用的简化版 Contract Net Protocol（合同网协议）。列出从 Order Agent 接收结账请求到 Inventory Agent 为中标仓库预留库存的七步流水线。

### `neural_network_models.md`

记录 ML 模型层：需求预测（回归）、欺诈检测（二分类）、商品分类（监督文本分类）。将每个模块映射到对应的 ELEC320 课程主题，并描述预期的训练模式与在线模式划分。

### `deployment.md`

Docker 与部署指南。引用仓库根目录下的 `Dockerfile` 和 `docker-compose.yml`，解释后端和前端如何容器化并部署到云端虚拟机。

### `course_mapping.md`

解释三门大学课程（COMP315 云计算、COMP310 多智能体系统、ELEC320 神经网络）如何映射到运行中的系统。本文档是 `/agents/course-map` API 端点和前端课程智能仪表盘的依据。

### `中文项目介绍.md`

面向学生和评审者的详细中文项目介绍。涵盖项目起源、工程决策、智能体工作流、ML 模型层，以及扩展建议。面向中文 GitHub 访问者和课堂展示。

## 如何使用本目录

- **评审者：** 先阅读 `system_design.md` 和 `agent_design.md` 了解架构，再阅读 `course_mapping.md` 了解课程作业如何落地。
- **学生：** 先阅读 `中文项目介绍.md` 和 `course_mapping.md` 了解项目理念，再对照代码查看每个概念的具体实现。
- **部署者：** 阅读 `deployment.md` 和仓库根目录的 `docker-compose.yml`，了解容器化策略。

## 贡献说明

当你添加重大新功能（如新智能体、真实训练后的 ML 模型、数据库层）时，请在此处添加一份简短的设计笔记，说明决策原因和权衡。这能保持仓库的可读性和架构复盘友好性。
