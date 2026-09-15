# 🏭 OpenCMMS

> 开源设备维护管理系统 - An open-source CMMS built with Django

一个基于Django和Vue.js的现代化设备维护管理系统，提供完整的设备台账、工单管理、保养计划、备件管理等功能。

**作者**: [Grant_Shen](https://github.com/shenqiang3332314)

## 📋 系统概述

CMMS (Computerized Maintenance Management System) 是一个专业的设备维护管理系统，帮助企业：

- 📊 管理设备台账和生命周期
- 🔧 处理维修工单和任务分配
- 📅 制定和执行预防性保养计划
- 📦 管理备件库存和采购
- 📈 生成维护报表和分析
- 👥 用户权限和角色管理

## 🚀 快速开始

### 系统要求

- **Python**: 3.8 或更高版本
- **操作系统**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **内存**: 最小 2GB RAM
- **存储**: 最小 1GB 可用空间

### 方式一：一键启动（开发环境）

#### Windows用户
```bash
# 双击运行或在命令行执行
start.bat
```

#### Linux/macOS用户
```bash
# 给脚本执行权限
chmod +x start.sh

# 运行启动脚本
./start.sh
```

### 方式二：可执行文件（生产部署）

#### 打包成exe文件
```bash
# Windows下打包成独立可执行文件
package_cmms.bat
```

打包完成后，可执行文件位于 `CMMS_发布包/CMMS系统.exe`，可以直接复制到任何Windows电脑运行。

详细打包说明请参考：[打包说明.md](打包说明.md)

#### 如果自动启动失败
如果遇到启动问题，请参考 [安装指南](INSTALL_GUIDE.md) 进行手动安装：

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境 (Windows)
venv\Scripts\activate.bat
# 或 (Linux/macOS)
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 数据库迁移
python manage.py migrate

# 5. 创建管理员账户
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123', role='admin', full_name='System Administrator') if not User.objects.filter(username='admin').exists() else print('Admin already exists')"

# 6. 启动服务器
python manage.py runserver 0.0.0.0:8000
```

### 首次访问

启动成功后，在浏览器中访问：

- **前端界面**: http://10.215.73.161:8000/static/index.html
- **管理后台**: http://10.215.73.161:8000/admin
- **API文档**: http://10.215.73.161:8000/api
- **本机访问**: http://127.0.0.1:8000 (仅本机可访问)

### Run with Docker

```bash
cp .env.example .env
# Set SECRET_KEY in .env before starting
docker compose up --build
```

访问 http://localhost/ 查看应用，或访问 http://localhost/health/ 检查服务状态。

### 默认账户

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 系统管理员 | `admin` | `admin123` | 全部功能 |

## 🏗️ 项目结构

```
OpenCMMS/
├── 📁 assets/              # 设备台账模块
├── 📁 workorders/          # 工单管理模块
├── 📁 maintenance/         # 保养计划模块
├── 📁 inspections/         # 点检记录模块
├── 📁 spareparts/          # 备件管理模块
├── 📁 users/               # 用户管理模块
├── 📁 reports/             # 报表统计模块
├── 📁 static/              # 静态文件
│   ├── 📁 css/            # 样式文件
│   ├── 📁 js/             # JavaScript文件
│   └── 📄 index.html      # 主界面
├── 📁 templates/           # Django模板
├── 📁 tests/               # 测试文件
│   ├── 📁 backend/        # 后端API测试
│   ├── 📁 frontend/       # 前端功能测试
│   └── 📁 integration/    # 集成测试
├── 📁 logs/                # 日志文件
├── 📁 media/               # 媒体文件
├── 📄 manage.py            # Django管理脚本
├── 📄 requirements.txt     # Python依赖
├── 📄 setup.py             # 安装脚本
├── 📄 start.bat            # Windows启动脚本
├── 📄 start.sh             # Linux/macOS启动脚本
└── 📄 README.md            # 项目说明
```

## 🎯 核心功能

### 1. 设备台账管理
- ✅ 设备信息录入和维护
- ✅ 设备分类和层级管理
- ✅ 设备状态跟踪
- ✅ 设备生命周期管理
- ✅ 设备文档和图片管理

### 2. 工单管理
- ✅ 工单创建和分配
- ✅ 工单状态流转 (待处理→已分配→进行中→已完成→已关闭)
- ✅ 工单优先级管理
- ✅ 工单类型分类 (纠正性维护/预防性维护/点检)
- ✅ 工单成本统计

### 3. 保养计划
- ✅ 预防性保养计划制定
- ✅ 时间触发和计数器触发
- ✅ 自动生成保养工单
- ✅ 保养清单模板
- ✅ 保养计划激活/停用

### 4. 备件管理
- ✅ 备件库存管理
- ✅ 库存预警和补货提醒
- ✅ 备件入库/出库记录
- ✅ 备件成本统计
- ✅ 供应商管理

### 5. 用户权限
- ✅ 基于角色的权限控制
- ✅ 用户组管理
- ✅ 操作审计日志
- ✅ JWT身份认证

### 6. 报表统计
- 🚧 设备运行状态报表
- 🚧 维修成本分析
- 🚧 保养执行率统计
- 🚧 备件消耗分析

## 🔧 技术架构

### 后端技术栈
- **框架**: Django 5.2.9
- **API**: Django REST Framework
- **数据库**: SQLite (可扩展到PostgreSQL/MySQL)
- **认证**: JWT (Simple JWT)
- **任务队列**: Celery + Redis
- **文档**: Django REST Framework Browsable API

### 前端技术栈
- **框架**: 原生JavaScript + HTML5
- **样式**: CSS3 + Flexbox/Grid
- **图标**: 内置图标系统
- **交互**: 原生DOM操作
- **模块化**: ES6模块

### 开发工具
- **代码质量**: 内置代码检查
- **测试**: Django Test Framework + 自定义测试套件
- **日志**: Python logging + 文件日志
- **部署**: Docker支持 (计划中)

## 📊 用户角色

| 角色 | 权限说明 |
|------|----------|
| **系统管理员 (admin)** | 全部功能，包括用户管理、系统配置 |
| **主管 (supervisor)** | 设备管理、工单管理、保养计划、报表查看 |
| **技术员 (technician)** | 工单处理、设备信息查看、保养执行 |
| **操作员 (operator)** | 工单创建、设备状态查看 |

## 🧪 测试

### 运行测试

```bash
# 后端API测试
python tests/backend/test_maintenance_flow.py
python tests/backend/test_workorder_complete.py

# 前端功能测试
# 在浏览器中打开 tests/frontend/ 下的HTML文件

# 集成测试
# 在浏览器中打开 tests/integration/ 下的测试文件
```

### 测试覆盖

- ✅ 用户认证和权限
- ✅ 设备CRUD操作
- ✅ 工单完整流程
- ✅ 保养计划管理
- ✅ 备件库存管理
- ✅ API接口测试
- ✅ 前端功能测试

## 📝 API文档

系统提供完整的RESTful API，支持：

### 认证接口
- `POST /api/auth/login/` - 用户登录
- `POST /api/auth/logout/` - 用户登出
- `POST /api/auth/token/refresh/` - 刷新令牌

### 设备管理
- `GET /api/assets/` - 获取设备列表
- `POST /api/assets/` - 创建设备
- `GET /api/assets/{id}/` - 获取设备详情
- `PUT /api/assets/{id}/` - 更新设备
- `DELETE /api/assets/{id}/` - 删除设备

### 工单管理
- `GET /api/workorders/` - 获取工单列表
- `POST /api/workorders/` - 创建工单
- `POST /api/workorders/{id}/start/` - 开始工单
- `POST /api/workorders/{id}/complete/` - 完成工单
- `POST /api/workorders/{id}/close/` - 关闭工单

### 保养计划
- `GET /api/maintenance/plans/` - 获取保养计划列表
- `POST /api/maintenance/plans/` - 创建保养计划
- `POST /api/maintenance/plans/{id}/generate_work_order/` - 生成工单

### 备件管理
- `GET /api/spareparts/` - 获取备件列表
- `POST /api/spareparts/` - 创建备件
- `POST /api/spareparts/{id}/stock_in/` - 备件入库
- `POST /api/spareparts/{id}/stock_out/` - 备件出库

## 🔒 安全特性

- ✅ JWT身份认证
- ✅ 基于角色的访问控制 (RBAC)
- ✅ API请求频率限制
- ✅ SQL注入防护
- ✅ XSS攻击防护
- ✅ CSRF保护
- ✅ 操作审计日志

## 🚀 部署指南

### 开发环境
```bash
# 克隆项目
git clone <repository-url>
cd cmms

# 运行安装脚本
python setup.py

# 启动开发服务器
python manage.py runserver
```

### 生产环境
```bash
# 设置环境变量
export DEBUG=False
export SECRET_KEY=your-secret-key
export DATABASE_URL=your-database-url

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 收集静态文件
python manage.py collectstatic

# 启动服务器 (推荐使用Gunicorn)
gunicorn cmms_project.wsgi:application
```

## 📞 支持与反馈

### 常见问题

**Q: 忘记管理员密码怎么办？**
A: 运行 `python manage.py changepassword admin` 重置密码

**Q: 如何备份数据？**
A: 运行 `python manage.py dumpdata > backup.json` 导出数据

**Q: 如何更改数据库？**
A: 修改 `settings.py` 中的 `DATABASES` 配置

**Q: 系统支持多语言吗？**
A: 目前支持中文，可扩展其他语言

### 技术支持

- 📧 邮箱: support@cmms.com
- 📱 电话: +86-xxx-xxxx-xxxx
- 💬 在线客服: 工作日 9:00-18:00

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📈 版本历史

### v1.0.0 (2026-01-09)
- ✅ 初始版本发布
- ✅ 设备台账管理
- ✅ 工单管理系统
- ✅ 保养计划功能
- ✅ 备件管理
- ✅ 用户权限系统
- ✅ RESTful API
- ✅ 响应式前端界面

---

**🏭 OpenCMMS** - 让设备管理更简单、更高效！

Made with ❤️ by [Grant_Shen](https://github.com/shenqiang3332314)