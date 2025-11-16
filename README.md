# NowInOpenHarmony 后端服务

## 项目概述

NowInOpenHarmony 是一个聚合 OpenHarmony 相关资讯的应用后端服务。该系统从 OpenHarmony 官方网站、技术博客等多源采集新闻数据,进行结构化处理,并对外提供 RESTful 风格的数据接口供 OpenHarmony 客户端调用。采用多线程爬虫架构,支持非阻塞数据更新和智能缓存管理。

## 技术栈

- **编程语言**: Python 3.8+
- **Web框架**: FastAPI 0.104.1
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **任务调度**: APScheduler 3.10.4
- **爬虫框架**: Requests 2.31.0 + BeautifulSoup 4.12.2 + Selenium 4.15.0
- **缓存机制**: 内存缓存 + 线程安全 + 状态管理
- **部署**: Docker + Docker Compose + Uvicorn + Nginx

## 功能特性

### 数据采集模块
- 从 OpenHarmony 官方网站采集新闻和动态
- 从 OpenHarmony 技术博客采集技术文章
- 支持移动端 Banner 图片采集（传统版 + 增强版）
- 多源数据聚合（官方新闻 + 技术博客 + 轮播图）
- 智能数据去重和清洗
- 多线程并发爬虫,支持失败重试机制

### 缓存机制
- **启动预热**: 服务启动时自动执行一次数据爬取（后台线程执行）
- **精细状态管理**: 只有在写入数据库时才设为"准备中",读取时设为"已准备"
- **后台更新**: 每30分钟自动更新缓存数据（后台线程执行）
- **线程安全**: 使用可重入锁保证数据一致性
- **无缝切换**: 更新时仍使用旧数据,更新完成后切换
- **非阻塞**: 爬虫任务在独立线程执行,不阻塞主服务线程

### API接口模块
- 新闻列表和详情接口
- 支持分页、分类和搜索
- 手动触发爬取接口
- 服务状态监控接口
- 缓存刷新接口

### 定时任务模块
- 每30分钟自动更新缓存
- 每天凌晨2点执行完整爬取
- 支持失败重试机制

### 数据存储模块
- 结构化数据存储
- 支持分类存储
- 数据库索引优化

## 快速开始

### 环境要求

- Python 3.8+
- pip
- (可选) Docker & Docker Compose

### 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

**重要**: 在生产环境部署前,必须配置安全的环境变量！

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件,修改以下关键配置
```

**生产环境建议修改的配置项**:
```env
# CORS配置（仅允许可信域名,生产环境不要使用 * ）
CORS_ORIGINS=https://your-frontend-domain.com,https://admin.your-domain.com

# 数据库密码（如使用PostgreSQL）
POSTGRES_PASSWORD=your-strong-password-min-16-chars

# Redis密码（如使用Redis）
REDIS_PASSWORD=your-redis-password-here
```

### 启动服务

```bash
# 方式1: 使用启动脚本（推荐,包含IP检测等）
python run.py

# 方式2: 直接使用uvicorn（开发环境）
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# 方式3: Docker部署（生产环境推荐）
# 使用部署脚本
./deploy.sh install    # 初始化部署环境
./deploy.sh start      # 启动开发环境
./deploy.sh start prod # 启动生产环境

# 或手动Docker命令
docker-compose up -d                                   # 开发环境
docker-compose -f docker-compose.prod.yml up -d        # 生产环境
```

### 访问服务

- 服务地址: http://localhost:8001
- API文档 (Swagger): http://localhost:8001/docs
- API文档 (ReDoc): http://localhost:8001/redoc
- 健康检查: http://localhost:8001/health

## API接口

### 新闻接口

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/news/` | 获取新闻列表（支持分页、分类、搜索） |
| GET | `/api/news/{article_id}` | 获取新闻详情 |
| GET | `/api/news/openharmony` | 获取OpenHarmony官方新闻 |
| GET | `/api/news/blog` | 获取技术博客文章 |
| POST | `/api/news/crawl` | 手动触发新闻爬取 |
| GET | `/api/news/status/info` | 获取服务状态信息 |
| POST | `/api/news/cache/refresh` | 手动刷新缓存 |

