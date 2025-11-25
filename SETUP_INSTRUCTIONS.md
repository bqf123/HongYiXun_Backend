# 华为开发者博客爬虫 - 安装和测试指南

## 📋 当前状态

✅ 已完成的工作：
1. 创建了华为开发者博客爬虫 (`services/huawei_developer_blog_crawler.py`)
2. 集成到news_service中，支持自动更新
3. 支持category分类查询（`Huawei Developer`）
4. 支持page和page_size分页功能
5. 创建了完整的测试脚本

## 🚀 快速开始指南

### 方法一：直接启动服务器测试（推荐）

由于爬虫需要一些时间来初始化和爬取数据，最简单的方法是直接启动服务器：

#### 步骤1：启动服务器

```bash
python run.py
```

等待看到：
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

#### 步骤2：等待初始数据加载

服务器启动后会在后台自动爬取数据。你可以：

1. **查看日志**：观察终端输出，会显示爬取进度
2. **访问API文档**：打开浏览器访问 `http://localhost:8001/docs`
3. **检查状态**：访问 `http://localhost:8001/api/news/status/info`

#### 步骤3：测试API接口

打开新的终端窗口，运行：

```bash
# 等待几分钟后，测试获取所有新闻
curl "http://localhost:8001/api/news/?page=1&page_size=10"

# 测试category分类查询
curl "http://localhost:8001/api/news/?category=Huawei%20Developer&page=1&page_size=10"

# 测试分页
curl "http://localhost:8001/api/news/?page=2&page_size=5"
```

或者使用浏览器访问Swagger UI进行测试：
```
http://localhost:8001/docs
```

### 方法二：运行自动化测试

如果服务器已经运行并且有数据，可以运行完整的测试脚本：

```bash
python test_huawei_developer_integration.py
```

这个脚本会自动测试：
- ✅ API健康检查
- ✅ 获取所有新闻
- ✅ Category分类查询
- ✅ 分页功能
- ✅ 组合过滤
- ✅ 搜索功能

## 📡 API使用示例

### 1. 获取所有新闻（包含华为开发者博客）

**请求：**
```bash
GET http://localhost:8001/api/news/?page=1&page_size=20
```

**响应：**
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
      "source": "Huawei Developer"
    }
  ],
  "total": 156,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_prev": false
}
```

### 2. 按Category查询华为开发者博客

**请求：**
```bash
GET http://localhost:8001/api/news/?category=Huawei Developer&page=1&page_size=10
```

**说明：**
- 只返回 `category="Huawei Developer"` 的文章
- 支持分页参数

### 3. 分页查询

**请求：**
```bash
# 第1页，每页10条
GET http://localhost:8001/api/news/?page=1&page_size=10

# 第2页，每页20条
GET http://localhost:8001/api/news/?page=2&page_size=20
```

**响应字段说明：**
- `total`: 总文章数
- `page`: 当前页码（从1开始）
- `page_size`: 每页数量
- `has_next`: 是否有下一页
- `has_prev`: 是否有上一页

### 4. 组合查询（分类+分页）

**请求：**
```bash
GET http://localhost:8001/api/news/?category=Huawei Developer&page=1&page_size=10
```

### 5. 搜索功能

**请求：**
```bash
# 搜索包含"HarmonyOS"的文章
GET http://localhost:8001/api/news/?search=HarmonyOS&page=1&page_size=10

# 搜索+分类
GET http://localhost:8001/api/news/?search=开发&category=Huawei Developer
```

## 🔧 如果遇到问题

### 问题1：服务器启动失败

**解决方案：**
```bash
# 检查端口是否被占用
netstat -ano | findstr :8001

# 如果被占用，可以修改端口
# 编辑 main.py，将 port=8001 改为其他端口
```

### 问题2：没有数据返回

**原因：** 首次启动需要时间爬取数据

**解决方案：**
1. 查看服务器日志，确认爬虫是否在运行
2. 等待3-5分钟
3. 访问 `/api/news/status/info` 查看状态
4. 如果状态是 `preparing`，说明正在爬取，请继续等待

### 问题3：爬虫运行缓慢

**原因：** 华为开发者网站是动态网站，需要使用Selenium

**说明：**
- 首次爬取可能需要5-10分钟
- 后续会使用缓存，响应速度很快
- 定时任务每6小时自动更新一次

### 问题4：Chrome WebDriver错误

**解决方案：**
```bash
# 确保已安装Chrome浏览器
# 安装webdriver-manager（已在requirements.txt中）
pip install webdriver-manager

