# 中小企业智能合同审查平台

基于 **FastAPI + Vue 3** 的 AI 合同智能审查系统，为中小企业提供合同上传、AI 风险识别、人工复核、风险统计分析的全流程合同管理服务。

## ✨ 功能特性

- **AI 智能审查**：接入 DeepSeek 大模型，自动识别合同中的风险条款并生成风险评分与修改建议
- **多角色权限体系**：支持管理员（admin）、审核员（reviewer）、普通用户（user）三种角色
- **合同全流程管理**：上传 → 解析 → AI 审核 → 人工复核 → 归档的完整状态机管理
- **多格式文档解析**：支持 PDF、Word（.doc/.docx）、TXT 文本提取，含扫描件 OCR 识别
- **可视化统计分析**：仪表板展示合同数量、风险分布（ECharts 图表）
- **风险规则引擎**：内置关键词、模式匹配、逻辑三类风险规则，可动态配置
- **对象存储**：基于 MinIO 的合同文件云存储，支持本地存储模式
- **安全审计**：完整的操作日志与审计追踪，密码 bcrypt 加密存储

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 · TypeScript · Vite · Pinia · Vue Router · Element Plus · ECharts · vue-i18n |
| 后端 | Python 3.10+ · FastAPI · SQLAlchemy 2.0 · Pydantic v2 |
| 数据库 | MySQL 8.0+ / MariaDB 10.5+ |
| 缓存/队列 | Redis · Celery |
| 对象存储 | MinIO |
| AI 服务 | DeepSeek（兼容 OpenAI / 本地模型） |
| 认证 | JWT（Access Token + Refresh Token）· Passlib/bcrypt |

## 📁 项目结构

```
.
├── backend/                  # 后端服务（FastAPI）
│   ├── main.py               # 应用入口
│   └── app/
│       ├── core/             # 配置、数据库、安全模块
│       ├── middleware/       # 中间件（认证等）
│       ├── models/           # SQLAlchemy 数据模型
│       ├── routes/           # API 路由（auth/contract/review/stats/user/admin/reviewer）
│       ├── schemas/          # Pydantic 数据校验模型
│       └── services/         # 业务逻辑（AI 审核、文件解析、存储等）
├── frontend/                 # 前端应用（Vue 3 + Vite）
│   └── src/
│       ├── api/              # 接口封装
│       ├── components/       # 通用组件（PDF 预览等）
│       ├── layouts/          # 主布局
│       ├── router/           # 路由与权限守卫
│       ├── stores/           # Pinia 状态管理
│       ├── views/            # 页面（仪表板/合同/审核/管理后台）
│       └── utils/            # 工具函数
├── database/
│   └── init.sql              # 数据库初始化脚本（建表、视图、存储过程、触发器、默认数据）
├── .env.example              # 环境变量示例（复制为 .env 使用）
└── .gitignore
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+（或 MariaDB 10.5+）
- Redis 6.0+
- MinIO（可选，也可使用本地存储模式）
- DeepSeek API Key（[申请地址](https://platform.deepseek.com/)）

### 1. 初始化数据库

```bash
# 执行数据库初始化脚本，创建库表、视图、存储过程及默认数据
mysql -u root -p < database/init.sql
```

### 2. 配置环境变量

```bash
# 复制环境变量示例并填写真实配置
cp .env.example .env
```

**必须修改的关键项**（`backend/app/core/config.py` 会从 `.env` 读取，**真实密钥严禁写入代码或提交到 git**）：

| 配置项 | 说明 |
|--------|------|
| `DATABASE_URL` | 数据库连接串，格式 `mysql+aiomysql://用户:密码@主机:端口/库名` |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥（默认 AI 提供商） |
| `JWT_SECRET_KEY` | JWT 签名密钥，生产环境务必替换为强随机值 |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | MinIO 对象存储凭据 |
| `SECURITY_PASSWORD_SALT` | 密码加盐值，生产环境务必替换 |

> `.env` 已被 `.gitignore` 忽略，不会提交到 git 仓库。

### 3. 启动后端

```bash
cd backend
# 创建并激活虚拟环境
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务（默认 http://localhost:8001）
python main.py
# 或：uvicorn main:app --reload
```

启动后：
- API 文档（调试模式开启）：http://localhost:8001/docs
- 健康检查：http://localhost:8001/health

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

## 🔐 安全说明

- 所有密钥（API Key、数据库密码、JWT 密钥）统一通过 `.env` 环境变量注入，禁止硬编码
- 用户密码使用 bcrypt 加盐哈希存储
- JWT 采用双 Token 机制（短期 Access Token + 刷新 Token）
- 接口按角色做权限控制（admin / reviewer / user）
- 生产环境部署前请务必替换默认密码、JWT 密钥与密码盐值

## 📄 API 文档

启动后端后，浏览器访问以下地址查看交互式 API 文档：

- Swagger UI：`http://localhost:8001/docs`
- ReDoc：`http://localhost:8001/redoc`

主要接口模块（前缀 `/api/v1`）：

| 模块 | 前缀 | 说明 |
|------|------|------|
| 认证 | `/api/v1/auth` | 登录、注册、Token 刷新、忘记密码/重置密码 |
| 合同管理 | `/api/v1/contracts` | 合同上传、列表、详情、状态管理 |
| 合同审核 | `/api/v1/contracts` | AI 审核、人工复核、审核结果 |
| 统计分析 | `/api/v1/stats` | 风险分布、合同统计 |
| 用户功能 | `/api/v1/user` | 个人信息、我的合同 |
| 管理后台 | `/api/v1/admin` | 用户管理、合同管理 |
| 审核工作台 | `/api/v1/reviewer` | 待审合同队列、人工复核 |

## 📊 数据模型

系统核心数据表（详见 `database/init.sql`）：

- **users**：用户表（admin / reviewer / user 三种角色）
- **contracts**：合同主表，记录处理状态与风险信息
- **contract_reviews**：审核记录表（AI + 人工双审核）
- **risk_rules**：风险检测规则（关键词 / 模式 / 逻辑）
- **audit_logs**：操作审计日志
- **system_configs**：动态系统配置

合同处理状态机：`uploaded → parsing → parsed → ai_pending → ai_reviewed → manual_pending → reviewed / archived / error`

## 🧭 路线图

- [ ] Docker Compose 一键部署
- [ ] 合同模板库与条款模板管理
- [ ] 多租户与团队协作
- [ ] 邮件通知与导出报告
- [ ] 更多 AI 提供商适配与本地模型支持

## 📄 许可证

[MIT License](LICENSE)

---

**⚠️ 注意**：本项目默认接入第三方 AI 服务，请遵守相关服务条款，并对上传合同内容做好数据合规与脱敏处理。