### 轮播图接口

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/banner/mobile` | 获取手机版Banner图片URL列表 |
| GET | `/api/banner/mobile/enhanced` | 增强版爬虫获取Banner图片 |
| POST | `/api/banner/crawl` | 手动触发轮播图爬取 |
| GET | `/api/banner/status` | 获取轮播图服务状态 |
| DELETE | `/api/banner/cache/clear` | 清空轮播图缓存 |
| GET | `/api/banner/cache` | 获取轮播图缓存详细信息 |

### 基础接口

- `GET /` - 服务信息
- `GET /health` - 健康检查（包含缓存状态）
- `GET /api/health` - 详细API健康检查

**注意**: 当前所有API端点均为公开访问,无需认证。生产环境建议为敏感操作添加认证保护。

## Docker 中的 Banner 爬虫

### 环境变量配置

- `BANNER_USE_ENHANCED`: 是否启用增强版（Selenium）爬虫。默认 `true`。在受限环境可设为 `false`,强制使用传统解析。
- `CHROME_BIN`: 自定义 Chrome/Chromium 可执行路径（如 `/usr/bin/chromium`）
- `CHROMEDRIVER_PATH`: 自定义 Chromedriver 路径（如 `/usr/bin/chromedriver`）
- `SELENIUM_USE_USER_DATA_DIR`: 是否向 Chrome 传入 `--user-data-dir`（默认 `false`）

### 运行建议

- 使用提供的 Dockerfile 已安装 `chromium` 与 `chromium-driver`,可直接使用增强版
- 如遇到资源限制,可设置 `BANNER_USE_ENHANCED=false`,API 与定时任务会自动回退
- 如需 Selenium 稳定性:可在 docker-compose 中设置更大的共享内存 `shm_size: 1g`

### 常见问题

- **错误**: `session not created: user data directory is already in use`
  - 默认不使用 `--user-data-dir`,失败时自动切换策略
  - 如仍出现,确认是否有并发任务,或临时关闭增强版

- **找不到浏览器或驱动**:
  - 通过环境变量指定 `CHROME_BIN`、`CHROMEDRIVER_PATH` 路径
  - 或在镜像中安装对应软件包

## 安全配置指南

### 1. 环境变量安全配置（必须）

```bash
# CORS配置 - 仅允许可信来源
CORS_ORIGINS=https://your-frontend-domain.com,https://admin.your-domain.com
# 警告: 生产环境绝不能使用 * (允许所有来源)

# 数据库密码（如使用PostgreSQL）
POSTGRES_PASSWORD=<强密码,至少16字符,包含大小写字母数字特殊符号>

# Redis密码（如使用Redis）
REDIS_PASSWORD=<强密码,至少16字符>
```

### 2. SSL/TLS证书配置（生产环境必须）

```bash
# 方式1: 使用 Let's Encrypt 获取免费证书（推荐）
certbot certonly --standalone -d your-domain.com
# 证书路径: /etc/letsencrypt/live/your-domain.com/

# 方式2: 生成自签名证书（仅测试用）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem

# 更新 nginx 配置使用 HTTPS
# 参考 nginx/conf.d/openharmony.conf
```

### 3. 防火墙配置

```bash
# Ubuntu/Debian 使用 ufw
sudo ufw allow 80/tcp    # HTTP (重定向到HTTPS)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 22/tcp    # SSH (建议限制来源IP)
sudo ufw enable

# 限制SSH仅允许特定IP
sudo ufw allow from 1.2.3.4 to any port 22

# CentOS/RHEL 使用 firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 4. 数据库安全

**SQLite（仅开发/小规模）**:
- 文件权限: `chmod 600 openharmony_news.db`
- 不要暴露到Web目录

**PostgreSQL（生产环境推荐）**:
```bash
# docker-compose.yml 配置
postgres:
  environment:
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # 从环境变量读取
  volumes:
    - postgres_data:/var/lib/postgresql/data
  networks:
    - backend  # 不暴露到公网

# 启用SSL连接
DATABASE_URL=postgresql://user:password@localhost:5432/dbname?sslmode=require
```

### 5. Docker安全配置

