# Copyright (c) 2025 XBXyftx
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
华为开发者博客爬虫
目标网站: https://developer.huawei.com/consumer/cn/blog/recommended
数据类型: 技术博客文章
"""

import logging
import time
import random
from typing import List, Dict, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import re

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)


class HuaweiDeveloperBlogCrawler:
    """华为开发者博客爬虫类"""

    def __init__(self, base_url: str = "https://developer.huawei.com"):
        """
        初始化爬虫

        Args:
            base_url: 目标网站根URL
        """
        self.base_url = base_url
        self.blog_list_url = f"{base_url}/consumer/cn/blog/recommended"
        self.driver = None

    def _init_driver(self):
        """初始化Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--log-level=3')  # 减少日志输出
            
            # 尝试使用webdriver-manager自动管理驱动
            if WEBDRIVER_MANAGER_AVAILABLE:
                try:
                    import platform
                    # 根据系统架构选择正确的驱动
                    if platform.machine().endswith('64'):
                        from webdriver_manager.chrome import ChromeDriverManager
                        from webdriver_manager.core.os_manager import ChromeType
                        service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
                    else:
                        service = Service(ChromeDriverManager().install())
                    
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    logger.info("WebDriver初始化成功（使用webdriver-manager）")
                    return
                except Exception as e:
                    logger.warning(f"webdriver-manager初始化失败，尝试使用系统Chrome: {e}")
            
            # 回退到系统Chrome
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("WebDriver初始化成功（使用系统Chrome）")
        except Exception as e:
            logger.error(f"WebDriver初始化失败: {e}")
            logger.error("请确保已安装Chrome浏览器和ChromeDriver")
            logger.error("或者运行: pip install webdriver-manager")
            raise

    def _close_driver(self):
        """关闭WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver已关闭")
            except Exception as e:
                logger.error(f"关闭WebDriver失败: {e}")

    def _random_sleep(self, min_seconds=1, max_seconds=3):
        """随机延迟，模拟人类行为"""
        sleep_time = random.uniform(min_seconds, max_seconds)
        time.sleep(sleep_time)

    def fetch_article_urls(self, max_articles=20) -> List[str]:
        """
        获取文章URL列表

        Args:
            max_articles: 最大文章数量

        Returns:
            文章URL列表
        """
        article_urls = []
        
        try:
            self._init_driver()
            
            logger.info(f"正在访问: {self.blog_list_url}")
            self.driver.get(self.blog_list_url)
            
            # 等待页面加载
            self._random_sleep(3, 5)
            
            # 点击"最新"选项
            try:
                logger.info("尝试点击'最新'选项...")
                # 等待"最新"按钮出现并点击
                latest_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '最新')]"))
                )
                latest_button.click()
                logger.info("已点击'最新'选项")
                self._random_sleep(2, 4)
            except Exception as e:
                logger.warning(f"点击'最新'选项失败，继续使用默认列表: {e}")
            
            # 调试：保存页面HTML以便分析
            try:
                page_source = self.driver.page_source
                # 查找所有可能的链接
                soup = BeautifulSoup(page_source, 'html.parser')
                all_links = soup.find_all('a', href=True)
                blog_links = [link for link in all_links if '/blog/' in link.get('href', '') or '/blogDetail' in link.get('href', '')]
                logger.info(f"页面中找到 {len(all_links)} 个链接，其中 {len(blog_links)} 个博客链接")
                
                # 显示前3个博客链接作为示例
                for i, link in enumerate(blog_links[:3], 1):
                    logger.info(f"示例链接 {i}: {link.get('href')}")
            except Exception as e:
                logger.warning(f"调试信息获取失败: {e}")
            
            # 滚动页面以加载更多内容
            logger.info("开始滚动页面加载内容...")
            scroll_count = 0
            max_scrolls = 5
            
            while scroll_count < max_scrolls and len(article_urls) < max_articles:
                # 滚动到页面底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self._random_sleep(2, 3)
                scroll_count += 1
                
                # 查找所有文章链接 - 尝试多种选择器
                try:
                    # 尝试多种可能的选择器
                    selectors = [
                        "a.title-text",  # 直接是a标签
                        ".title-text a",  # title-text下的a标签
                        "a[href*='/blog/']",  # 包含/blog/的链接
                        ".blog-item a",  # blog-item下的链接
                        ".article-item a",  # article-item下的链接
                        "a.ng-star-inserted[href]",  # 带href的ng-star-inserted链接
                    ]
                    
                    articles = []
                    for selector in selectors:
                        try:
                            found = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if found:
                                articles = found
                                logger.info(f"第{scroll_count}次滚动，使用选择器 '{selector}' 找到 {len(articles)} 个文章元素")
                                break
                        except:
                            continue
                    
                    if not articles:
                        logger.warning(f"第{scroll_count}次滚动，未找到文章元素")
                        continue
                    
                    for article in articles:
                        if len(article_urls) >= max_articles:
                            break
                        
                        try:
                            # 尝试直接获取href
                            href = article.get_attribute('href')
                            
                            # 如果元素本身不是链接，尝试查找父级或子级链接
                            if not href:
                                try:
                                    # 尝试查找父级链接
                                    parent_link = article.find_element(By.XPATH, "./ancestor::a[@href]")
                                    href = parent_link.get_attribute('href')
                                except:
                                    try:
                                        # 尝试查找子级链接
                                        child_link = article.find_element(By.XPATH, ".//a[@href]")
                                        href = child_link.get_attribute('href')
                                    except:
                                        continue
                            
                            if href and href not in article_urls:
                                # 过滤掉非博客文章的链接
                                if '/blog/' not in href and '/blogDetail' not in href:
                                    continue
                                
                                # 确保是完整URL
                                if href.startswith('/'):
                                    full_url = f"{self.base_url}{href}"
                                elif not href.startswith('http'):
                                    full_url = f"{self.base_url}/{href}"
                                else:
                                    full_url = href
                                
                                article_urls.append(full_url)
                                logger.info(f"找到文章URL: {full_url}")
                        except Exception as e:
                            logger.debug(f"提取单个文章URL失败: {e}")
                            continue
                
                except Exception as e:
                    logger.error(f"查找文章元素失败: {e}")
            
            logger.info(f"共找到 {len(article_urls)} 个文章URL")
            
        except Exception as e:
            logger.error(f"获取文章URL列表失败: {e}")
        finally:
            self._close_driver()
        
        return article_urls[:max_articles]

    def fetch_article_content(self, article_url: str) -> Optional[Dict]:
        """
        获取文章详细内容

        Args:
            article_url: 文章URL

        Returns:
            文章内容字典，失败返回None
        """
        try:
            self._init_driver()
            
            logger.info(f"正在抓取文章: {article_url}")
            self.driver.get(article_url)
            
            # 等待页面加载
            self._random_sleep(3, 5)
            
            # 等待内容加载
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                logger.error(f"页面加载超时: {article_url}")
                return None
            
            # 获取页面HTML
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 提取标题
            title = ""
            title_selectors = [
                'h1.title',
                'h1',
                '.article-title',
                '[class*="title"]'
            ]
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title:
                logger.warning(f"未找到标题: {article_url}")
                title = "无标题"
            
            # 提取发布日期
            date = datetime.now().strftime("%Y-%m-%d")
            date_selectors = [
                '.publish-time',
                '.date',
                '[class*="time"]',
                '[class*="date"]'
            ]
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    # 尝试提取日期
                    date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', date_text)
                    if date_match:
                        date = date_match.group(1).replace('/', '-')
                        break
            
            # 提取正文内容（排除operations标签及其以下内容）
            content_blocks = []
            
            # 查找主要内容区域
            content_area = None
            content_selectors = [
                'div[_ngcontent-serverapp-c154]',
                '.article-content',
                '.content',
                'article',
                '.post-content'
            ]
            
            for selector in content_selectors:
                content_area = soup.select_one(selector)
                if content_area:
                    break
            
            if content_area:
                # 移除operations标签及其以下的所有内容
                operations_div = content_area.find('div', class_='operations')
                if operations_div:
                    # 删除operations及其后面的所有兄弟元素
                    for sibling in list(operations_div.find_next_siblings()):
                        sibling.decompose()
                    operations_div.decompose()
                
                # 提取文本和图片
                for element in content_area.descendants:
                    if element.name == 'p' or element.name == 'div':
                        text = element.get_text(strip=True)
                        if text and len(text) > 10:  # 过滤太短的文本
                            content_blocks.append({
                                "type": "text",
                                "value": text
                            })
                    elif element.name == 'img':
                        img_src = element.get('src', '')
                        if img_src:
                            # 确保是完整URL
                            if img_src.startswith('/'):
                                img_src = f"{self.base_url}{img_src}"
                            elif not img_src.startswith('http'):
                                img_src = f"{self.base_url}/{img_src}"
                            
                            content_blocks.append({
                                "type": "image",
                                "value": img_src
                            })
            
            # 如果没有找到内容，记录警告
            if not content_blocks:
                logger.warning(f"未找到文章内容: {article_url}")
                content_blocks = [{
                    "type": "text",
                    "value": "内容提取失败"
                }]
            
            # 生成摘要（取前200个字符）
            summary = ""
            for block in content_blocks:
                if block["type"] == "text":
                    summary = block["value"][:200]
                    break
            
            article_data = {
                "title": title,
                "url": article_url,
                "date": date,
                "content": content_blocks,
                "summary": summary,
                "category": "Huawei Developer",
                "source": "Huawei Developer"
            }
            
            logger.info(f"成功抓取文章: {title}")
            return article_data
            
        except Exception as e:
            logger.error(f"获取文章内容失败 {article_url}: {e}")
            return None
        finally:
            self._close_driver()

    def crawl_all(self, max_articles=20) -> List[Dict]:
        """
        执行完整爬取流程

        Args:
            max_articles: 最大文章数量

        Returns:
            文章列表
        """
        logger.info(f"开始爬取华为开发者博客，最多 {max_articles} 篇文章")
        
        # 第一步：获取文章URL列表
        article_urls = self.fetch_article_urls(max_articles)
        
        if not article_urls:
            logger.warning("未找到任何文章URL")
            return []
        
        # 第二步：逐个抓取文章内容
        articles = []
        for i, url in enumerate(article_urls, 1):
            logger.info(f"正在抓取第 {i}/{len(article_urls)} 篇文章")
            
            article_data = self.fetch_article_content(url)
            if article_data:
                articles.append(article_data)
            
            # 随机延迟，避免被封
            if i < len(article_urls):
                self._random_sleep(2, 5)
        
        logger.info(f"爬取完成，成功获取 {len(articles)} 篇文章")
        return articles


# 模块级函数 - 供外部调用
def crawl_huawei_developer_blog(max_articles=20) -> List[Dict]:
    """
    执行华为开发者博客爬取

    Args:
        max_articles: 最大文章数量

    Returns:
        文章列表
    """
    crawler = HuaweiDeveloperBlogCrawler()
    return crawler.crawl_all(max_articles)


if __name__ == "__main__":
    # 本地测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("开始测试华为开发者博客爬虫...")
    articles = crawl_huawei_developer_blog(max_articles=5)
    
    print(f"\n成功爬取 {len(articles)} 篇文章:")
    for i, article in enumerate(articles, 1):
        print(f"\n{i}. {article['title']}")
        print(f"   URL: {article['url']}")
        print(f"   日期: {article['date']}")
        print(f"   内容块数: {len(article['content'])}")
        print(f"   摘要: {article['summary'][:100]}...")
