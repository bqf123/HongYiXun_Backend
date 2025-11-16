"""
YourDataSource API 路由模板

功能说明:
- 提供 YourDataSource 数据的 RESTful API 接口
- 支持分页、搜索、过滤功能
- 包含手动触发爬虫的管理接口

使用步骤:
1. 复制此文件到 api/ 目录
2. 重命名为 yourdatasource.py
3. 全局替换 YourDataSource -> 你的数据源名称
4. 全局替换 yourdatasource -> 你的数据源小写标识
5. 在 main.py 中注册路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from core.database import get_db
from models.news import NewsArticle, NewsListResponse, NewsArticleResponse
from services.your_datasource_crawler import YourDataSourceCrawler  # TODO: 修改导入路径

logger = logging.getLogger(__name__)

# 创建路由器
# TODO: 修改 prefix 和 tags
router = APIRouter(
    prefix="/api/yourdatasource",
    tags=["yourdatasource"]
)

# 数据源标识
SOURCE = "yourdatasource"  # TODO: 修改为你的数据源标识


@router.get("/news", response_model=NewsListResponse)
async def get_yourdatasource_news(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    获取 YourDataSource 新闻列表

    支持功能:
    - 分页查询
    - 关键词搜索（标题和摘要）
    - 日期范围过滤

    Args:
        page: 页码，从1开始
        page_size: 每页数量，最大100
        search: 搜索关键词
        start_date: 开始日期
        end_date: 结束日期
        db: 数据库会话

    Returns:
        NewsListResponse: 包含新闻列表和分页信息
    """
    try:
        # 构建查询
        query = db.query(NewsArticle).filter(NewsArticle.source == SOURCE)

        # 关键词搜索
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (NewsArticle.title.like(search_filter)) |
                (NewsArticle.summary.like(search_filter))
            )

        # 日期范围过滤
        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(NewsArticle.publish_date >= start)
            except ValueError:
                raise HTTPException(status_code=400, detail="开始日期格式错误，应为 YYYY-MM-DD")

        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d")
                query = query.filter(NewsArticle.publish_date <= end)
            except ValueError:
                raise HTTPException(status_code=400, detail="结束日期格式错误，应为 YYYY-MM-DD")

        # 获取总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        articles = query.order_by(
            NewsArticle.publish_date.desc()
        ).offset(offset).limit(page_size).all()

        # 构建响应
        return NewsListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[NewsArticleResponse.from_orm(article) for article in articles]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 {SOURCE} 新闻列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取新闻列表失败")


@router.get("/news/{news_id}", response_model=NewsArticleResponse)
async def get_yourdatasource_news_detail(
    news_id: int,
    db: Session = Depends(get_db)
):
    """
    获取 YourDataSource 新闻详情

    Args:
        news_id: 新闻ID
        db: 数据库会话

    Returns:
        NewsArticleResponse: 新闻详情
    """
    try:
        article = db.query(NewsArticle).filter(
            NewsArticle.id == news_id,
            NewsArticle.source == SOURCE
        ).first()

        if not article:
            raise HTTPException(status_code=404, detail="新闻不存在")

        return NewsArticleResponse.from_orm(article)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 {SOURCE} 新闻详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取新闻详情失败")


@router.post("/crawl")
async def trigger_yourdatasource_crawl(
    background_tasks: BackgroundTasks,
    fetch_detail: bool = Query(False, description="是否获取文章详情"),
    db: Session = Depends(get_db)
):
    """
    手动触发 YourDataSource 新闻爬取

    此接口会在后台异步执行爬虫任务，不会阻塞请求。

    Args:
        background_tasks: FastAPI 后台任务
        fetch_detail: 是否获取文章详情（会增加爬取时间）
        db: 数据库会话

    Returns:
        dict: 任务提交状态
    """
    try:
        # 添加后台任务
        background_tasks.add_task(
            run_crawler_task,
            fetch_detail=fetch_detail
        )

        return {
            "status": "success",
            "message": f"{SOURCE} 爬虫任务已提交，正在后台执行",
            "fetch_detail": fetch_detail
        }

    except Exception as e:
        logger.error(f"提交 {SOURCE} 爬虫任务失败: {e}")
        raise HTTPException(status_code=500, detail="提交爬虫任务失败")


@router.get("/stats")
async def get_yourdatasource_stats(
    db: Session = Depends(get_db)
):
    """
    获取 YourDataSource 数据统计信息

    Args:
        db: 数据库会话

    Returns:
        dict: 统计信息，包括总数、最新文章时间等
    """
    try:
        # 总文章数
        total = db.query(NewsArticle).filter(
            NewsArticle.source == SOURCE
        ).count()

        # 最新文章
        latest_article = db.query(NewsArticle).filter(
            NewsArticle.source == SOURCE
        ).order_by(NewsArticle.publish_date.desc()).first()

        # 最早文章
        earliest_article = db.query(NewsArticle).filter(
            NewsArticle.source == SOURCE
        ).order_by(NewsArticle.publish_date.asc()).first()

        return {
            "source": SOURCE,
            "total_articles": total,
            "latest_publish_date": latest_article.publish_date.isoformat() if latest_article else None,
            "earliest_publish_date": earliest_article.publish_date.isoformat() if earliest_article else None,
            "last_crawl_time": latest_article.created_at.isoformat() if latest_article else None
        }

    except Exception as e:
        logger.error(f"获取 {SOURCE} 统计信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")


# 后台任务函数
def run_crawler_task(fetch_detail: bool = False):
    """
    后台爬虫任务

    Args:
        fetch_detail: 是否获取文章详情
    """
    try:
        logger.info(f"开始执行 {SOURCE} 后台爬虫任务...")
        crawler = YourDataSourceCrawler()
        db = next(get_db())

        try:
            count = crawler.crawl(db, fetch_detail=fetch_detail)
            logger.info(f"{SOURCE} 后台爬虫任务完成，新增 {count} 条新闻")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"{SOURCE} 后台爬虫任务失败: {e}")


# ============= 注册说明 =============
# 将此路由注册到 main.py:
#
# from api.yourdatasource import router as yourdatasource_router
# app.include_router(yourdatasource_router)
# ====================================