```yaml
# docker-compose.yml 安全实践
services:
  app:
    # 使用非特权用户运行
    user: "1000:1000"
    # 只读文件系统（除了必要的挂载）
    read_only: true
    tmpfs:
      - /tmp
    # 资源限制
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
    # 安全选项
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

### 6. API速率限制（待实现）

**当前状态**: 未实现速率限制

**建议**: 为防止API滥用,建议在生产环境添加速率限制:
- 可使用 Nginx 的 `limit_req` 模块
- 或使用 Python 的 `slowapi` 库
- 参考 SECURITY_AUDIT_REPORT.md 中的实现方案

### 7. 定期安全维护

```bash
# 每月更新依赖项
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt

# 检查已知漏洞
pip install safety pip-audit
safety check
pip-audit

# 每周检查日志
tail -f logs/error_*.log
grep "ERROR\|CRITICAL" logs/app_*.log

# 审查访问日志
grep "403\|404\|500" /var/log/nginx/access.log | tail -100
```

### 8. 监控和告警

建议配置:
- 异常访问告警（大量403/500错误）
- 磁盘空间监控（日志、数据库）
- 服务可用性监控（健康检查）
- 数据库性能监控
- SSL证书过期提醒

## 安全注意事项

### 当前安全状况

**已实现的安全措施**:
- ✅ Docker 容器化隔离
- ✅ Nginx 反向代理
- ✅ 基本的 HTTP 安全头配置
- ✅ 参数化数据库查询
- ✅ 错误信息脱敏处理

**已知的安全限制**:
- ⚠️ **CORS 配置**: 默认允许所有来源(`*`),生产环境需修改为具体域名
- ⚠️ **API 认证**: 当前所有端点均无认证保护,任何人都可以调用
- ⚠️ **速率限制**: 未实现请求频率限制,可能被滥用
- ⚠️ **XSS 防护**: 爬取的内容未进行 HTML 净化
- ⚠️ **输入验证**: 基本验证已实现,但可进一步加强

### 生产环境安全建议

1. **修改 CORS 配置**: 在 `.env` 中设置 `CORS_ORIGINS` 为具体的前端域名
2. **添加访问控制**: 考虑为敏感操作添加认证机制
3. **启用速率限制**: 使用 Nginx 或应用层限流
4. **内容净化**: 对爬取的 HTML 内容进行清洗
5. **定期更新**: 保持依赖项为最新版本,修复已知漏洞

详细的安全审计报告和修复方案请参考 `SECURITY_AUDIT_REPORT.md`

## 安全增强建议（可选）

如果你需要增强项目的安全性,可以参考 `SECURITY_AUDIT_REPORT.md` 中的详细建议,包括:

1. **CORS 配置优化** - 限制为具体域名
2. **API 认证机制** - 为敏感端点添加密钥或 OAuth2 认证
3. **速率限制** - 防止 API 滥用和 DoS 攻击
4. **HTML 内容净化** - 防止 XSS 攻击
5. **依赖项安全扫描** - 使用 `safety` 或 `pip-audit` 定期检查

这些功能目前未实现,是为了保持项目简洁和易于开发。根据你的实际需求选择性实施。

## 缓存机制详解

### 服务状态
- **preparing**: 数据更新中,服务暂时不可用
- **ready**: 服务就绪,可以正常访问
- **error**: 服务错误,需要检查日志

### 工作流程
1. **服务启动**: 立即启动HTTP服务,后台线程执行初始数据爬取
2. **爬虫执行**: 爬虫执行期间状态保持为"就绪",使用现有数据响应请求
3. **数据写入**: 只有在写入数据库时才短暂设为"准备中"
4. **数据就绪**: 写入完成后立即恢复为"就绪"状态
5. **定时更新**: 每30分钟后台线程更新数据,遵循相同的精细状态管理
6. **非阻塞响应**: 整个过程中API接口始终可正常响应请求

## 测试和监控

```bash
# 健康检查
curl http://localhost:8001/health

# 查看API文档
curl http://localhost:8001/docs

# 查看服务状态详情
curl http://localhost:8001/api/news/status/info

# 手动触发数据爬取
curl -X POST http://localhost:8001/api/news/crawl

# 查看应用日志
tail -f logs/app.log
tail -f logs/error_*.log

