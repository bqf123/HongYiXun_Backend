# 🚀 快速开始 - 华为开发者博客爬虫测试

## 一步一步操作指南

### 第一步：启动服务器

打开终端，运行：

```bash
python run.py
```

**等待看到这个信息：**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**注意：** 
- 首次启动会在后台自动爬取数据
- 这个过程可能需要3-5分钟
- 服务器会立即可用，但数据会逐步加载

---

### 第二步：打开浏览器测试

在浏览器中打开：

```
http://localhost:8001/docs
```

你会看到Swagger API文档界面。

---

### 第三步：测试API接口

#### 测试1：获取所有新闻

1. 在Swagger UI中找到 `GET /api/news/`
2. 点击展开
3. 点击 "Try it out"
4. 设置参数：
   - page: `1`
   - page_size: `10`
5. 点击 "Execute"
6. 查看响应结果

#### 测试2：按Category查询华为开发者博客

1. 在Swagger UI中找到 `GET /api/news/`
2. 点击 "Try it out"
3. 设置参数：
   - category: `Huawei Developer`
   - page: `1`
   - page_size: `10`
4. 点击 "Execute"
5. 查看响应结果

#### 测试3：测试分页功能

1. 在Swagger UI中找到 `GET /api/news/`
2. 点击 "Try it out"
3. 设置参数：
   - page: `2`
   - page_size: `5`
4. 点击 "Execute"
5. 查看响应结果，注意 `has_next` 和 `has_prev` 字段

---

### 第四步：使用命令行测试（可选）

打开新的终端窗口，运行：

```bash
# 测试1：获取所有新闻
curl "http://localhost:8001/api/news/?page=1&page_size=10"

# 测试2：按category查询
curl "http://localhost:8001/api/news/?category=Huawei%20Developer&page=1&page_size=10"

# 测试3：测试分页
curl "http://localhost:8001/api/news/?page=2&page_size=5"

# 测试4：查看服务状态
curl "http://localhost:8001/api/news/status/info"
```

---

### 第五步：运行自动化测试（可选）

如果服务器已经运行并且有数据，可以运行完整测试：

```bash
python test_huawei_developer_integration.py
```

这会自动测试所有功能并显示结果。

---

## 📊 预期结果

### API响应示例

```json
{
  "articles": [
    {
      "id": "huawei_dev_xxx",
      "title": "文章标题",
      "date": "2024-01-15",
      "url": "https://developer.huawei.com/...",
      "content": [
        {
          "type": "text",
          "value": "文章内容..."
        },
        {
          "type": "image",
          "value": "https://..."
        }
      ],
      "category": "Huawei Developer",
      "source": "Huawei Developer",
      "summary": "文章摘要..."
    }
  ],
  "total": 156,
  "page": 1,
  "page_size": 10,
  "has_next": true,
  "has_prev": false
}
```

### 验证要点

✅ 检查以下内容：

1. **Category字段**
   - 华为开发者博客的文章 `category` 应该是 `"Huawei Developer"`
   - 可以通过 `category` 参数过滤

2. **分页功能**
   - `page` 和 `page_size` 参数正常工作
   - `has_next` 和 `has_prev` 正确显示
   - `total` 显示总文章数

3. **内容结构**
   - `content` 是数组格式
   - 包含 `text` 和 `image` 类型的块
   - 图片URL是完整的HTTPS链接
   - 没有包含 `operations` 标签的内容

---

## ❓ 常见问题

### Q: 服务器启动后没有数据？

**A:** 首次启动需要时间爬取数据，请：
1. 等待3-5分钟
2. 查看终端日志，确认爬虫在运行
3. 访问 `http://localhost:8001/api/news/status/info` 查看状态

### Q: 如何知道数据已经加载完成？

**A:** 访问状态接口：
```bash
curl "http://localhost:8001/api/news/status/info"
```

如果 `status` 是 `"ready"` 并且 `cache_count` 大于0，说明数据已加载。

### Q: Category查询返回空结果？

**A:** 请确保：
1. 数据已经加载完成
2. Category名称正确：`Huawei Developer`（区分大小写）
3. URL编码正确：空格用 `%20` 或 `+`

### Q: 如何停止服务器？

**A:** 在运行服务器的终端按 `Ctrl+C`

---

## 📚 更多文档

- **详细使用指南**: `HUAWEI_DEVELOPER_BLOG_GUIDE.md`
- **安装说明**: `SETUP_INSTRUCTIONS.md`
- **API数据结构**: `API_DATA_STRUCTURE.md`
- **协作指南**: `COLLABORATION_GUIDE.md`

---

## ✅ 完成检查清单

测试完成后，请确认：

- [ ] 服务器能正常启动
- [ ] 可以访问 API 文档 (`/docs`)
- [ ] 可以获取新闻列表
- [ ] Category 过滤功能正常
- [ ] 分页功能正常
- [ ] 文章包含正确的内容结构
- [ ] 图片URL是完整的
- [ ] 没有包含不需要的内容

---

## 🎉 完成！

如果所有测试都通过，恭喜你！华为开发者博客爬虫已经成功集成到项目中。

**现在你可以：**
- ✅ 通过API获取华为开发者博客文章
- ✅ 使用category参数过滤文章
- ✅ 使用page和page_size进行分页
- ✅ 组合使用各种查询参数

祝使用愉快！🚀
