# 华为开发者博客爬虫集成指南

## 📋 概述

本指南介绍如何使用新集成的华为开发者博客爬虫，包括：
- 爬虫功能说明
- 本地测试步骤
- API接口使用
- Category分类查询
- 分页功能使用

## 🎯 功能特性

### 爬虫功能
- ✅ 自动访问华为开发者博客推荐页
- ✅ 点击"最新"选项获取最新文章
- ✅ 遍历scroll-container列表
- ✅ 模拟用户点击获取文章URL
- ✅ 动态等待页面加载
- ✅ 随机时间间隔防反爬
- ✅ 提取文章标题、日期、正文、图片
- ✅ 自动排除operations标签及以下内容
- ✅ 输出Markdown格式内容
- ✅ 支持category分类（Huawei Developer）

### API功能
- ✅ 支持分页查询（page, page_size）
- ✅ 支持分类过滤（category）
- ✅ 支持关键词搜索（search）
- ✅ 自动集成到定时更新任务

## 🚀 快速开始

### 前置要求

1. **Python环境**
   ```bash
   python --version  # 需要 Python 3.8+
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **Chrome浏览器**
   - 确保已安装Chrome浏览器
   - 或者安装webdriver-manager自动管理驱动：
     ```bash
     pip install webdriver-manager
     ```

### 方法一：使用测试脚本（推荐）

#### 步骤1：启动服务器

打开第一个终端窗口：
```bash
python run.py
```

等待看到以下信息：
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

#### 步骤2：运行测试

打开第二个终端窗口：
```bash
python test_huawei_developer_integration.py
```

测试脚本会自动执行以下测试：
1. ✅ API健康检查
2. ✅ 获取所有新闻
3. ✅ Category分类查询
4. ✅ 分页功能测试
5. ✅ 组合过滤测试
6. ✅ 搜索功能测试

### 方法二：使用辅助启动脚本

```bash
python start_test_server.py
```

这个脚本会：
1. 自动检查服务器是否运行
2. 如果没有运行，自动启动服务器
3. 等待服务器就绪
4. 提示你运行测试脚本

### 方法三：手动测试爬虫

```bash
python services/huawei_developer_blog_crawler.py
```

这会直接运行爬虫，爬取5篇文章并显示结果。

## 📡 API接口使用

### 1. 获取所有新闻（包含华为开发者博客）

```bash
curl "http://localhost:8001/api/news/?page=1&page_size=20"
```

**响应示例：**
```json
{
  "articles": [
    {
      "id": "huawei_dev_xxx",
      "title": "文章标题",
      "date": "2024-01-15",
      "url": "https://developer.huawei.com/...",
      "content": [
        {"type": "text", "value": "文章内容..."},
        {"type": "image", "value": "https://..."}
      ],
      "category": "Huawei Developer",
      "source": "Huawei Developer",
      "summary": "文章摘要..."
    }
  ],
  "total": 156,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_prev": false
}
```

### 2. 按Category分类查询

#### 查询华为开发者博客文章

```bash
curl "http://localhost:8001/api/news/?category=Huawei%20Developer&page=1&page_size=10"
```

#### 查询其他分类

```bash
# 官方动态
curl "http://localhost:8001/api/news/?category=官方动态&page=1&page_size=10"

# 技术博客
curl "http://localhost:8001/api/news/?category=技术博客&page=1&page_size=10"
```

### 3. 分页查询

```bash
# 第1页，每页10条
curl "http://localhost:8001/api/news/?page=1&page_size=10"

# 第2页，每页20条
curl "http://localhost:8001/api/news/?page=2&page_size=20"

# 第3页，每页5条
curl "http://localhost:8001/api/news/?page=3&page_size=5"
```

### 4. 组合查询（分类+分页）

```bash
curl "http://localhost:8001/api/news/?category=Huawei%20Developer&page=1&page_size=10"
```

### 5. 搜索功能

```bash
# 搜索包含"HarmonyOS"的文章
curl "http://localhost:8001/api/news/?search=HarmonyOS&page=1&page_size=10"

# 搜索+分类
curl "http://localhost:8001/api/news/?search=开发&category=Huawei%20Developer&page=1&page_size=10"
```

### 6. 手动触发爬取

```bash
# 爬取所有来源（包括华为开发者博客）
curl -X POST "http://localhost:8001/api/news/crawl?source=all"

