"""
YourDataSource 新闻爬虫模板

功能说明:
- 从 YourDataSource 网站爬取新闻/文章数据
- 支持增量更新和全量爬取
- 包含错误处理和重试机制

使用步骤:
1. 复制此文件到 services/ 目录
2. 重命名为 your_datasource_crawler.py
3. 全局替换 YourDataSource -> 你的数据源名称
4. 全局替换 yourdatasource -> 你的数据源小写标识
5. 实现 TODO 标记的部分
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from sqlalchemy.orm import Session

from core.database import get_db
from models.news import NewsArticle

logger = logging.getLogger(__name__)


class YourDataSourceCrawler:
    """YourDataSource 新闻爬虫类"""

    def __init__(self):
        # TODO: 修改为你的数据源 URL
        self.base_url = "https://www.yourdatasource.com"
        self.news_list_url = f"{self.base_url}/news"  # 新闻列表页

        # 请求配置
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.timeout = 10
        self.max_retries = 3

        # 爬虫标识
        self.source = "yourdatasource"  # TODO: 修改为你的数据源标识

    def fetch_page(self, url: str) -> Optional[str]:
        """
        获取网页内容

        Args:
            url: 目标URL

        Returns:
            网页HTML内容，失败返回None
        """
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                # TODO: 根据实际编码调整
                response.encoding = response.apparent_encoding or 'utf-8'
                return response.text

            except requests.RequestException as e:
                logger.warning(
                    f"获取页面失败 (尝试 {attempt + 1}/{self.max_retries}): {url}, 错误: {e}"
                )
                if attempt == self.max_retries - 1:
                    logger.error(f"获取页面最终失败: {url}")
                    return None
        return None

    def parse_news_list(self, html: str) -> List[Dict]:
        """
        解析新闻列表页

        Args:
            html: 新闻列表页HTML

        Returns:
            新闻条目列表，每个条目包含 title, url, date 等字段
        """
        news_items = []
        soup = BeautifulSoup(html, 'html.parser')

        # TODO: 根据实际网页结构修改选择器
        # 示例: 找到所有新闻条目容器
        news_elements = soup.select('.news-item')  # 修改为实际的CSS选择器

        for element in news_elements:
            try:
                # TODO: 根据实际结构提取数据
                # 示例提取逻辑
                title_elem = element.select_one('.title')  # 修改选择器
                link_elem = element.select_one('a')
                date_elem = element.select_one('.date')

                if not (title_elem and link_elem):
                    continue

                title = title_elem.get_text(strip=True)
                url = link_elem.get('href', '')
                if not url.startswith('http'):
                    url = self.base_url + url

                # 日期解析
                date_str = date_elem.get_text(strip=True) if date_elem else ""
                publish_date = self.parse_date(date_str)

                news_items.append({
                    'title': title,
                    'url': url,
                    'publish_date': publish_date,
                    'source': self.source
                })

            except Exception as e:
                logger.warning(f"解析新闻条目失败: {e}")
                continue

        return news_items

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """
        解析日期字符串

        Args:
            date_str: 日期字符串

        Returns:
            datetime对象，解析失败返回None
        """
        if not date_str:
            return None

        # TODO: 根据实际日期格式添加解析逻辑
        # 示例格式
        date_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        logger.warning(f"无法解析日期: {date_str}")
        return None

    def fetch_article_detail(self, url: str) -> Dict:
        """
        获取文章详情

        Args:
            url: 文章URL

        Returns:
            文章详情字典，包含 content, summary, image_url 等
        """
        html = self.fetch_page(url)
        if not html:
            return {}

        soup = BeautifulSoup(html, 'html.parser')

        # TODO: 根据实际页面结构提取详情
        detail = {}

        # 示例: 提取正文内容
        content_elem = soup.select_one('.article-content')  # 修改选择器
        if content_elem:
            detail['content'] = content_elem.get_text(strip=True)

        # 示例: 提取摘要
        summary_elem = soup.select_one('.summary')
        if summary_elem:
            detail['summary'] = summary_elem.get_text(strip=True)

        # 示例: 提取封面图
        image_elem = soup.select_one('.article-image img')
        if image_elem:
            image_url = image_elem.get('src', '')
            if not image_url.startswith('http'):
                image_url = self.base_url + image_url
            detail['image_url'] = image_url

        return detail

    def crawl(self, db: Session, fetch_detail: bool = False) -> int:
        """
        执行爬取任务

        Args:
            db: 数据库会话
            fetch_detail: 是否获取文章详情

        Returns:
            新增文章数量
        """
        logger.info(f"开始爬取 {self.source} 新闻...")

        # 获取新闻列表页
        html = self.fetch_page(self.news_list_url)
        if not html:
            logger.error("获取新闻列表失败")
            return 0

        # 解析新闻列表
        news_items = self.parse_news_list(html)
        logger.info(f"解析到 {len(news_items)} 条新闻")

        new_count = 0
        for item in news_items:
            try:
                # 检查是否已存在
                existing = db.query(NewsArticle).filter(
                    NewsArticle.url == item['url']
                ).first()

                if existing:
                    logger.debug(f"新闻已存在，跳过: {item['title']}")
                    continue

                # 获取详情（可选）
                if fetch_detail:
                    detail = self.fetch_article_detail(item['url'])
                    item.update(detail)

                # 创建数据库记录
                article = NewsArticle(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    summary=item.get('summary', ''),
                    content=item.get('content', ''),
                    image_url=item.get('image_url', ''),
                    publish_date=item.get('publish_date'),
                    source=self.source,
                    created_at=datetime.now()
                )

                db.add(article)
                db.commit()
                new_count += 1
                logger.info(f"新增文章: {article.title}")

            except Exception as e:
                logger.error(f"保存文章失败: {e}")
                db.rollback()
                continue

        logger.info(f"{self.source} 爬取完成，新增 {new_count} 条新闻")
        return new_count


# 便捷函数
def crawl_yourdatasource_news(fetch_detail: bool = False) -> int:
    """
    爬取 YourDataSource 新闻的便捷函数

    Args:
        fetch_detail: 是否获取文章详情

    Returns:
        新增文章数量
    """
    crawler = YourDataSourceCrawler()
    db = next(get_db())
    try:
        return crawler.crawl(db, fetch_detail=fetch_detail)
    finally:
        db.close()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    count = crawl_yourdatasource_news(fetch_detail=True)
    print(f"成功爬取 {count} 条新闻")
