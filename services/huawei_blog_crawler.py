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
Huawei Developer blog crawler.

Key requirements implemented in this module:
1. Always select the "Latest" tab and iterate through the scroll-container list.
2. Simulate user clicks on `title-text` elements to capture the real redirected URL.
3. Wait for the dynamic site to finish loading and insert random delays to avoid bans.
4. Extract text/image blocks from the main content while removing everything below the
   operations section.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import re
import time
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional
from urllib.parse import urljoin
import sys
sys.path.append(r"D:\lib\site-packages")
import undetected_chromedriver as uc

from bs4 import BeautifulSoup

try:
    from selenium import webdriver
    from selenium.common.exceptions import (
        TimeoutException,
        WebDriverException,
        StaleElementReferenceException,
    )
    from selenium.webdriver import ActionChains
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError as exc:  # pragma: no cover - selenium is required at runtime
    raise RuntimeError("selenium is required for HuaweiBlogCrawler") from exc


logger = logging.getLogger(__name__)


class HuaweiBlogCrawler:
    """Crawler for https://developer.huawei.com/consumer/cn/blog/recommended."""

    LIST_URL = "https://developer.huawei.com/consumer/cn/blog/recommended"
    SOURCE = "Huawei Developer Blog"

    def __init__(self, max_articles: int = 20):
        self.max_articles = max_articles
        self.base_url = "https://developer.huawei.com"

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def crawl_latest_articles(
        self,
        batch_callback: Optional[Callable[[List[Dict]], None]] = None,
        batch_size: int = 5,
    ) -> List[Dict]:
        """Crawl the Latest tab and return normalized article dictionaries."""
        articles: List[Dict] = []
        driver = None

        try:
            driver = self._create_driver()
            driver.get(self.LIST_URL)
            self._wait_for_page(driver)
            self._ensure_latest_tab(driver)

            idx = 0
            while idx < self.max_articles:
                self._wait_for_cards(driver)
                cards = self._get_card_elements(driver)
                if idx >= len(cards):
                    logger.info("Only %s cards available in the latest tab", len(cards))
                    break

                article = self._open_card_and_collect(driver, idx)
                if article:
                    articles.append(article)
                    logger.info("Captured article: %s", article.get("title", "Unknown"))
                    if (
                        batch_callback
                        and batch_size > 0
                        and len(articles) % batch_size == 0
                    ):
                        batch_callback(articles[-batch_size:])

                idx += 1
                self._ensure_latest_tab(driver)

        except Exception as exc:
            logger.error("Huawei blog crawler failed: %s", exc)
        finally:
            if driver:
                driver.quit()

        return articles

    # ------------------------------------------------------------------ #
    # Selenium helpers
    # ------------------------------------------------------------------ #
    def _create_driver(self):
        options = uc.ChromeOptions()
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-quic")
        options.add_argument("--disable-http2")
        options.add_argument(
            "--disable-features=SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure"
        )
        options.add_argument("--ignore-certificate-errors")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
        options.page_load_strategy = "normal"
        # 移除 headless，因为 undetected-chromedriver 在 headless 模式下容易被检测
        # 如果您一定要无头，请用 '--headless=chrome'（Chrome 109+）
        # options.add_argument("--headless=chrome")

        chrome_binary = os.getenv("HUAWEI_BLOG_CHROME_BINARY") or os.getenv("CHROME_BIN")
        if chrome_binary:
            options.binary_location = chrome_binary

        try:
            # 使用 undetected_chromedriver
            driver = uc.Chrome(options=options)  # ← 请改成您的 Chrome 主版本号！
            # 关键：删除 webdriver 特征
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                      get: () => undefined
                    });
                    """
                },
            )
            return driver
        except Exception as e:
            logger.exception("Failed to initialize undetected-chromedriver; check Chrome setup")
            raise

    def _wait_for_page(self, driver):
        WebDriverWait(driver, 60).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.sort"))
        )

    def _ensure_latest_tab(self, driver):
        """Click the 'Latest' tab to satisfy the requirement."""
        tabs = driver.find_elements(By.CSS_SELECTOR, "div.sort")
        latest = None
        for tab in tabs:
            if "\u6700\u65b0" in tab.text:
                latest = tab
                break
        if not latest:
            raise RuntimeError("Latest tab was not found on the Huawei blog page")

        classes = latest.get_attribute("class") or ""
        if "active" not in classes:
            self._scroll_into_view(driver, latest)
            self._human_pause()
            latest.click()
            self._human_pause(1.0, 1.5)

    def _wait_for_cards(self, driver):
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.scroll-container .article-item")
            )
        )

    def _get_card_elements(self, driver):
        container = driver.find_element(By.CSS_SELECTOR, "div.scroll-container")
        return container.find_elements(By.CSS_SELECTOR, "div.article-item")

    # ------------------------------------------------------------------ #
    # Card & detail processing
    # ------------------------------------------------------------------ #
    def _extract_card_metadata(self, card) -> Dict:
        title_el = card.find_element(By.CSS_SELECTOR, "a.title-text")
        title = title_el.text.strip()
        relative_url = title_el.get_attribute("href") or "#"
        summary_el = card.find_elements(By.CSS_SELECTOR, "div.article-description div")
        summary = (
            summary_el[0].text.strip()
            if summary_el
            else card.find_element(By.CSS_SELECTOR, "div.article-content").text.strip()
        )
        topic_time_el = card.find_elements(By.CSS_SELECTOR, ".topic-time")
        topic_time = topic_time_el[0].text.strip() if topic_time_el else ""

        return {
            "title": title,
            "relative_url": relative_url,
            "summary": summary,
            "time_label": topic_time,
        }

    def _open_card_and_collect(self, driver, index: int) -> Optional[Dict]:
        attempts = 0
        while attempts < 3:
            try:
                self._wait_for_cards(driver)
                cards = self._get_card_elements(driver)
                if index >= len(cards):
                    return None

                card = cards[index]
                metadata = self._extract_card_metadata(card)
                title_el = card.find_element(By.CSS_SELECTOR, "a.title-text")
                self._scroll_into_view(driver, title_el)
                self._human_pause(0.8, 1.6)
                try:
                    title_el.click()
                except Exception:
                    ActionChains(driver).move_to_element(title_el).pause(0.2).click().perform()

                self._human_pause(0.8, 1.2)
                logger.debug("URL after click on index %s: %s", index, driver.current_url)
                handles = driver.window_handles
                if len(handles) > 1:
                    driver.switch_to.window(handles[-1])

                WebDriverWait(driver, 40).until(EC.url_contains("/blog/topic/"))
                WebDriverWait(driver, 40).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.blog-content"))
                )

                current_url = driver.current_url
                logger.debug("Visiting article URL: %s", current_url)
                article = self._extract_article_from_detail(driver, metadata, current_url)

                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                else:
                    driver.back()
                self._wait_for_cards(driver)
                return article
            except StaleElementReferenceException:
                attempts += 1
                logger.debug("Encountered stale element while clicking card %s, retry %s", index, attempts)
                self._human_pause(0.5, 1.0)
            except TimeoutException:
                logger.warning("Timed out while loading article detail via card index %s", index)
                try:
                    snippet = driver.page_source[:5000]
                    logger.debug("Detail page snippet on timeout: %s", snippet)
                except Exception:
                    logger.exception("Failed to capture detail page HTML during timeout")
                driver.back()
                self._wait_for_cards(driver)
                return None

        logger.error("Failed to interact with card index %s after multiple retries", index)
        return None

    def _extract_article_from_detail(
        self, driver, metadata: Dict, absolute_url: str
    ) -> Optional[Dict]:
        self._remove_operations_blocks(driver)
        content_element = driver.find_element(By.CSS_SELECTOR, "div.blog-content")
        html = content_element.get_attribute("innerHTML") or ""
        soup = BeautifulSoup(html, "html.parser")
        blocks = self._parse_content_blocks(soup)

        publish_time = self._normalize_time(metadata.get("time_label") or "")
        summary = metadata.get("summary") or (
            blocks[0]["value"][:120] if blocks and blocks[0]["type"] == "text" else ""
        )

        return {
            "id": hashlib.md5(absolute_url.encode("utf-8")).hexdigest(),
            "title": metadata.get("title"),
            "url": absolute_url,
            "date": publish_time,
            "source": self.SOURCE,
            "summary": summary,
            "category": "Huawei Developer",
            "content": blocks,
        }

    # ------------------------------------------------------------------ #
    # DOM helpers
    # ------------------------------------------------------------------ #
    def _remove_operations_blocks(self, driver):
        ops = driver.find_elements(By.CSS_SELECTOR, "div.operations")
        for op in ops:
            driver.execute_script("arguments[0].remove();", op)

    def _parse_content_blocks(self, soup: BeautifulSoup) -> List[Dict]:
        blocks: List[Dict] = []

        for element in soup.children:
            if getattr(element, "name", None) is None:
                text = str(element).strip()
                if text:
                    blocks.append({"type": "text", "value": text})
                continue

            if element.name == "img":
                src = (
                    element.get("src")
                    or element.get("data-src")
                    or element.get("data-original")
                )
                if src:
                    blocks.append({"type": "image", "value": urljoin(self.base_url, src)})
                continue

            # Recursively capture nested images first
            for img in element.find_all("img"):
                src = (
                    img.get("src")
                    or img.get("data-src")
                    or img.get("data-original")
                )
                if src:
                    blocks.append(
                        {"type": "image", "value": urljoin(self.base_url, src)}
                    )

            text_value = element.get_text(separator="\n", strip=True)
            if text_value:
                blocks.append({"type": "text", "value": text_value})

        return blocks

    def _scroll_into_view(self, driver, element):
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)

    def _human_pause(self, start: float = 0.8, end: float = 1.2):
        time.sleep(random.uniform(start, end))

    # ------------------------------------------------------------------ #
    # Time parsing
    # ------------------------------------------------------------------ #
    def _normalize_time(self, label: str) -> str:
        label = (label or "").strip()
        if not label:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        now = datetime.now()
        number_match = re.search(r"(\d+)", label)

        try:
            if "\u5206\u949f\u524d" in label and number_match:
                dt = now - timedelta(minutes=int(number_match.group(1)))
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            if "\u5c0f\u65f6\u524d" in label and number_match:
                dt = now - timedelta(hours=int(number_match.group(1)))
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            if "\u5929\u524d" in label and number_match:
                dt = now - timedelta(days=int(number_match.group(1)))
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            if label.startswith("\u6628\u5929"):
                time_part = re.search(r"(\d{1,2}:\d{2})", label)
                dt = now - timedelta(days=1)
                if time_part:
                    hours, minutes = map(int, time_part.group(1).split(":"))
                    dt = dt.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            if label.startswith("\u524d\u5929"):
                time_part = re.search(r"(\d{1,2}:\d{2})", label)
                dt = now - timedelta(days=2)
                if time_part:
                    hours, minutes = map(int, time_part.group(1).split(":"))
                    dt = dt.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            if re.match(r"\d{4}[./-]\d{2}[./-]\d{2}", label):
                normalized = label.replace(".", "-").replace("/", "-")
                if len(normalized) == 10:
                    normalized += " 00:00:00"
                return normalized
        except Exception:
            logger.debug("Failed to parse publish time label: %s", label)

        return label


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    crawler = HuaweiBlogCrawler(max_articles=5)
    results = crawler.crawl_latest_articles()
    print(json.dumps({"count": len(results), "articles": results}, ensure_ascii=False, indent=2))