# 仅爬取华为开发者博客
curl -X POST "http://localhost:8001/api/news/crawl?source=huawei_developer"
```

### 7. 查看服务状态

```bash
curl "http://localhost:8001/api/news/status/info"
```

## 🌐 使用浏览器测试

### 访问API文档

打开浏览器访问：
```
http://localhost:8001/docs
```

在Swagger UI中可以：
1. 查看所有API接口
2. 直接测试接口
3. 查看请求/响应格式

### 测试示例

1. **获取所有新闻**
   - 展开 `GET /api/news/`
   - 点击 "Try it out"
   - 设置参数：
     - page: 1
     - page_size: 10
   - 点击 "Execute"

2. **按分类查询**
   - 展开 `GET /api/news/`
   - 点击 "Try it out"
   - 设置参数：
     - category: Huawei Developer
     - page: 1
     - page_size: 10
   - 点击 "Execute"

## 📊 数据结构说明

### Category分类

项目支持以下分类：
- `Huawei Developer` - 华为开发者博客（新增）
- `官方动态` - OpenHarmony官网新闻
- `技术博客` - OpenHarmony技术博客

### 文章数据结构

```json
{
  "id": "huawei_dev_xxx",           // 唯一标识
  "title": "文章标题",               // 标题
  "date": "2024-01-15",             // 发布日期
  "url": "https://...",             // 原文链接
  "content": [                      // 内容块数组
    {
      "type": "text",               // 文本块
      "value": "文章内容..."
    },
    {
      "type": "image",              // 图片块
      "value": "https://..."
    }
  ],
  "category": "Huawei Developer",   // 分类
  "source": "Huawei Developer",     // 来源
  "summary": "文章摘要...",          // 摘要
  "created_at": "2024-01-15T10:30:00",  // 创建时间
  "updated_at": "2024-01-15T10:30:00"   // 更新时间
}
```

### 分页响应结构

```json
{
  "articles": [...],      // 文章列表
  "total": 156,          // 总文章数
  "page": 1,             // 当前页码
  "page_size": 20,       // 每页数量
  "has_next": true,      // 是否有下一页
  "has_prev": false      // 是否有上一页
}
```

## 🔧 配置说明

### 爬虫配置

在 `services/huawei_developer_blog_crawler.py` 中可以调整：

```python
# 最大文章数量
max_articles = 20

# 随机延迟范围（秒）
min_seconds = 1
max_seconds = 3

# 最大滚动次数
max_scrolls = 5
```

### 定时任务配置

在 `core/scheduler.py` 中，华为开发者博客会：
- 每6小时自动更新一次
- 每天凌晨2点执行完整爬取

## ❓ 常见问题

### Q1: 爬虫运行失败，提示WebDriver错误

**A:** 请确保：
1. 已安装Chrome浏览器
2. 安装webdriver-manager：
   ```bash
   pip install webdriver-manager
   ```

### Q2: 服务启动后没有数据

**A:** 首次启动需要时间爬取数据，请：
1. 查看日志输出
2. 等待几分钟
3. 访问 `/api/news/status/info` 查看状态

### Q3: 如何只测试华为开发者博客爬虫？

**A:** 运行：
```bash
python services/huawei_developer_blog_crawler.py
```

### Q4: Category查询返回空结果

**A:** 请确保：
1. 服务已完成首次爬取
2. Category名称正确（区分大小写）
3. 使用正确的URL编码（空格用%20）

### Q5: 如何查看爬虫日志？

**A:** 日志文件位于：
```
logs/openharmony_api_YYYYMMDD.log
logs/error_YYYYMMDD.log
```

## 📝 开发说明

### 文件结构

```
services/
├── huawei_developer_blog_crawler.py  # 华为开发者博客爬虫（新增）
├── news_service.py                   # 新闻服务（已更新）
└── ...

api/
├── news.py                           # 新闻API（无需修改）
└── ...

tests/
├── test_huawei_developer_integration.py  # 集成测试（新增）
└── start_test_server.py                  # 启动脚本（新增）
```

### 集成要点

1. **爬虫类** (`HuaweiDeveloperBlogCrawler`)
   - 使用Selenium处理动态网站
   - 实现随机延迟防反爬
   - 自动排除不需要的内容

2. **服务集成** (`NewsService`)
   - 添加 `HUAWEI_DEVELOPER` 枚举
   - 在 `crawl_news` 中添加爬取逻辑
   - 支持批量写入缓存

3. **API接口** (无需修改)
   - 自动支持新的category
   - 分页、搜索功能自动生效

## 🎉 总结

现在你可以：
1. ✅ 使用爬虫自动获取华为开发者博客文章
2. ✅ 通过API按category分类查询
3. ✅ 使用page和page_size进行分页
4. ✅ 组合使用分类、分页、搜索功能
5. ✅ 查看详细的测试结果和API响应

如有问题，请查看日志文件或运行测试脚本获取详细信息。
