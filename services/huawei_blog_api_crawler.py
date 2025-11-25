# huawei_blog_api_crawler.py
import requests
import json
import hashlib
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup

# Selenium 相关导入
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

class HuaweiBlogAPICrawler:
    API_URL = "https://svc-drcn.developer.huawei.com/community/servlet/consumer/partnerblogservice/v1/openblog/getBlogList"
    
    def __init__(self):
        self.driver = None
    
    def _get_driver(self):
        """获取或创建浏览器实例（使用 undetected-chromedriver）"""
        if not self.driver:
            try:
                options = uc.ChromeOptions()
                options.add_argument("--headless=new")  # 无界面模式
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
                options.add_argument("--window-size=1920,1080")
                
                self.driver = uc.Chrome(options=options)
                # 移除 webdriver 特征
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                print("浏览器启动成功")
            except Exception as e:
                print(f"启动浏览器失败: {e}")
                return None
        return self.driver
    
    def crawl_latest_articles(self, max_articles=5, page=1, page_size=5, keyword=""):
        """
        抓取华为开发者博客文章
        
        Args:
            max_articles: 初始化时抓取的最大数量（用于缓存）
            page: 当前页码（默认=1）
            page_size: 每页数量（默认=5）
            keyword: 关键字搜索（默认=空，不搜索）
        """
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
        
        fetch_size = max(max_articles, page * page_size, 50)
        
        payload = {
            "pageSize": fetch_size,
            "pageIndex": 1,
            "type": 0
        }
        
        try:
            response = requests.post(
                self.API_URL, 
                headers=headers, 
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            base_articles = []
            result_list = data.get("resultList", [])
            for item in result_list:
                article = {
                    "id": hashlib.md5(item["blogId"].encode()).hexdigest(),
                    "title": item.get("title", ""),
                    "url": f"https://developer.huawei.com/consumer/cn/blog/topic/{item['blogId']}",
                    "date": self._format_time(item.get("publishTime", "")),
                    "source": "Huawei Developer Blog",
                    "summary": item.get("summary", ""),
                    "category": "Huawei Developer",
                    "content": [{"type": "text", "value": item.get("summary", "")}]
                }
                base_articles.append(article)
            
            # 关键字过滤
            if keyword:
                filtered = []
                for art in base_articles:
                    if (keyword in art["title"]) or (keyword in art["summary"]):
                        filtered.append(art)
                base_articles = filtered
            
            # 内存分页
            start = (page - 1) * page_size
            end = start + page_size
            paginated_articles = base_articles[start:end]
            
            # 补充完整内容（只对当前页的文章抓取详情）
            final_articles = []
            for article in paginated_articles:
                print(f"正在抓取文章内容: {article['title']}")
                time.sleep(random.uniform(1.0, 2.0))  # 随机延迟
                article["content"] = self._fetch_article_content(article["url"])
                final_articles.append(article)
                
            return final_articles
            
        except Exception as e:
            print(f"API 爬取失败: {e}")
            return []

    def _fetch_article_content(self, url):
        """用 undetected-chromedriver 抓取文章详情页的完整内容"""
        try:
            driver = self._get_driver()
            if not driver:
                return [{"type": "text", "value": "浏览器初始化失败"}]
            
            driver.get(url)
            
            # 等待页面加载
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 等待主要内容区域
            content_element = None
            selectors = [
                'div#blogContent',
                'div.blog-content',
                'div.article-content',
                'div.post-content',
                'article',
                'div.content',
                'div.main-content'
            ]
            
            for selector in selectors:
                try:
                    content_element = WebDriverWait(driver, 8).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if not content_element:
                # 尝试查找包含最多文本的 div
                all_divs = driver.find_elements(By.TAG_NAME, "div")
                if all_divs:
                    content_element = max(all_divs, key=lambda x: len(x.text) if x.text else 0)
            
            if not content_element:
                return [{"type": "text", "value": "无法找到文章内容区域"}]
            
            # 提取内容块
            blocks = []
            
            # 先处理图片
            img_elements = content_element.find_elements(By.TAG_NAME, "img")
            for img in img_elements:
                img_src = img.get_attribute('src') or img.get_attribute('data-src')
                if img_src:
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    elif img_src.startswith('/'):
                        img_src = 'https://developer.huawei.com' + img_src
                    blocks.append({"type": "image", "value": img_src})
            
            # 处理文本元素
            text_elements = content_element.find_elements(By.XPATH, ".//p | .//h1 | .//h2 | .//h3 | .//h4 | .//h5 | .//h6 | .//div")
            seen_texts = set()  # 避免重复
            
            for element in text_elements:
                text = element.text.strip()
                if text and len(text) > 2 and text not in seen_texts:
                    seen_texts.add(text)
                    blocks.append({"type": "text", "value": text})
            
            return blocks if blocks else [{"type": "text", "value": "文章内容为空"}]
            
        except Exception as e:
            error_msg = f"内容抓取失败: {str(e)}"
            print(error_msg)
            return [{"type": "text", "value": error_msg}]

    def _format_time(self, time_str):
        """将 YYYYMMDDHHmmss 格式的字符串转为标准日期格式"""
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
    
    def __del__(self):
        """清理资源"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

if __name__ == "__main__":
    crawler = HuaweiBlogAPICrawler()
    
    # 测试分页：第1页，每页2条
    print("=== 第1页 ===")
    articles = crawler.crawl_latest_articles(page=1, page_size=2)
    print(json.dumps({"count": len(articles), "articles": articles}, ensure_ascii=False, indent=2))
    
    # 测试关键字搜索
    print("\n=== 关键字搜索 '鸿蒙' ===")
    articles = crawler.crawl_latest_articles(keyword="鸿蒙", page_size=2)
    print(json.dumps({"count": len(articles), "articles": articles}, ensure_ascii=False, indent=2))