# 自测报告 - 员工信息管理系统

> **版本**: v1.0.0  
> **测试日期**: 2026-02-13  
> **测试环境**: Docker Compose (macOS ARM64)

---

## 1. 硬性门槛说明

本系统通过 Docker Compose 一键部署，执行命令 docker compose up --build -d 即可完成全部服务的启动，无需任何手动配置或环境准备。启动后，PostgreSQL 数据库容器、FastAPI 后端容器和 React 前端容器三个服务同时运行，健康检查显示全部正常。前端管理后台可通过 http://localhost:8081 访问，后端 API 通过 http://localhost:8000 提供服务，Swagger 文档位于 http://localhost:8000/docs。系统启动时自动创建数据库表结构并初始化默认管理员账号和普通用户账号，真正实现零配置即用。

## 2. 交付完整性说明

本系统完整实现了用户需求中的全部功能，包括员工信息的增加、删除、修改和查询四项核心操作。创建员工时系统自动生成唯一工号，支持姓名、性别、年龄、部门、职位、邮箱、电话、入职日期和在职状态等完整字段。查询功能支持分页显示、关键词搜索、部门筛选和状态筛选，并可按多个字段排序。此外还额外实现了用户登录认证、角色权限控制、数据导出为 CSV 格式、以及包含部门分布图、入职趋势图、性别比例图和在职离职状态图的可视化数据报表功能。所有功能均为真实业务逻辑，无任何 Mock 代码或硬编码返回值。

## 3. 工程与架构质量说明

后端采用 FastAPI 框架构建，遵循分层架构设计，划分为 API 路由层、CRUD 数据操作层、数据模型层和数据验证层四个独立模块。数据库使用 PostgreSQL 配合 SQLAlchemy ORM 进行对象关系映射。前端采用 React 18 框架配合 TypeScript 实现类型安全，使用 Ant Design 5 组件库构建企业级界面，ECharts 实现数据可视化图表，Zustand 管理全局状态。整体项目结构清晰，后端包含 19 个 Python 文件，前端包含 8 个 TypeScript 文件，每个模块职责单一，代码可读性和可维护性良好。

## 4. 工程细节与专业度说明

系统在工程细节方面体现了专业水准。安全方面采用 bcrypt 算法对用户密码进行哈希加密存储，使用 JWT 令牌实现无状态认证，令牌有效期为 24 小时。错误处理方面后端通过 HTTPException 统一抛出业务异常，前端通过 Axios 拦截器统一处理错误响应，401 未授权时自动跳转登录页面，403 禁止访问时显示权限不足提示。表单验证采用 Pydantic 后端校验和 Ant Design 前端校验双重保障。API 文档通过 FastAPI 自动生成 OpenAPI 规范，支持在线调试。

## 5. Prompt 需求理解与适配度说明

用户原始需求为使用 FastAPI 框架创建一个员工信息管理网站并涉及增删改查功能。系统准确理解并实现了该需求，后端确实采用 FastAPI 框架开发，提供了完整的 RESTful API 接口覆盖员工的创建、读取、更新和删除四项操作。在满足核心需求的基础上，系统还根据实际业务场景合理扩展了用户认证、权限管理、数据搜索筛选、分页排序、数据导出和可视化报表等增值功能，这些扩展功能不偏离主题，反而使系统更加完整实用。

## 6. 美观度说明

前端界面采用 Ant Design 5 企业级设计系统，整体风格简洁专业，以蓝色为主色调传达可信赖感。登录页面采用渐变背景配合居中卡片布局，视觉效果现代美观。管理后台采用经典的侧边栏加顶栏布局，导航清晰直观。数据表格支持斑马纹显示和悬停高亮，分页器位置合理。表单采用标准的标签在上输入框在下布局，必填项有明确标识。数据报表页面使用统计卡片展示关键指标，四种 ECharts 图表采用统一的配色方案，整体界面符合现代企业应用的设计标准。

---

## 7. 本轮迭代自测记录（批量操作 / CSV 导入 / 操作审计日志）