# Docker日志
docker-compose logs -f app
./deploy.sh logs app
```

**注意**: 测试套件已精简,移除了冗余的测试文件以简化测试流程。核心测试功能通过API端点直接验证。

## 配置说明

### 环境变量完整列表

```env
# 应用配置
APP_NAME=NowInOpenHarmony API
APP_VERSION=1.0.0
DEBUG=false
HOST=0.0.0.0
PORT=8001
RELOAD=false

# CORS配置（生产环境建议修改为具体域名）
CORS_ORIGINS=*

# 数据库配置
DATABASE_URL=sqlite:///./data/openharmony_news.db
# 生产环境使用PostgreSQL:
# DATABASE_URL=postgresql://user:password@postgres:5432/openharmony_news

# PostgreSQL配置（使用Docker时）
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<强密码>
POSTGRES_DB=openharmony_news

# Redis配置（可选）
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<Redis密码>

# 爬虫配置
CRAWLER_DELAY=1.0
CRAWLER_TIMEOUT=10
MAX_RETRIES=3

# Banner爬虫配置
BANNER_USE_ENHANCED=true
CHROME_BIN=/usr/bin/chromium
CHROMEDRIVER_PATH=/usr/bin/chromedriver
SELENIUM_USE_USER_DATA_DIR=false

# 定时任务配置
ENABLE_SCHEDULER=true
CACHE_UPDATE_INTERVAL=30
FULL_CRAWL_HOUR=2

# 缓存配置
ENABLE_CACHE=true
CACHE_INITIAL_LOAD=true

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

## 项目结构

```
HongYiXun_Backend/
├── api/                           # API接口模块
│   ├── __init__.py
│   ├── news.py                   # 新闻接口（完整CRUD + 多源支持）
│   └── banner.py                 # 轮播图接口（移动端Banner采集）
├── core/                          # 核心模块
│   ├── __init__.py
│   ├── cache.py                  # 缓存管理（内存缓存 + 状态管理）
│   ├── config.py                 # 配置管理（Pydantic Settings）
│   ├── database.py               # 数据库管理（SQLAlchemy）
│   ├── logging_config.py         # 日志配置（结构化日志）
│   └── scheduler.py              # 定时任务调度（APScheduler）
├── models/                        # 数据模型
│   ├── __init__.py
│   ├── news.py                   # 新闻相关模型（文章 + 响应）
│   └── banner.py                 # 轮播图模型（Banner响应）
├── services/                      # 服务层（爬虫和业务逻辑）
│   ├── __init__.py
│   ├── news_service.py           # 新闻服务统一管理
│   ├── openharmony_news_crawler.py       # OpenHarmony官网新闻爬虫
│   ├── openharmony_blog_crawler.py       # OpenHarmony技术博客爬虫
│   ├── openharmony_image_crawler.py      # OpenHarmony图片爬虫
│   ├── mobile_banner_crawler.py          # 移动端轮播图爬虫（传统版）
│   └── enhanced_mobile_banner_crawler.py # 增强版轮播图爬虫（Selenium）
├── nginx/                         # Nginx配置
│   ├── conf.d/
│   │   └── openharmony.conf      # 反向代理配置
│   └── ssl/                      # SSL证书目录
├── logs/                          # 日志文件目录
├── data/                          # 数据文件目录
├── downloads/                     # 下载文件目录（图片等）
├── .env.example                   # 环境变量模板
├── .gitignore                     # Git忽略配置
├── main.py                        # FastAPI应用入口
├── run.py                         # 增强版启动脚本（IP检测等）
├── requirements.txt               # Python依赖
├── Dockerfile                     # Docker镜像配置
├── docker-compose.yml             # 容器编排配置（开发）
├── docker-compose.prod.yml        # 容器编排配置（生产）
├── deploy.sh                      # 部署脚本
├── CLAUDE.md                      # Claude Code项目指导
└── README.md                      # 项目说明（本文件）
```

## 架构增强特性

### 多源数据聚合
- **官方新闻**: OpenHarmony官网新闻和动态
- **技术博客**: OpenHarmony技术博客文章
- **轮播图**: 移动端Banner图片采集（双爬虫架构）
- **统一服务**: NewsService统一管理多源数据

### 多线程爬虫架构
- **ThreadPoolExecutor**: 线程池管理爬虫任务
- **非阻塞执行**: 爬虫任务在后台线程执行
- **状态管理**: 精细状态控制,只在写入时设为"准备中"
- **并发安全**: 线程安全的缓存更新机制

