# 汽车运煤智能监督与风险预警系统 - 开发计划

## 项目概述

基于港口—入厂数据比对的汽车运煤智能监督与风险预警系统。聚焦**重量、时间、铅封**三大核心指标，构建燃煤汽运全流程监督体系，精准识别运输舞弊隐患。

## 技术栈选型（最优方案）

### 后端
- **Python 3.12+** + **FastAPI** (高性能异步框架，自动生成OpenAPI文档)
- **SQLAlchemy 2.0** (async) + **SQLite** (开发) / **PostgreSQL** (生产)
- **Pydantic v2** (数据验证，与FastAPI深度集成)
- **APScheduler** (定时任务，用于批量数据分析)

### 前端
- **React 18** + **TypeScript** + **Vite**
- **Ant Design 5** (企业级UI组件库，中文友好)
- **ECharts** (数据可视化，适合仪表盘)
- **React Router v6** + **Zustand** (轻量状态管理)

### 算法/分析
- **NumPy** + **Pandas** (数据分析)
- **Scikit-learn** (异常检测：Isolation Forest, Z-score)
- 动态阈值算法 (基于历史数据的滑动窗口统计)

## 项目结构

```
coal-transport-monitor/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI应用入口
│   │   ├── config.py               # 配置管理
│   │   ├── database.py             # 数据库连接
│   │   ├── models/                 # SQLAlchemy模型
│   │   │   ├── __init__.py
│   │   │   ├── vehicle.py          # 车辆信息
│   │   │   ├── transport.py        # 运输记录
│   │   │   ├── seal.py             # 铅封记录
│   │   │   ├── alert.py            # 预警记录
│   │   │   └── user.py             # 用户权限
│   │   ├── schemas/                # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── vehicle.py
│   │   │   ├── transport.py
│   │   │   ├── seal.py
│   │   │   ├── alert.py
│   │   │   └── dashboard.py
│   │   ├── api/                    # API路由
│   │   │   ├── __init__.py
│   │   │   ├── vehicles.py
│   │   │   ├── transports.py
│   │   │   ├── alerts.py
│   │   │   ├── dashboard.py
│   │   │   └── auth.py
│   │   ├── services/               # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── risk_engine.py      # 风险检测引擎(核心)
│   │   │   ├── weight_analyzer.py  # 重量异常分析
│   │   │   ├── time_analyzer.py    # 时间异常分析
│   │   │   ├── seal_analyzer.py    # 铅封异常分析
│   │   │   └── statistics.py       # 统计分析
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── helpers.py
│   ├── tests/
│   ├── alembic/                    # 数据库迁移
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/                    # API客户端
│   │   ├── components/             # 通用组件
│   │   │   ├── Layout/
│   │   │   ├── AlertBadge/
│   │   │   └── StatusIndicator/
│   │   ├── pages/                  # 页面
│   │   │   ├── Dashboard.tsx       # 首页仪表盘
│   │   │   ├── TransportList.tsx   # 运输记录
│   │   │   ├── AlertCenter.tsx     # 预警中心
│   │   │   ├── VehicleManage.tsx   # 车辆管理
│   │   │   └── Settings.tsx        # 系统设置
│   │   ├── stores/                 # Zustand状态
│   │   └── utils/
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   └── api.md
├── docker-compose.yml
├── Makefile
├── README.md
└── PLAN.md
```

## 数据模型设计

### 1. Vehicle (车辆信息)
```python
class Vehicle:
    id: int (PK)
    plate_number: str          # 车牌号 (唯一索引)
    tare_weight: float         # 皮重(kg)
    driver_name: str           # 司机姓名
    driver_phone: str          # 司机电话
    status: VehicleStatus      # ACTIVE/INACTIVE
    created_at: datetime
    updated_at: datetime
```

### 2. TransportRecord (运输记录) - 核心表
```python
class TransportRecord:
    id: int (PK)
    vehicle_id: int (FK -> Vehicle)
    
    # 出港信息
    departure_port: str            # 出发港口
    departure_weight: float        # 出港过磅重量(kg) 毛重
    departure_net_weight: float    # 出港净重(kg) = 毛重 - 皮重
    departure_time: datetime       # 出发时间
    departure_seal_id: int (FK)    # 出港铅封ID
    
    # 进厂信息
    arrival_weight: float          # 进厂过磅重量(kg) 毛重
    arrival_net_weight: float      # 进厂净重(kg) = 毛重 - 皮重
    arrival_time: datetime         # 到达时间
    arrival_seal_id: int (FK)      # 进厂铅封ID
    
    # 计算字段
    weight_diff: float             # 重量差 = 进厂净重 - 出港净重
    weight_diff_ratio: float       # 重量偏差率 = 重量差 / 出港净重
    transport_duration: int        # 运输耗时(分钟)
    
    # 状态
    status: RecordStatus           # NORMAL / ALERT / SEVERE
    alert_count: int               # 累计预警次数
    notes: str                     # 备注
    
    created_at: datetime
    updated_at: datetime
```

### 3. SealRecord (铅封记录)
```python
class SealRecord:
    id: int (PK)
    qr_code: str               # 铅封二维码内容
    seal_type: SealType        # DEPARTURE / ARRIVAL
    is_valid: bool             # 是否有效
    scan_time: datetime        # 扫描时间
    image_url: str             # 铅封照片URL(可选)
    transport_id: int (FK)     # 关联运输记录
```

