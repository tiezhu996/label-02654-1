# 员工信息管理系统

基于 **FastAPI + React + PostgreSQL** 的现代化员工信息管理系统，支持完整的 CRUD 操作、权限管理和数据报表。

## 1. How to Run

```bash
docker compose up --build -d
```

## 2. Services

| 服务 | 地址 |
|------|------|
| 前端管理后台 | http://localhost:8081 |
| 后端 API | http://localhost:8000 |
| API 文档 (Swagger) | http://localhost:8000/docs |
| API 文档 (ReDoc) | http://localhost:8000/redoc |

## 3. 测试账号

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 全部 CRUD + 导出 + 报表 |
| 普通用户 | user | user123 | 仅查看 + 报表 |

## 4. 题目内容

用 fastapi 框架创建一个员工信息管理网站，要涉及到增删改查

---

## 项目简介

这是一个功能完整的员工信息管理系统，具备以下特性：

- **员工管理**: 支持员工的增删改查操作
- **权限控制**: 管理员/普通用户双角色权限体系
- **数据搜索**: 支持按姓名、工号、部门搜索和筛选
- **数据导出**: CSV 格式数据导出
- **数据报表**: 部门分布、入职趋势、性别比例等可视化图表

## 技术栈

### 后端
| 技术 | 版本 | 说明 |
|------|------|------|
| FastAPI | 0.109.2 | 高性能 Python Web 框架 |
| SQLAlchemy | 2.0.25 | ORM 数据库操作 |
| PostgreSQL | 15 | 关系型数据库 |
| JWT (python-jose) | 3.3.0 | 用户认证 |
| Pydantic | 2.6.1 | 数据验证 |

### 前端
| 技术 | 版本 | 说明 |
|------|------|------|
| React | 18.2.0 | 前端框架 |
| TypeScript | 5.3.3 | 类型安全 |
| Ant Design | 5.14.1 | UI 组件库 |
| ECharts | 5.5.0 | 数据可视化 |
| Zustand | 4.5.1 | 状态管理 |
| React Router | 6.22.1 | 路由管理 |

### 部署
| 技术 | 说明 |
|------|------|
| Docker | 容器化 |
| Docker Compose | 服务编排 |
| Nginx | 前端静态资源服务 |

## 项目结构

```
label-02654/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/               # API 路由 (auth, employees)
│   │   ├── core/              # 核心配置 (config, database, security)
│   │   ├── crud/              # 数据库操作 (user, employee)
│   │   ├── models/            # 数据模型 (User, Employee)
│   │   └── schemas/           # Pydantic 模式
│   ├── tests/                 # 单元测试 (31 个用例)
│   ├── requirements.txt       # 生产依赖
│   ├── requirements-dev.txt   # 开发依赖
│   └── Dockerfile
├── frontend-admin/             # React 管理后台
│   ├── src/
│   │   ├── api/               # API 请求封装
│   │   ├── components/        # 公共组件 (MainLayout)
│   │   ├── pages/             # 页面 (Login, Dashboard, Employee*)
│   │   └── stores/            # 状态管理 (authStore)
│   ├── package.json
│   └── Dockerfile
├── docs/                       # 项目文档
│   ├── Requirements.md        # 需求文档
│   ├── Roadmap.md             # 开发路线图
│   ├── DesignSpec.md          # 设计规范
│   ├── AuditReport.md         # 审核报告
│   └── SelfTestReport.md      # 自测报告
├── docker-compose.yml
└── README.md
```

## 功能特性

### 员工管理 (CRUD)
- ✅ 员工列表展示（分页、排序）
- ✅ 按姓名/工号/部门搜索
- ✅ 按部门/状态筛选
- ✅ 新增员工（自动生成工号）
- ✅ 编辑员工信息
- ✅ 删除员工
- ✅ 查看员工详情
- ✅ CSV 数据导出

### 数据报表
- ✅ 员工总数统计卡片
- ✅ 在职/离职统计卡片
- ✅ 本月入职统计卡片
- ✅ 部门人数分布图（饼图）
- ✅ 入职趋势图（折线图，近12个月）
- ✅ 性别比例图（饼图）
- ✅ 在职/离职状态图（饼图）

### 系统功能
- ✅ 用户登录/登出
- ✅ JWT Token 认证
- ✅ 管理员/普通用户权限控制
- ✅ 响应式布局

## API 接口

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | /api/auth/login | 用户登录 | 公开 |
| POST | /api/auth/register | 用户注册 | 公开 |
| GET | /api/auth/me | 获取当前用户 | 登录 |
| GET | /api/employees | 获取员工列表 | 登录 |
| GET | /api/employees/{id} | 获取员工详情 | 登录 |
| POST | /api/employees | 创建员工 | 管理员 |
| PUT | /api/employees/{id} | 更新员工 | 管理员 |
| DELETE | /api/employees/{id} | 删除员工 | 管理员 |
| GET | /api/employees/departments | 获取部门列表 | 登录 |
| GET | /api/employees/statistics | 获取统计数据 | 登录 |
| GET | /api/employees/export | 导出 CSV | 登录 |

## 本地开发

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

# 运行测试
pytest -v

# 启动开发服务器
uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend-admin
npm install
npm run dev
```

## 冲突解决记录

| 冲突点 | AI分析 | 用户决定 |
|--------|--------|----------|
| (无冲突) | - | - |

---

**开发完成日期**: 2026-02-13