### 轮播图双爬虫策略
- **传统爬虫**: Requests + BeautifulSoup,快速稳定
- **增强爬虫**: Selenium WebDriver,支持动态内容
- **智能回退**: 增强版失败时自动回退到传统版
- **图片下载**: 可选下载图片到本地存储

### 缓存状态管理
- **READY**: 服务就绪,数据可用
- **PREPARING**: 正在更新,短暂状态
- **ERROR**: 服务错误,需要检查日志
- **无缝切换**: 更新过程中保持服务可用

## 多线程改进

### 问题背景
原始实现中,爬虫任务在主线程中同步执行,导致:
- 服务启动时需要等待爬虫完成（6-7分钟）
- 定时更新期间API请求被阻塞
- 用户体验差,服务响应延迟

### 解决方案
采用多线程架构:
- **ThreadPoolExecutor**: 使用线程池管理爬虫任务
- **后台执行**: 爬虫任务在独立线程中执行
- **非阻塞响应**: 主服务线程立即响应API请求
- **状态管理**: 通过缓存状态反映爬虫进度

### 改进效果
- ✅ 服务启动后立即可以响应请求
- ✅ 爬虫执行期间API接口正常响应
- ✅ 支持并发请求,不会阻塞
- ✅ 精细状态管理:只有在写入数据库时才设为"准备中"

### 技术实现
```python
# 使用ThreadPoolExecutor执行爬虫任务
self.thread_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="CrawlerWorker")

# 提交任务到后台线程
future = self.thread_pool.submit(self._run_crawler_in_thread, "任务名称")

# 精细状态管理
def set_updating(self, is_updating: bool):
    if is_updating:
        self.set_status(ServiceStatus.PREPARING)  # 只在写入时设为准备中
    else:
        self.set_status(ServiceStatus.READY)      # 写入完成后立即恢复就绪
```

## 开发指南

### 添加新的数据源

1. 在 `services/` 目录下创建新的爬虫类,继承基础爬虫接口
2. 实现数据采集和解析逻辑,支持多线程执行
3. 在 `NewsSource` 枚举中添加新数据源
4. 在 `news_service.py` 中集成新数据源
5. 在 `scheduler.py` 中添加定时任务
6. 更新数据库模型（如需要）

### 添加新的API接口

1. 在 `api/` 目录下创建新的路由文件
2. 定义数据模型（在 `models/` 中）
3. 在 `main.py` 中注册路由
4. 更新API文档（本README）

### 数据库迁移

当前使用 SQLite 进行开发,生产环境建议使用 PostgreSQL:

1. 安装 PostgreSQL 驱动: `pip install psycopg2-binary`
2. 更新 `DATABASE_URL` 环境变量
3. 运行数据库初始化脚本（启动时自动创建表）

### 代码质量检查

```bash
# 安装开发依赖
pip install flake8 black mypy

# 代码格式化
black .

# 代码风格检查
flake8 .

# 类型检查
mypy .
```

## 部署指南

### Docker部署（推荐）

```bash
# 1. 克隆仓库
git clone <repository-url>
cd HongYiXun_Backend

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件,修改生产环境配置

# 3. 使用部署脚本
./deploy.sh install       # 初始化部署环境
./deploy.sh start prod    # 启动生产环境
./deploy.sh status        # 查看服务状态
./deploy.sh health        # 健康检查

# 4. 查看日志
./deploy.sh logs app
./deploy.sh logs nginx
```

### 手动部署（传统方式）

```bash
# 1. 安装Python和依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 配置环境变量（可选）
export DATABASE_URL=<your-database-url>
export CORS_ORIGINS=https://your-domain.com
export POSTGRES_PASSWORD=<your-password>

# 3. 启动服务（使用进程管理器）
# 使用 systemd
sudo cp deployment/openharmony.service /etc/systemd/system/
sudo systemctl start openharmony
sudo systemctl enable openharmony

# 或使用 supervisor
sudo cp deployment/openharmony.conf /etc/supervisor/conf.d/
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start openharmony
```

### Nginx反向代理配置

参考 `nginx/conf.d/openharmony.conf`,关键配置:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 性能优化建议