### 4. Alert (预警记录)
```python
class Alert:
    id: int (PK)
    transport_id: int (FK -> TransportRecord)
    alert_type: AlertType      # WEIGHT_SHORTAGE / WEIGHT_OVERAGE / TIME_EXCESSIVE / TIME_STOP / SEAL_MISMATCH / SEAL_DAMAGED
    severity: Severity         # GENERAL(一般) / SEVERE(严重)
    description: str           # 预警描述
    threshold_value: float     # 触发阈值
    actual_value: float        # 实际值
    status: AlertStatus        # PENDING / ACKNOWLEDGED / RESOLVED / DISMISSED
    resolved_by: str           # 处理人
    resolved_at: datetime      # 处理时间
    resolution_notes: str      # 处理备注
    created_at: datetime
```

### 5. User (用户)
```python
class User:
    id: int (PK)
    username: str
    hashed_password: str
    role: UserRole             # ADMIN / OPERATOR / VIEWER
    is_active: bool
    created_at: datetime
```

## 核心算法 - 风险检测引擎

### 1. 重量异常检测 (WeightAnalyzer)

```
判定规则:
- 亏吨: (出港净重 - 进厂净重) / 出港净重 > 3‰ → 严重预警
- 盈吨: (进厂净重 - 出港净重) / 出港净重 > 3‰ → 一般预警

进阶算法 (动态阈值):
- 计算该车辆/该线路历史N次运输的重量偏差均值μ和标准差σ
- 动态阈值 = μ + k*σ (k=2 for 一般, k=3 for 严重)
- 结合固定阈值(3‰)和动态阈值取较严格者
```

### 2. 时间异常检测 (TimeAnalyzer)

```
判定规则:
- 运输时长 > 正常时长 + 60min → 严重预警
- 运输时长 > 正常时长 + 30min → 一般预警

进阶算法:
- 统计该线路历史运输时长的中位数作为"正常时长"
- 使用IQR方法剔除异常值后计算基准
- 滑动窗口更新基准值(最近100次运输)
```

### 3. 铅封异常检测 (SealAnalyzer)

```
判定规则:
- 出港铅封QR码 ≠ 进厂铅封QR码 → 严重预警
- 铅封QR码无法识别/破损 → 一般预警

算法:
- 字符串精确匹配 + 相似度计算(Levenshtein距离)
- 检测QR码格式合规性
```

### 4. 综合风险评分 (RiskEngine)

```
风险评分 = Σ(alert_weight * severity_factor)

权重分配:
- 重量异常: 0.4
- 时间异常: 0.3  
- 铅封异常: 0.3

严重程度系数:
- 一般预警: 1.0
- 严重预警: 2.0

累计3次严重预警 → 高亮标记该车辆
```

## API设计 (RESTful)

### 认证
- `POST /api/auth/login` - 登录获取JWT
- `POST /api/auth/refresh` - 刷新token

### 运输记录
- `GET /api/transports` - 分页查询(支持车牌/时间/状态筛选)
- `GET /api/transports/{id}` - 详情
- `POST /api/transports` - 新增运输记录(自动触发风险检测)
- `PUT /api/transports/{id}` - 更新
- `GET /api/transports/{id}/alerts` - 该运输的预警列表

### 预警
- `GET /api/alerts` - 预警列表(支持类型/严重度/状态筛选)
- `PUT /api/alerts/{id}/acknowledge` - 确认预警
- `PUT /api/alerts/{id}/resolve` - 处理预警
- `GET /api/alerts/stats` - 预警统计

### 车辆
- `GET /api/vehicles` - 车辆列表
- `POST /api/vehicles` - 新增车辆
- `GET /api/vehicles/{plate}/history` - 车辆运输历史

### 仪表盘
- `GET /api/dashboard/overview` - 概览数据(总运输/预警数/异常率)
- `GET /api/dashboard/alert-trend` - 预警趋势(按日/周/月)
- `GET /api/dashboard/top-risk-vehicles` - 高风险车辆TOP10
- `GET /api/dashboard/weight-distribution` - 重量偏差分布

## 前端页面设计

### 1. 首页仪表盘 (Dashboard)
- 顶部: 总运输次数、活跃预警、今日异常率、平均运输时长 KPI卡片
- 中部左: 预警趋势折线图 (ECharts)
- 中部右: 重量偏差分布直方图
- 底部左: 高风险车辆TOP10表格(红灯/黄灯标识)
- 底部右: 最新预警列表(实时滚动)

### 2. 运输记录页 (TransportList)
- 表格: 车牌、出港时间、到达时间、出港重量、进厂重量、偏差率、运输时长、状态
- 筛选: 车牌、日期范围、状态(正常/一般预警/严重预警)
- 详情弹窗: 完整运输信息 + 铅封对比 + 预警详情

### 3. 预警中心 (AlertCenter)
- 预警列表: 类型图标、严重度标签、时间、描述、状态
- 操作: 确认、处理(填写备注)、忽略
- 统计: 按类型饼图、按趋势折线图

### 4. 车辆管理 (VehicleManage)
- CRUD车辆信息
- 车辆历史运输时间线
- 车辆风险评分

### 5. 系统设置 (Settings)
- 阈值配置: 重量偏差阈值、时间偏差阈值
- 用户管理: 增删改查、角色分配
- 数据导出: CSV/Excel

## 实现优先级

### Phase 1 (核心功能 - 必须)
1. 数据模型 + 数据库
2. 运输记录CRUD API
3. 三大风险检测算法
4. 预警生成 + 分级
5. 前端仪表盘 + 预警中心

### Phase 2 (增强功能)
1. 用户认证(JWT)
2. 历史数据统计
3. 数据导出
4. 动态阈值算法

### Phase 3 (未来展望)
1. GPS轨迹集成
2. 煤质数据比对
3. 承运商考核
4. 移动端适配

## 开发约束

1. 所有代码注释使用中文
2. API响应统一格式: `{"code": 200, "message": "success", "data": {...}}`
3. 前端UI全中文
4. 数据库表名使用snake_case
5. 测试覆盖率 > 80%
6. 遵循DL/T 1668-2016标准的数据记录要求
