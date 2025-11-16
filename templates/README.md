# 新爬虫开发模板

本目录提供了开发新爬虫的完整模板代码,帮助团队成员快速开始开发。

## 📁 模板文件说明

```
templates/
├── crawler_template.py          # 爬虫类模板
├── api_template.py              # API路由模板
├── model_template.py            # 数据模型模板
└── README.md                    # 本文件
```

## 🚀 快速开始

### 步骤1: 复制模板文件

```bash
# 假设你要开发 "华为新闻" 爬虫

# 1. 复制爬虫模板
cp templates/crawler_template.py services/huawei_news_crawler.py

# 2. 复制API模板
cp templates/api_template.py api/huawei_news.py

# 3. 复制模型模板(可选)
cp templates/model_template.py models/huawei_news.py
```

### 步骤2: 全局替换占位符

在复制的文件中,使用编辑器的"查找替换"功能:

| 占位符 | 替换为 | 示例 |
|--------|--------|------|
| `YourDataSource` | 你的数据源名称(驼峰) | `HuaweiNews` |
| `your_datasource` | 你的数据源名称(下划线) | `huawei_news` |
| `Your Data Source` | 你的数据源名称(中文) | `华为新闻` |
| `https://example.com` | 目标网站URL | `https://www.huawei.com/cn/news` |

**VS Code 快捷键**: `Ctrl+H` (Windows) / `Cmd+H` (Mac)

### 步骤3: 实现业务逻辑

根据你的目标网站,填充以下方法:

```python
# services/huawei_news_crawler.py

def fetch_list(self, page: int = 1) -> List[Dict]:
    """实现:如何获取列表页数据"""
    pass

def fetch_detail(self, detail_url: str) -> Optional[Dict]:
    """实现:如何获取详情页数据"""
    pass

def save_to_database(self, data: List[Dict]) -> int:
    """实现:如何保存到数据库"""
    pass
```

### 步骤4: 测试爬虫

```bash
# 运行测试
python services/huawei_news_crawler.py

# 预期输出
# 爬取完成: {'total': 20, 'saved': 20, 'status': 'success'}
```

### 步骤5: 注册API路由

在 `main.py` 中注册你的API:

```python
# main.py
from api import news, banner, huawei_news  # 添加你的导入

app = FastAPI(title="NowInOpenHarmony API")

# 注册路由
app.include_router(news.router)
app.include_router(banner.router)
app.include_router(huawei_news.router)  # 添加这行
```

### 步骤6: 测试API

```bash
# 启动服务
python run.py

# 访问 API 文档
# http://localhost:8001/docs

# 测试你的API
curl http://localhost:8001/api/huawei-news/
curl -X POST http://localhost:8001/api/huawei-news/crawl
```

## 📝 开发指南

### 数据库表设计建议

```python
# 表名: <数据源>_<数据类型>
# 例如: huawei_news_articles

CREATE TABLE IF NOT EXISTS huawei_news_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,                    -- 标题(必需)
    url TEXT UNIQUE NOT NULL,               -- URL(必需,唯一)
    content TEXT,                           -- 内容
    summary TEXT,                           -- 摘要
    author TEXT,                            -- 作者
    category TEXT,                          -- 分类
    tags TEXT,                              -- 标签(JSON数组字符串)
    cover_image TEXT,                       -- 封面图片URL
    view_count INTEGER DEFAULT 0,          -- 浏览量
    publish_time DATETIME,                  -- 发布时间
    crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 爬取时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_url ON huawei_news_articles(url);
CREATE INDEX IF NOT EXISTS idx_publish_time ON huawei_news_articles(publish_time DESC);
CREATE INDEX IF NOT EXISTS idx_category ON huawei_news_articles(category);
```

### 爬虫最佳实践

#### 1. 遵守 robots.txt

```python
# 在爬虫开始前检查
from urllib.robotparser import RobotFileParser

rp = RobotFileParser()
rp.set_url("https://example.com/robots.txt")
rp.read()

if not rp.can_fetch("*", "https://example.com/page"):
    logger.warning("该页面不允许爬取")
    return
```

#### 2. 添加请求延迟

```python
import time
import random

# 在请求之间添加随机延迟
time.sleep(random.uniform(1, 3))  # 1-3秒随机延迟
```

#### 3. 设置合理的 User-Agent

```python
self.session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
})
```

#### 4. 异常处理

```python
def fetch_with_retry(self, url: str, max_retries: int = 3) -> Optional[str]:
    """带重试的请求"""
    for i in range(max_retries):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"请求失败(第{i+1}次): {e}")
            if i < max_retries - 1:
                time.sleep(2 ** i)  # 指数退避
            else:
                logger.error(f"请求最终失败: {url}")
                return None
```

#### 5. 数据去重

```python
def is_exists(self, url: str) -> bool:
    """检查URL是否已存在"""
    from core.database import execute_query

    result = execute_query(
        "SELECT COUNT(*) as count FROM your_table WHERE url = ?",
        (url,)
    )
    return result[0]['count'] > 0 if result else False
```

### API 设计建议

#### 1. 统一的响应格式

```python
# 成功响应
{
    "code": 200,
    "message": "success",
    "data": {
        "total": 100,
        "page": 1,
        "page_size": 20,
        "items": [...]
    }
}

# 错误响应
{
    "code": 500,
    "message": "Internal server error",
    "data": None
}
```

#### 2. 分页参数验证

```python
@router.get("/")
async def get_list(
    page: int = Query(1, ge=1, le=1000, description="页码,1-1000"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量,1-100"),
):
    # 计算偏移量
    offset = (page - 1) * page_size
    ...
```

#### 3. 搜索功能

