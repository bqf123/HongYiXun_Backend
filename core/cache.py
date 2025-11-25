# core/cache.py
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
from enum import Enum

from services.huawei_blog_api_crawler import HuaweiBlogAPICrawler
from models.news import NewsArticle, NewsResponse

logger = logging.getLogger(__name__)

class ServiceStatus(str, Enum):
    PREPARING = "preparing"
    READY = "ready"
    ERROR = "error"

class NewsCache:
    def __init__(self):
        self.articles: List[NewsArticle] = []
        self.status: ServiceStatus = ServiceStatus.PREPARING
        self.error_message: Optional[str] = None
        self.last_update: Optional[datetime] = None
        self._load_initial_data()
    
    def _load_initial_data(self):
        """加载初始数据到缓存"""
        try:
            logger.info("开始加载新闻缓存...")
            self.articles = []
            
            # 加载华为开发者博客
            try:
                huawei_crawler = HuaweiBlogAPICrawler()
                # 只加载基础数据（不抓取详情内容，详情在 get_news 时抓取）
                huawei_articles = self._get_huawei_articles_basic()
                self.articles.extend(huawei_articles)
                logger.info(f"成功加载 {len(huawei_articles)} 篇华为开发者文章（基础数据）")
            except Exception as e:
                logger.error(f"加载华为开发者博客失败: {e}")
            
            self.status = ServiceStatus.READY
            self.last_update = datetime.now()
            logger.info("新闻缓存加载完成")
            
        except Exception as e:
            self.status = ServiceStatus.ERROR
            self.error_message = str(e)
            logger.error(f"新闻缓存加载失败: {e}")
    
    def _get_huawei_articles_basic(self):
        """获取华为文章的基础数据（不包含详情内容）"""
        import requests
        import hashlib
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Referer": "https://developer.huawei.com/consumer/cn/blog/recommended",
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://developer.huawei.com",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors"
        }
        
        payload = {
            "pageSize": 50,
            "pageIndex": 1,
            "type": 0
        }
        
        try:
            response = requests.post(
                "https://svc-drcn.developer.huawei.com/community/servlet/consumer/partnerblogservice/v1/openblog/getBlogList",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            articles = []
            result_list = data.get("resultList", [])
            for item in result_list:
                article = {
                    "id": hashlib.md5(item["blogId"].encode()).hexdigest(),
                    "title": item.get("title", ""),
                    "url": f"https://developer.huawei.com/consumer/cn/blog/topic/{item['blogId']}",
                    "date": self._format_time_basic(item.get("publishTime", "")),
                    "source": "Huawei Developer Blog",
                    "summary": item.get("summary", ""),
                    "category": "Huawei Developer",
                    "content": [{"type": "text", "value": item.get("summary", "")}]
                }
                articles.append(article)
            return articles
        except Exception as e:
            logger.error(f"获取华为文章基础数据失败: {e}")
            return []
    
    def _format_time_basic(self, time_str):
        """基础时间格式化"""
        if not time_str:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            time_str = str(time_str).strip()
            if len(time_str) >= 14:
                year = time_str[0:4]
                month = time_str[4:6]
                day = time_str[6:8]
                hour = time_str[8:10]
                minute = time_str[10:12]
                second = time_str[12:14]
                return f"{year}-{month}-{day} {hour}:{minute}:{second}"
            else:
                return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_news(self, page: int = 1, page_size: int = 20, 
                 category: Optional[str] = None, 
                 search: Optional[str] = None) -> NewsResponse:
        """获取新闻列表，支持分类和搜索（此时才抓取完整内容）"""
        if self.status == ServiceStatus.PREPARING:
            return NewsResponse(
                articles=[],
                total=0,
                page=page,
                page_size=page_size,
                has_next=False,
                has_prev=False
            )
        
        # 过滤数据
        filtered_articles = self.articles
        
        # 分类过滤
        if category:
            filtered_articles = [a for a in filtered_articles if a.get('category') == category]
        
        # 关键字搜索
        if search:
            filtered_articles = [
                a for a in filtered_articles 
                if search.lower() in a.get('title', '').lower() or 
                   search.lower() in a.get('summary', '').lower()
            ]
        
        # 分页处理
        total = len(filtered_articles)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_articles = filtered_articles[start:end]
        
        # 注意：这里不抓取详细内容，因为会太慢
        # 详细内容应该在获取单篇文章时抓取（/api/news/{article_id}）
        
        return NewsResponse(
            articles=paginated_articles,
            total=total,
            page=page,
            page_size=page_size,
            has_next=end < total,
            has_prev=page > 1
        )
    
    def get_article_detail(self, article_id: str):
        """获取单篇文章的详细内容"""
        for article in self.articles:
            if article["id"] == article_id:
                # 抓取详细内容
                crawler = HuaweiBlogAPICrawler()
                article["content"] = crawler._fetch_article_content(article["url"])
                return article
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        return {
            "status": self.status.value,
            "error_message": self.error_message,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "total_articles": len(self.articles)
        }
    
    def refresh_data(self):
        """刷新缓存数据"""
        self.status = ServiceStatus.PREPARING
        self._load_initial_data()
    
    def append_to_cache(self, articles: List[NewsArticle]):
        """向缓存中追加文章（用于分批加载）"""
        self.articles.extend(articles)
        logger.info(f"向新闻缓存追加 {len(articles)} 篇文章，当前总数: {len(self.articles)}")


# 全局缓存实例
_news_cache = None

def get_news_cache() -> NewsCache:
    """获取新闻缓存实例（单例模式）"""
    global _news_cache
    if _news_cache is None:
        _news_cache = NewsCache()
    return _news_cache


# =============== 轮播图缓存部分 ===============
_banner_cache = None

class BannerCache:
    def __init__(self):
        self.banners = []
        self.status = ServiceStatus.PREPARING
        self.error_message = None
        self.last_update = None
        self._load_initial_data()
    
    def _load_initial_data(self):
        """加载轮播图数据（暂时返回空列表）"""
        try:
            # 未来可以在这里实现真实的轮播图爬取逻辑
            self.banners = []
            self.status = ServiceStatus.READY
            self.last_update = datetime.now()
        except Exception as e:
            self.status = ServiceStatus.ERROR
            self.error_message = str(e)
    
    def get_banners(self):
        """获取轮播图列表"""
        return self.banners
    
    def get_status(self):
        """获取轮播图缓存状态"""
        return {
            "status": self.status.value,
            "error_message": self.error_message,
            "last_update": self.last_update.isoformat() if self.last_update else None
        }
    
    def set_updating(self, is_updating: bool):
        """设置轮播图缓存更新状态"""
        if is_updating:
            logger.info("轮播图缓存开始更新")
        else:
            logger.info("轮播图缓存更新完成")
            self.last_update = datetime.now()
    
    def update_cache(self, banners: List[Dict]):
        """更新轮播图缓存数据"""
        self.banners = banners
        self.status = ServiceStatus.READY
        self.last_update = datetime.now()
        logger.info(f"轮播图缓存更新完成，共 {len(banners)} 张图片")


def get_banner_cache() -> BannerCache:
    """获取轮播图缓存实例（单例模式）"""
    global _banner_cache
    if _banner_cache is None:
        _banner_cache = BannerCache()
    return _banner_cache


def init_cache():
    """
    初始化所有缓存（新闻缓存 + 轮播图缓存）
    这个函数会被 main.py 调用来预热缓存
    """
    # 触发新闻缓存初始化
    get_news_cache()
    # 触发轮播图缓存初始化  
    get_banner_cache()
    logger.info("所有缓存初始化完成")