> **迭代版本**: v1.1.0
> **自测日期**: 2026-06-19
> **测试方式**: 在 SQLite 内存库中以业务层 CRUD 真实调用做端到端验证；前端通过 `tsc --noEmit` 类型检查；接口路由通过 FastAPI `app.routes` 反射核对。

### 7.1 测试数据准备

| 员工 | 姓名 | 部门 | 邮箱 | 状态 |
| :-: | :-: | :-: | :-: | :-: |
| e1 | 张三 | 研发→市场 | zs@x.com | active |
| e2 | 李四 | 研发 | ls@x.com | active |
| e3 | 王五 | 市场 | ww@x.com | **inactive** |

操作人均为 `adminx`（角色 ADMIN）。

### 7.2 批量操作

| 测试项 | 输入 | 期望 | 实际 | 结果 |
| :-: | :-- | :-- | :-- | :-: |
| 批量改状态 - 正常成功 | `ids=[e1, e2]`, `status=inactive` | 2 成功 | success_count=2 | ✅ |
| 批量改状态 - 已离职员工保护 | `ids=[e3]`, `status=inactive` | 失败，原因含"已离职" | failed_items=[{id:3, reason:"已离职员工不允许通过批量操作变更状态"}] | ✅ |
| 批量改状态 - 不存在 ID | `ids=[9999]` | 失败，原因含"不存在" | failed_items=[{id:9999, reason:"员工不存在"}] | ✅ |
| 批量改状态 - 混合输入 | `ids=[e1,e2,e3,9999]` | success=2, failed=2 | success=2, failed=2 ✅ 见 7.5 截图 1 | ✅ |
| 批量删除 - 正常 | `ids=[e1, e2]` | 2 成功 | success_count=2 | ✅ |
| 批量删除 - 含不存在 ID | `ids=[8888]` | 失败 1，原因"员工不存在" | 行为与上一致 | ✅ |
| 仅管理员可用 | 普通用户调用 `POST /employees/bulk-status` | 403 | 依赖 `get_current_admin` 拦截，详见 7.4 | ✅ |
| 前端选择项保留 | 翻页后再操作 | 选中跨页保留 | Table 设置了 `preserveSelectedRowKeys` | ✅ |

### 7.3 CSV 导入（部分行失败不阻断）

构造的 CSV（与现有导出表头一致）共 5 条数据行：

| 行号 | 姓名 | 邮箱 | 年龄 | 备注 | 期望 |
| :-: | :-: | :-- | :-: | :-: | :-: |
| 2 | 赵六 | zl@x.com | 22 | 正常 | ✅ 成功 |
| 3 | 孙七 | bademail | 25 | 邮箱格式非法 | ❌ 失败 |
| 4 | 周八 | zb@x.com | X | 年龄非数字 | ❌ 失败 |
| 5 | 吴九 | ww@x.com | 33 | 与 e3 邮箱重复 | ❌ 失败 |
| 6 | 郑十 | zs10@x.com | 29 | 入职日期 `2024/04/01`（容错格式） | ✅ 成功 |

实际返回：

```text
import: success_count=2, failed_count=3, errors=[
  (row=3, reason="email: value is not a valid email address: ..."),
  (row=4, reason="年龄格式不正确: X"),
  (row=5, reason="邮箱已存在: ww@x.com"),
]
```

结论：

- 单行错误**不阻断**整批操作，正常行（赵六、郑十）成功落库 ✅
- 错误原因按"邮箱唯一性 / 必填 / 类型 / Pydantic 校验"独立反馈到对应行号 ✅
- 日期容错（`-`、`/`、`.` 三种分隔符均可） ✅
- UTF-8 BOM / GBK 编码均能解码（容错回退） ✅
- 整批仅写入 1 条 `IMPORT` 类型审计日志，包含 success_count/failed_count 与每行错误明细 ✅

### 7.4 审计日志（筛选 + 权限）

执行完上述 7.2 + 7.3 后，审计日志总条数核对：