```python
@router.get("/search")
async def search(
    keyword: str = Query(..., min_length=1, max_length=100),
    category: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """
    搜索功能
    - keyword: 搜索关键词(必需)
    - category: 分类筛选(可选)
    - start_date: 开始日期(可选,格式:YYYY-MM-DD)
    - end_date: 结束日期(可选)
    """
    pass
```

## 🎯 完整示例

假设你要爬取 "华为开发者新闻":

### 1. 爬虫文件 (services/huawei_dev_news_crawler.py)

```python
"""
华为开发者新闻爬虫
目标网站: https://developer.huawei.com/consumer/cn/news/
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import time
import random

import requests
from bs4 import BeautifulSoup

from core.database import execute_query, execute_update

logger = logging.getLogger(__name__)


class HuaweiDevNewsCrawler:
    """华为开发者新闻爬虫"""

    BASE_URL = "https://developer.huawei.com/consumer/cn/news"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS huawei_dev_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            summary TEXT,
            cover_image TEXT,
            publish_time TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        execute_update(create_table_sql)
        execute_update("CREATE INDEX IF NOT EXISTS idx_url ON huawei_dev_news(url)")

    def fetch_list(self, page: int = 1) -> List[Dict]:
        """获取新闻列表"""
        try:
            url = f"{self.BASE_URL}?page={page}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.select('.news-item')  # 根据实际页面结构调整

            results = []
            for item in news_items:
                try:
                    title = item.select_one('.title').get_text(strip=True)
                    link = item.select_one('a')['href']
                    summary = item.select_one('.summary').get_text(strip=True)

                    results.append({
                        'title': title,
                        'url': link if link.startswith('http') else self.BASE_URL + link,
                        'summary': summary,
                    })
                except Exception as e:
                    logger.error(f"解析新闻项失败: {e}")

            logger.info(f"获取到 {len(results)} 条新闻")
            return results

        except Exception as e:
            logger.error(f"获取新闻列表失败: {e}")
            return []

    def save_to_database(self, data: List[Dict]) -> int:
        """保存到数据库"""
        count = 0
        for item in data:
            try:
                # 检查是否已存在
                exists = execute_query(
                    "SELECT COUNT(*) as cnt FROM huawei_dev_news WHERE url = ?",
                    (item['url'],)
                )

                if exists and exists[0]['cnt'] > 0:
                    continue

                # 插入数据
                execute_update(
                    """
                    INSERT INTO huawei_dev_news (title, url, summary, cover_image, publish_time)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        item['title'],
                        item['url'],
                        item.get('summary', ''),
                        item.get('cover_image', ''),
                        item.get('publish_time', ''),
                    )
                )
                count += 1

            except Exception as e:
                logger.error(f"保存数据失败: {e}")

        logger.info(f"成功保存 {count} 条新数据")
        return count


def crawl_all() -> Dict:
    """执行爬取任务"""
    crawler = HuaweiDevNewsCrawler()

    all_data = []
    for page in range(1, 6):
        data = crawler.fetch_list(page)
        all_data.extend(data)
        time.sleep(random.uniform(1, 2))  # 随机延迟

    saved = crawler.save_to_database(all_data)

    return {
        'total': len(all_data),
        'saved': saved,
        'status': 'success'
    }


if __name__ == "__main__":
    result = crawl_all()
    print(f"爬取完成: {result}")
```

### 2. API文件 (api/huawei_dev_news.py)

```python
"""华为开发者新闻 API"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from core.database import execute_query
from services.huawei_dev_news_crawler import crawl_all

router = APIRouter(prefix="/api/huawei-dev-news", tags=["华为开发者新闻"])


@router.get("/")
async def get_news_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取华为开发者新闻列表"""
    try:
        offset = (page - 1) * page_size

        # 查询总数
        total_result = execute_query("SELECT COUNT(*) as total FROM huawei_dev_news")
        total = total_result[0]['total'] if total_result else 0

        # 查询数据
        items = execute_query(
            """
            SELECT id, title, url, summary, cover_image, publish_time, created_at
            FROM huawei_dev_news
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (page_size, offset)
        )

        return {
            "code": 200,
            "message": "success",
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": items or []
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crawl")
async def trigger_crawl():
    """手动触发爬取"""
    try:
        result = crawl_all()
        return {
            "code": 200,
            "message": "爬取完成",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. 在 main.py 中注册

```python
# main.py
from api import news, banner, huawei_dev_news

app = FastAPI(title="NowInOpenHarmony API")

app.include_router(news.router)
app.include_router(banner.router)
app.include_router(huawei_dev_news.router)  # 新增
```

## ⚠️ 注意事项

### 法律和道德

1. **遵守 robots.txt**: 检查目标网站的爬虫协议
2. **控制频率**: 不要对网站造成压力
3. **尊重版权**: 注明数据来源
4. **用户协议**: 遵守网站的使用条款

### 技术限制

1. **反爬虫机制**: 有些网站有验证码、IP限制等
2. **动态内容**: 需要使用 Selenium 的情况
3. **数据结构**: 网站改版可能导致爬虫失效
4. **字符编码**: 注意处理各种编码问题

### 资源管理

1. **内存使用**: 大量数据时注意分批处理
2. **网络连接**: 使用连接池,及时关闭连接
3. **数据库连接**: 避免连接泄漏
4. **磁盘空间**: 定期清理旧数据

## 📚 参考资料

- [Requests 文档](https://docs.python-requests.org/)
- [BeautifulSoup 文档](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Selenium 文档](https://selenium-python.readthedocs.io/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [robots.txt 规范](https://www.robotstxt.org/)

## 🆘 获取帮助

遇到问题?

1. 查看 `COLLABORATION_GUIDE.md` 协作指南
2. 查看现有爬虫代码作为参考
3. 在团队群里提问
4. 联系架构负责人

祝开发顺利! 🚀
