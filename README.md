# 汽车运煤智能监督与风险预警系统

[English](#english) | [中文](#中文)

---

## 中文

### 项目简介

基于港口—入厂数据比对的汽车运煤智能监督与风险预警系统。聚焦**重量、时间、铅封**三大核心指标，构建燃煤汽运全流程监督体系，精准识别运输舞弊隐患。

### 核心功能

- **重量异常检测** - 亏吨/盈吨智能识别，支持固定阈值 + 动态阈值双重检测
- **时间异常检测** - 运输超时、中途停留异常自动预警
- **铅封验证** - 出港/进厂铅封二维码比对，防篡改
- **分级预警** - 一般预警(黄灯) / 严重预警(红灯) 分级管控
- **风险仪表盘** - 实时监控、趋势分析、高风险车辆排名
- **闭环管理** - 预警→确认→处理→归档 全流程可追溯

### 技术栈

| 层级 | 技术选型 |
|------|---------|
| 后端框架 | FastAPI + SQLAlchemy 2.0 + Pydantic v2 |
| 前端框架 | React 18 + TypeScript + Ant Design 5 |
| 数据可视化 | ECharts |
| 数据分析 | Pandas + NumPy + Scikit-learn |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |
| 容器化 | Docker Compose |

### 快速开始

```bash
# 克隆项目
git clone https://github.com/woshiniba-debug/coal-transport-monitor.git
cd coal-transport-monitor

# 启动后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 启动前端 (新终端)
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 查看前端界面
访问 http://localhost:8000/docs 查看API文档

### 风险预警规则

| 类型 | 一般预警 | 严重预警 |
|------|---------|---------|
| 重量 | 盈吨 > 3‰ | 亏吨 > 3‰ |
| 时间 | 超时 30-60 分钟 | 超时 > 60 分钟 |
| 铅封 | 二维码损坏 | 出港/进厂二维码不一致 |

### 项目结构

```
coal-transport-monitor/
├── backend/          # Python后端 (FastAPI)
├── frontend/         # React前端
├── docs/             # 文档
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## English

### Overview

An intelligent monitoring and risk early-warning system for coal transport trucks, based on port-to-factory data comparison. Focuses on three core indicators: **weight, time, and seal verification** to identify transportation fraud risks.

### Core Features

- **Weight Anomaly Detection** - Smart identification of shortage/overage with static + dynamic thresholds
- **Time Anomaly Detection** - Automatic alerts for transport delays and abnormal stops
- **Seal Verification** - Port/factory QR code comparison to prevent tampering
- **Tiered Alerts** - General (yellow) / Severe (red) alert classification
- **Risk Dashboard** - Real-time monitoring, trend analysis, high-risk vehicle ranking
- **Closed-loop Management** - Alert → Acknowledge → Resolve → Archive full traceability

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLAlchemy 2.0 + Pydantic v2 |
| Frontend | React 18 + TypeScript + Ant Design 5 |
| Visualization | ECharts |
| Analytics | Pandas + NumPy + Scikit-learn |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Container | Docker Compose |

### Quick Start

```bash
git clone https://github.com/woshiniba-debug/coal-transport-monitor.git
cd coal-transport-monitor

# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Alert Rules

| Type | General Alert | Severe Alert |
|------|--------------|-------------|
| Weight | Overage > 3‰ | Shortage > 3‰ |
| Time | 30-60 min over | > 60 min over |
| Seal | QR damaged | Port/factory QR mismatch |

### License

MIT
