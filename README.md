# 中小企业智能合同审查平台

基于 **FastAPI + Vue 3** 的 AI 合同智能审查系统，为中小企业提供合同上传、AI 风险识别、人工复核、风险统计分析的全流程合同管理服务。

## 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [常用运维脚本](#常用运维脚本)
- [安全说明](#安全说明)
- [API 文档](#api-文档)
- [数据模型](#数据模型)
- [路线图](#路线图)
- [许可证](#许可证)

## 功能特性

| 模块 | 能力 |
|------|------|
| **AI 智能审查** | 自动识别合同风险条款，生成风险评分、风险等级与修改建议 |
| **多 AI 提供商** | 支持 DeepSeek / OpenAI / 本地模型切换（`AI_PROVIDER` 配置） |
| **多角色权限** | 管理员（admin）、审核员（reviewer）、普通用户（user）三种角色 |
| **全流程管理** | 上传 → 解析 → AI 审核 → 人工复核 → 归档的完整状态机管理 |
| **多格式解析** | PDF、Word（.doc/.docx）、TXT 文本提取，扫描件 OCR 识别 |
| **可视化统计** | 仪表板展示合同数量、风险分布（ECharts 图表） |
| **风险规则引擎** | 关键词、模式匹配、逻辑三类风险规则，可动态配置 |
| **双模存储** | MinIO 对象存储 / 本地存储（`STORAGE_TYPE` 配置） |
| **安全审计** | 操作日志与审计追踪，密码 bcrypt 加盐哈希 |
| **邮件通知** | 忘记密码 / 密码重置邮件发送（未配置 SMTP 时自动降级为开发模式） |

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 · TypeScript · Vite · Pinia · Vue Router · Element Plus · ECharts · axios · vue-i18n |
| 后端 | Python 3.10+ · FastAPI · SQLAlchemy 2.0 · Pydantic v2 · Alembic |
| 数据库 | MySQL 8.0+ / MariaDB 10.5+ |
| 缓存/队列 | Redis · Celery |
| 文件存储 | MinIO（可选，支持本地存储模式） |
| 文档解析 | PyPDF2 · python-docx · pytesseract（OCR）· pdf2image |
| AI 服务 | DeepSeek / OpenAI / 本地模型（`deepseek`、`openai`、`local`） |
| 认证 | JWT（Access Token + Refresh Token）· Passlib / bcrypt |

## 项目结构

```
.
├── backend/                       # 后端服务（FastAPI）
│   ├── main.py                    # 应用入口（含生命周期、CORS、全局异常处理）
│   ├── requirements.txt           # Python 依赖
│   ├── scripts/                   # 运维脚本
│   │   └── migrate_stuck_contracts.py   # 修复卡在处理状态的合同
│   └── app/
│       ├── core/                  # 配置、数据库、安全模块
│       ├── middleware/            # 中间件（认证，当前暂未启用）
│       ├── models/                # SQLAlchemy 数据模型
│       ├── routes/                # API 路由（auth/contract/review/stats/user/admin/reviewer）
│       ├── schemas/               # Pydantic 数据校验模型
│       └── services/              # 业务逻辑
│           ├── ai_service.py           # AI 模型调用（多提供商）
│           ├── ai_review_service.py    # AI 审核业务
│           ├── contract_processing_service.py  # 合同处理流水线
│           ├── file_service.py         # 文件存取（本地 / MinIO 双模式）
│           ├── minio_service.py        # MinIO 对象存储封装
│           └── parser_service.py       # 文档解析与 OCR
├── frontend/                      # 前端应用（Vue 3 + Vite）
│   └── src/
│       ├── api/                   # 接口封装（auth/contract/dashboard/userContract/reviewer/admin）
│       ├── components/            # 通用组件（PDF 预览等）
│       ├── layouts/               # 主布局
│       ├── router/                # 路由与权限守卫
│       ├── stores/                # Pinia 状态管理
│       ├── types/                 # TypeScript 类型定义
│       ├── utils/                 # 工具函数
│       └── views/                 # 页面
│           ├── Dashboard.vue           # 仪表板
│           ├── Login/Register/ForgotPassword/ResetPassword.vue   # 认证相关
│           ├── contract/               # 上传合同 / 合同详情 / 合同审核
│           ├── user/                   # 我的合同
│           ├── review/                 # 审核工作站
│           ├── admin/                  # 用户管理 / 合同管理
│           └── profile/ settings/ help/ error/   # 个人中心 / 系统设置 / 帮助中心 / 404
├── database/
│   └── init.sql                   # 数据库初始化脚本（建库、建表、视图、存储过程、触发器、默认数据）
├── .env.example                   # 环境变量示例（复制为 .env 使用）
├── .gitignore
├── LICENSE
└── README.md
```

## 快速开始

### 环境要求

| 依赖 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.10+ | 后端运行环境 |
| Node.js | 18+ | 前端构建环境 |
| MySQL / MariaDB | 8.0+ / 10.5+ | 主数据库 |
| Redis | 6.0+ | 缓存、Celery 队列、Token 存储 |
| MinIO | 可选 | 对象存储，不配置时使用本地存储模式 |
| AI API Key | 必填 | DeepSeek 或 OpenAI 密钥 |

### 1. 初始化数据库

```bash
# 执行初始化脚本，自动建库、建表、视图、存储过程、触发器及默认数据
mysql -u root -p < database/init.sql
```

### 2. 配置环境变量

```bash
# 复制环境变量示例并填写真实配置
cp .env.example .env
```

**必须修改的关键项**（真实密钥严禁提交到 git，`.env` 已被 `.gitignore` 忽略）：

| 配置项 | 说明 |
|--------|------|
| `DATABASE_URL` | 数据库连接串，如 `mysql://用户:密码@主机:端口/contract_db` |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥（默认 AI 提供商，申请见 [DeepSeek 开放平台](https://platform.deepseek.com/)） |
| `JWT_SECRET_KEY` | JWT 签名密钥，生产环境务必替换为强随机值 |
| `SECURITY_PASSWORD_SALT` | 密码加盐值，生产环境务必替换 |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | 对象存储凭据（使用 MinIO 时） |
| `STORAGE_TYPE` | 文件存储模式：`minio`（默认）或 `local` |

> 可选配置：切换 AI 提供商使用 `AI_PROVIDER=openai|local`；配置 `SMTP_*` 后启用真实邮件通知，否则忘记密码功能降级为开发模式（重置链接打印到日志）。

### 3. 启动后端

```bash
cd backend

# 创建并激活虚拟环境
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务（默认 http://localhost:8001，DEBUG 模式自动热重载）
python main.py
# 或：uvicorn main:app --reload
```

启动后：

- 健康检查：`http://localhost:8001/health`
- Swagger 文档（仅 DEBUG 模式）：`http://localhost:8001/docs`
- ReDoc 文档（仅 DEBUG 模式）：`http://localhost:8001/redoc`

### 4. 启动前端

```bash
cd frontend

npm install
npm run dev

# 访问 http://localhost:5173
```

### 默认账号

数据库初始化脚本会创建一个默认管理员账号：

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | `admin` | `admin123` |

> ⚠️ 首次登录后请立即修改默认密码。

## 常用运维脚本

| 脚本 | 用途 |
|------|------|
| `backend/scripts/migrate_stuck_contracts.py` | 将因异常中断而长期卡在 `parsing` / `ai_pending` 等状态的合同批量修正为 `error` |

## 安全说明

- 所有密钥（API Key、数据库密码、JWT 密钥）统一通过 `.env` 环境变量注入，禁止硬编码
- 用户密码使用 bcrypt 加盐哈希存储
- JWT 采用双 Token 机制（短期 Access Token + 长期 Refresh Token）
- 接口按角色做权限控制（admin / reviewer / user），前端路由同步守卫
- 上传文件类型白名单校验（`pdf, doc, docx, txt`）与大小限制（默认 50MB）
- 生产环境部署前请务必替换默认密码、JWT 密钥与密码盐值

## API 文档

启动后端（DEBUG 模式）后，浏览器访问以下地址查看交互式 API 文档：

- Swagger UI：`http://localhost:8001/docs`
- ReDoc：`http://localhost:8001/redoc`

接口统一前缀 `/api/v1`，主要模块如下：

| 模块 | 前缀 | 说明 |
|------|------|------|
| 认证 | `/api/v1/auth` | 登录、注册、Token 刷新、忘记密码 / 重置密码 |
| 合同管理 | `/api/v1/contracts` | 合同上传、列表、详情、状态管理 |
| 合同审核 | `/api/v1/contracts` | AI 审核、人工复核、审核结果、风险分布 |
| 统计分析 | `/api/v1/stats` | 合同统计、风险分布 |
| 用户功能 | `/api/v1/user` | 个人信息、我的合同 |
| 管理员功能 | `/api/v1/admin` | 用户管理、合同管理 |
| 审核员工作台 | `/api/v1/reviewer` | 待审合同队列、人工复核 |

## 数据模型

### 核心数据表

| 表名 | 说明 |
|------|------|
| `users` | 用户表（admin / reviewer / user 三种角色，含邮箱、公司、时区等） |
| `contracts` | 合同主表，记录合同类型、处理状态、风险评分与文件信息 |
| `contract_reviews` | 审核记录表（AI + 人工双审核） |
| `risk_rules` | 风险检测规则（关键词 / 模式 / 逻辑） |
| `audit_logs` | 操作审计日志 |
| `system_configs` | 动态系统配置 |

### 视图 / 存储过程 / 触发器

| 类型 | 名称 | 说明 |
|------|------|------|
| 视图 | `contract_stats` | 合同统计视图（按状态 / 类型汇总） |
| 视图 | `risk_distribution` | 风险分布视图（按风险等级汇总） |
| 存储过程 | `GetUserContractStats` | 按用户统计合同数据 |
| 触发器 | `update_contract_parsed_at` | 合同解析完成时自动维护时间字段 |
| 触发器 | `log_contract_review` | 审核写入时自动记录审计日志 |

### 合同状态机

```
uploaded → parsing → parsed → ai_pending → ai_reviewed → manual_pending → reviewed
                                                                    ├── archived
                                                                    └── error
```

## 路线图

- [ ] Docker Compose 一键部署
- [ ] 合同模板库与条款模板管理
- [ ] 多租户与团队协作
- [ ] 邮件通知与导出报告（已支持重置密码邮件，待扩展）
- [ ] 更多 AI 提供商适配与本地模型支持

## 许可证

[MIT License](LICENSE)

---

**⚠️ 注意**：本项目默认接入第三方 AI 服务，请遵守相关服务条款，并对上传合同内容做好数据合规与脱敏处理。
