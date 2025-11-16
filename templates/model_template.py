"""
YourDataSource 数据模型模板

功能说明:
- 定义 YourDataSource 特有的数据模型
- 如果与现有 NewsArticle 模型兼容，可以直接使用 models/news.py
- 如果需要额外字段，可以在此扩展

使用步骤:
1. 评估是否需要自定义模型，如果与 NewsArticle 兼容则无需此文件
2. 如需自定义，复制此文件到 models/ 目录
3. 重命名为 yourdatasource.py
4. 全局替换 YourDataSource -> 你的数据源名称
5. 添加特定字段和验证逻辑
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


# ============= Option 1: 使用现有模型 =============
# 如果你的数据源与现有 NewsArticle 兼容，直接导入使用:
#
# from models.news import NewsArticle, NewsListResponse, NewsArticleResponse
#
# 现有字段:
# - id: int
# - title: str
# - url: str
# - summary: str (可选)
# - content: str (可选)
# - image_url: str (可选)
# - publish_date: datetime (可选)
# - source: str
# - created_at: datetime
# ================================================


# ============= Option 2: 扩展模型 =============
# 如果需要额外字段，可以扩展模型

class YourDataSourceArticle(BaseModel):
    """
    YourDataSource 文章模型（扩展版）

    继承自基础新闻模型，添加特定字段
    """
    # 基础字段（与 NewsArticle 相同）
    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=500, description="文章标题")
    url: str = Field(..., description="文章URL")
    summary: Optional[str] = Field(None, max_length=1000, description="文章摘要")
    content: Optional[str] = Field(None, description="文章正文")
    image_url: Optional[str] = Field(None, description="封面图片URL")
    publish_date: Optional[datetime] = Field(None, description="发布时间")
    source: str = Field(default="yourdatasource", description="数据源标识")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    # TODO: 添加你的特定字段
    # 示例: 文章分类
    category: Optional[str] = Field(None, max_length=100, description="文章分类")

    # 示例: 作者信息
    author: Optional[str] = Field(None, max_length=100, description="作者")

    # 示例: 阅读量
    view_count: Optional[int] = Field(None, ge=0, description="阅读量")

    # 示例: 标签列表
    tags: Optional[List[str]] = Field(None, description="文章标签")

    # 示例: 是否置顶
    is_pinned: Optional[bool] = Field(False, description="是否置顶")

    # 示例: 外部ID（用于对接第三方系统）
    external_id: Optional[str] = Field(None, max_length=100, description="外部系统ID")

    class Config:
        from_attributes = True  # 支持从 ORM 对象转换
        json_schema_extra = {
            "example": {
                "title": "YourDataSource 示例文章标题",
                "url": "https://www.yourdatasource.com/article/123",
                "summary": "这是一篇关于...的文章",
                "content": "文章正文内容...",
                "image_url": "https://www.yourdatasource.com/images/123.jpg",
                "publish_date": "2024-01-15T10:30:00",
                "source": "yourdatasource",
                "category": "技术",
                "author": "张三",
                "view_count": 1234,
                "tags": ["标签1", "标签2"],
                "is_pinned": False
            }
        }

    @validator('url')
    def validate_url(cls, v):
        """验证 URL 格式"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL 必须以 http:// 或 https:// 开头')
        return v

    @validator('tags')
    def validate_tags(cls, v):
        """验证标签列表"""
        if v and len(v) > 10:
            raise ValueError('标签数量不能超过10个')
        return v


class YourDataSourceArticleResponse(BaseModel):
    """
    YourDataSource 文章响应模型

    用于 API 返回，可以隐藏部分内部字段
    """
    id: int
    title: str
    url: str
    summary: Optional[str] = None
    image_url: Optional[str] = None
    publish_date: Optional[datetime] = None
    source: str

    # TODO: 添加你的特定字段
    category: Optional[str] = None
    author: Optional[str] = None
    view_count: Optional[int] = None
    tags: Optional[List[str]] = None
    is_pinned: Optional[bool] = None

    class Config:
        from_attributes = True


class YourDataSourceListResponse(BaseModel):
    """
    YourDataSource 文章列表响应模型

    包含分页信息
    """
    total: int = Field(..., description="总记录数")
    page: int = Field(..., ge=1, description="当前页码")
    page_size: int = Field(..., ge=1, le=100, description="每页数量")
    items: List[YourDataSourceArticleResponse] = Field(..., description="文章列表")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 100,
                "page": 1,
                "page_size": 20,
                "items": [
                    {
                        "id": 1,
                        "title": "示例文章",
                        "url": "https://www.yourdatasource.com/article/1",
                        "summary": "文章摘要",
                        "image_url": "https://www.yourdatasource.com/images/1.jpg",
                        "publish_date": "2024-01-15T10:30:00",
                        "source": "yourdatasource",
                        "category": "技术",
                        "author": "张三"
                    }
                ]
            }
        }


# ============= Option 3: 完全自定义模型 =============
# 如果你的数据源结构完全不同，可以完全自定义

class YourDataSourceCustomModel(BaseModel):
    """
    完全自定义的数据模型

    适用于与新闻文章结构完全不同的数据源
    """
    # TODO: 定义你的字段
    id: Optional[int] = None
    name: str = Field(..., description="名称")
    description: str = Field(..., description="描述")
    data: dict = Field(..., description="数据内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")

    class Config:
        from_attributes = True


# ============= 数据库模型 (SQLAlchemy) =============
# 如果需要自定义数据库表结构，可以在这里定义

"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class YourDataSourceArticleDB(Base):
    \"\"\"
    YourDataSource 文章数据库模型
    \"\"\"
    __tablename__ = "yourdatasource_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    url = Column(String(1000), nullable=False, unique=True, index=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    image_url = Column(String(1000), nullable=True)
    publish_date = Column(DateTime, nullable=True, index=True)
    source = Column(String(50), nullable=False, default="yourdatasource", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # TODO: 添加你的特定字段
    category = Column(String(100), nullable=True, index=True)
    author = Column(String(100), nullable=True)
    view_count = Column(Integer, default=0)
    tags = Column(JSON, nullable=True)  # 存储为 JSON 数组
    is_pinned = Column(Boolean, default=False, index=True)
    external_id = Column(String(100), nullable=True, unique=True, index=True)

    def __repr__(self):
        return f"<YourDataSourceArticle(id={self.id}, title={self.title})>"
"""


# ============= 使用建议 =============
# 1. 如果与 NewsArticle 兼容，直接使用 models/news.py，无需创建新模型
# 2. 如果只需要少量额外字段，使用 Option 2 扩展模型
# 3. 如果数据结构完全不同，使用 Option 3 完全自定义
# 4. 记得在 core/database.py 中创建数据库表（如果使用自定义表）
# ===================================