# 如果还有问题，手动下载ChromeDriver
# 访问: https://chromedriver.chromium.org/downloads
# 下载对应版本并放到系统PATH中
```

## 📊 数据结构说明

### Category分类

项目支持以下分类：
- `Huawei Developer` - 华为开发者博客（新增）
- `官方动态` - OpenHarmony官网新闻
- `技术博客` - OpenHarmony技术博客

### 文章字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 唯一标识 |
| title | string | 文章标题 |
| date | string | 发布日期 (YYYY-MM-DD) |
| url | string | 原文链接 |
| content | array | 内容块数组（文本、图片等） |
| category | string | 分类 |
| source | string | 来源 |
| summary | string | 摘要 |

### 内容块类型

```json
{
  "type": "text",      // 文本块
  "value": "内容..."
}

{
  "type": "image",     // 图片块
  "value": "https://..."
}
```

## 🎯 测试检查清单

在测试时，请验证以下功能：

- [ ] 服务器能正常启动
- [ ] 访问 `/docs` 可以看到API文档
- [ ] 访问 `/api/news/` 能获取新闻列表
- [ ] 使用 `category=Huawei Developer` 能过滤华为开发者博客
- [ ] 使用 `page` 和 `page_size` 能正确分页
- [ ] 返回的文章包含 `content` 数组
- [ ] 文章内容包含文本和图片URL
- [ ] 没有包含 `operations` 标签以下的内容

## 📝 文件说明

### 新增文件

1. **services/huawei_developer_blog_crawler.py**
   - 华为开发者博客爬虫
   - 使用Selenium处理动态网站
   - 支持随机延迟防反爬

2. **test_huawei_developer_integration.py**
   - 完整的集成测试脚本
   - 测试所有API功能

3. **quick_test_crawler.py**
   - 快速测试爬虫功能
   - 不需要启动服务器

4. **start_test_server.py**
   - 辅助启动脚本
   - 自动检查服务器状态

5. **HUAWEI_DEVELOPER_BLOG_GUIDE.md**
   - 详细使用指南
   - API接口文档

### 修改文件

1. **services/news_service.py**
   - 添加了 `HUAWEI_DEVELOPER` 枚举
   - 集成了华为开发者博客爬虫
   - 支持批量写入缓存

2. **requirements.txt**
   - 添加了 `webdriver-manager==4.0.1`

## 🌐 使用浏览器测试

### Swagger UI

访问 `http://localhost:8001/docs`，你可以：

1. 查看所有API接口
2. 直接在浏览器中测试
3. 查看请求/响应格式

### 测试步骤

1. 展开 `GET /api/news/`
2. 点击 "Try it out"
3. 设置参数：
   - page: 1
   - page_size: 10
   - category: Huawei Developer
4. 点击 "Execute"
5. 查看响应结果

## 📞 需要帮助？

如果遇到问题：

1. **查看日志文件**
   ```
   logs/openharmony_api_YYYYMMDD.log
   logs/error_YYYYMMDD.log
   ```

2. **检查服务状态**
   ```bash
   curl http://localhost:8001/api/news/status/info
   ```

3. **查看详细文档**
   - `HUAWEI_DEVELOPER_BLOG_GUIDE.md` - 详细使用指南
   - `API_DATA_STRUCTURE.md` - API数据结构文档
   - `COLLABORATION_GUIDE.md` - 协作指南

## ✅ 总结

现在你可以：

1. ✅ 启动服务器，自动爬取华为开发者博客
2. ✅ 使用API按category分类查询
3. ✅ 使用page和page_size进行分页
4. ✅ 组合使用分类、分页、搜索功能
5. ✅ 查看详细的API响应结果

**下一步：**
```bash
# 1. 启动服务器
python run.py

# 2. 等待几分钟让数据加载

# 3. 在新终端测试API
curl "http://localhost:8001/api/news/?category=Huawei%20Developer&page=1&page_size=10"

# 或者访问浏览器
# http://localhost:8001/docs
```

祝测试顺利！🎉