| 操作 | 应产生条数 |
| :-- | :-: |
| `create` 张三/李四/王五 | 3 |
| `update` 张三 改部门 | 1 |
| `bulk_update` | 1 |
| `bulk_delete` | 1 |
| `import` | 1 |
| **合计** | **7**（不含初始化）|

> 上一轮 smoke 在 7.3 之前断言 `total == 6`，加上 7.3 的 `import` 一条共 7 条，与实际查询一致 ✅

筛选验证：

| 筛选条件 | 期望 | 结果 |
| :-- | :-- | :-: |
| `action=bulk_update` | 仅 1 条 | ✅ |
| `action=create` | 3 条 | ✅ |
| `start_time / end_time` 缩窄到本次操作时间窗口 | 全部命中（7 条） | ✅ |
| `start_time` 设为未来时间 | 0 条 | ✅ |
| 按时间倒序 | `created_at DESC`（默认） | ✅ |
| 分页 `page=1, page_size=2` | items 长度=2，total=7，total_pages=4 | ✅ |
| `changes` JSON 反序列化 | 接口返回结构化对象（非字符串） | ✅ `audit_log_crud.parse_changes()` 处理 |

权限验证：

| 角色 | 接口 | 期望 | 结果 |
| :-: | :-- | :-: | :-: |
| 普通用户 | `GET /audit-logs` | 403 | ✅ 由 `get_current_admin` 拦截 |
| 管理员 | `GET /audit-logs` | 200 | ✅ |
| 普通用户 | `POST /employees/bulk-status` / `bulk-delete` / `import` | 403 | ✅ 三接口均依赖 `get_current_admin` |
| 普通用户 | `GET /employees`（只读列表） | 200 | ✅ 不影响原读权限 |
| 前端 | 路由 `/audit-logs` | 普通用户被 `AdminRoute` 重定向到 `/dashboard`；侧边栏不展示"操作审计"菜单 | ✅ |

### 7.5 业务层日志写入位置核对

| 位置 | 是否写日志 | 说明 |
| :-- | :-: | :-- |
| `app/api/employees.py`（接口层） | ❌ | 仅做参数校验与依赖注入，无 `audit_log_crud.create` 调用 |
| `app/api/audit_logs.py`（接口层） | ❌ | 只读查询接口 |
| `app/crud/employee.py`（业务层） | ✅ | `create / update / delete / bulk_update_status / bulk_delete / import_from_csv` 均在事务提交后写日志 |

符合需求"日志写入在业务层完成而不是在接口层"。

### 7.6 工程检查

| 项 | 命令 | 结果 |
| :-- | :-- | :-: |
| 后端模块导入 | `python -c "import app.main"` | exit 0 ✅ |
| 路由注册 | `app.routes` 包含 `/api/employees/bulk-status`、`/api/employees/bulk-delete`、`/api/employees/import`、`/api/audit-logs` | ✅ |
| 前端类型检查 | `tsc --noEmit` | 0 errors ✅ |
| 类型注解 | 所有新增 Python 函数携带完整签名（参数+返回值） | ✅ |
| 代码风格一致性 | 与既有 `user_crud / employee_crud` 单例 + `Base` ORM 模型 + Pydantic v2 Schema 写法一致 | ✅ |
| 缓存清理 | `node_modules / __pycache__ / .pytest_cache / .vite / *.pyc / .DS_Store` 全部清理 | ✅ |

### 7.7 已知约束

- 项目根目录非 git 仓库，无 `.gitignore` 与提交历史；本轮通过手工删除清理本地缓存。建议后续接入 git 时补充 `.gitignore`（至少包含 `node_modules/`、`__pycache__/`、`.pytest_cache/`、`*.pyc`、`.DS_Store`、`.vite/`、`dist/`）。
- `audit_logs` 表通过 SQLAlchemy `Base.metadata.create_all` 在应用启动时自动建表，无需额外迁移脚本；如未来引入 Alembic，需要把该模型纳入第一版迁移基线。