1. **数据库优化**
   - 为常用查询字段添加索引
   - 使用连接池（PostgreSQL）
   - 定期清理旧数据

2. **缓存优化**
   - 考虑使用Redis替代内存缓存
   - 实现分级缓存策略
   - 添加缓存预热机制

3. **API优化**
   - 使用异步数据库驱动
   - 实现响应压缩（Gzip）
   - 添加CDN支持静态资源

4. **爬虫优化**
   - 实现增量更新策略
   - 添加代理池支持
   - 优化请求频率和并发数

## 故障排查

### 服务启动失败

```bash
# 检查端口占用
lsof -i :8001
netstat -tuln | grep 8001

# 检查日志
tail -f logs/error_*.log
docker-compose logs app

# 检查环境变量
python -c "from core.config import settings; print(settings)"
```

### 爬虫失败

```bash
# 检查网络连接
curl -I https://www.openharmony.cn

# 手动触发爬虫测试
python test_banner_crawler.py
python test_banner_quick.py

# 查看爬虫日志
grep "Crawler" logs/app_*.log
```

### 数据库问题

```bash
# SQLite检查
sqlite3 data/openharmony_news.db ".tables"
sqlite3 data/openharmony_news.db "SELECT COUNT(*) FROM news_articles;"

# PostgreSQL检查
docker-compose exec postgres psql -U postgres -d openharmony_news
\dt                    # 列出所有表
SELECT COUNT(*) FROM news_articles;
```

## 常见问题（FAQ）

**Q: 为什么服务启动后看不到数据？**

A: 服务启动时会在后台线程执行初始爬取,需要等待几分钟。可以通过 `/health` 端点查看缓存状态。

**Q: 如何手动触发数据更新？**

A: 直接调用 `POST /api/news/crawl` 或 `POST /api/banner/crawl` 端点即可。

**Q: CORS错误如何解决？**

A: 在 `.env` 文件中设置 `CORS_ORIGINS=https://your-frontend-domain.com`,不要使用 `*`。

**Q: Docker容器中Selenium失败怎么办？**

A: 设置 `BANNER_USE_ENHANCED=false` 使用传统爬虫,或增加 `shm_size: 1g` 配置。

**Q: 如何查看详细错误信息？**

A: 查看日志文件 `logs/error_*.log` 或使用 `docker-compose logs -f app`。

**Q: 生产环境推荐配置？**

A:
- 使用PostgreSQL数据库
- 启用HTTPS（SSL/TLS）
- 配置CORS为具体域名（不要使用 `*`）
- 使用Nginx反向代理
- 配置防火墙规则
- 定期备份数据库
- 考虑添加API认证和速率限制

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议！

### 提交Issue

- 使用清晰的标题描述问题
- 提供复现步骤
- 包含错误日志和环境信息
- 标注问题类型（Bug/功能请求/文档改进）

### 提交Pull Request

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交代码 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范

- 遵循PEP 8代码风格
- 添加必要的注释和文档字符串
- 编写单元测试（如适用）
- 更新相关文档

## 安全问题报告

如发现安全漏洞,请通过项目 Issues 报告,或联系项目维护者。

**注意**: 本项目当前为开发阶段,部分安全功能未实现。详细的安全状况和改进建议请参考 `SECURITY_AUDIT_REPORT.md`。

## 许可证

MIT License

Copyright (c) 2025 NowInOpenHarmony

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## 免责声明

本软件按"原样"提供,不提供任何形式的明示或暗示保证。使用本软件的风险由用户自行承担。

请遵守相关法律法规和网站服务条款:
- 遵守robots.txt协议
- 合理控制爬取频率
- 不用于商业目的（除非获得授权）
- 尊重版权和知识产权

## 联系方式

- 项目主页: https://github.com/your-username/HongYiXun_Backend
- 文档: https://your-docs-site.com
- 问题反馈: https://github.com/your-username/HongYiXun_Backend/issues

## 致谢

感谢以下开源项目:
- FastAPI - 现代、快速的Web框架
- BeautifulSoup - HTML/XML解析库
- Selenium - 浏览器自动化工具
- APScheduler - 任务调度库
- Uvicorn - ASGI服务器

---

**最后更新**: 2025-11-16
**版本**: 2.0.0
**维护状态**: 积极维护中
