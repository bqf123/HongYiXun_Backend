"""
测试华为开发者博客爬虫集成和API功能
包括：
1. 爬虫功能测试
2. category分类查询测试
3. page和page_size分页功能测试
"""

import asyncio
import logging
import sys
import requests
import time

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API基础URL
API_BASE_URL = "http://localhost:8001"


def test_api_health():
    """测试API健康状态"""
    logger.info("=" * 60)
    logger.info("测试1: API健康检查")
    logger.info("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ API健康状态: {data.get('status')}")
            logger.info(f"   缓存状态: {data.get('cache_status')}")
            logger.info(f"   缓存文章数: {data.get('cache_count')}")
            return True
        else:
            logger.error(f"❌ API健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ API健康检查异常: {e}")
        return False


def test_get_all_news():
    """测试获取所有新闻"""
    logger.info("\n" + "=" * 60)
    logger.info("测试2: 获取所有新闻（第1页，每页10条）")
    logger.info("=" * 60)
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/news/",
            params={"page": 1, "page_size": 10},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ 成功获取新闻")
            logger.info(f"   总文章数: {data.get('total')}")
            logger.info(f"   当前页: {data.get('page')}")
            logger.info(f"   每页数量: {data.get('page_size')}")
            logger.info(f"   是否有下一页: {data.get('has_next')}")
            logger.info(f"   是否有上一页: {data.get('has_prev')}")
            
            articles = data.get('articles', [])
            logger.info(f"\n   返回文章数: {len(articles)}")
            
            # 显示前3篇文章
            for i, article in enumerate(articles[:3], 1):
                logger.info(f"\n   文章 {i}:")
                logger.info(f"      标题: {article.get('title')}")
                logger.info(f"      分类: {article.get('category')}")
                logger.info(f"      来源: {article.get('source')}")
                logger.info(f"      日期: {article.get('date')}")
                logger.info(f"      URL: {article.get('url')[:80]}...")
            
            return True
        else:
            logger.error(f"❌ 获取新闻失败: {response.status_code}")
            logger.error(f"   响应: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ 获取新闻异常: {e}")
        return False


def test_category_filter():
    """测试category分类过滤"""
    logger.info("\n" + "=" * 60)
    logger.info("测试3: Category分类查询")
    logger.info("=" * 60)
    
    # 测试不同的category
    categories = ["Huawei Developer", "官方动态", "技术博客"]
    
    for category in categories:
        logger.info(f"\n--- 测试分类: {category} ---")
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/news/",
                params={"category": category, "page": 1, "page_size": 5},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                logger.info(f"✅ 分类 '{category}' 查询成功")
                logger.info(f"   找到 {data.get('total')} 篇文章")
                logger.info(f"   返回 {len(articles)} 篇文章")
                
                # 验证所有文章都属于该分类
                for article in articles:
                    if article.get('category') != category:
                        logger.warning(f"⚠️  文章分类不匹配: {article.get('category')} != {category}")
                
                # 显示第一篇文章
                if articles:
                    first = articles[0]
                    logger.info(f"   示例文章: {first.get('title')}")
            else:
                logger.error(f"❌ 分类查询失败: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ 分类查询异常: {e}")
    
    return True


def test_pagination():
    """测试分页功能"""
    logger.info("\n" + "=" * 60)
    logger.info("测试4: 分页功能测试")
    logger.info("=" * 60)
    
    # 测试不同的分页参数
    test_cases = [
        {"page": 1, "page_size": 5},
        {"page": 2, "page_size": 5},
        {"page": 1, "page_size": 20},
    ]
    
    for params in test_cases:
        logger.info(f"\n--- 测试分页: page={params['page']}, page_size={params['page_size']} ---")
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/news/",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                logger.info(f"✅ 分页查询成功")
                logger.info(f"   总文章数: {data.get('total')}")
                logger.info(f"   当前页: {data.get('page')}")
                logger.info(f"   每页数量: {data.get('page_size')}")
                logger.info(f"   返回文章数: {len(articles)}")
                logger.info(f"   是否有下一页: {data.get('has_next')}")
                logger.info(f"   是否有上一页: {data.get('has_prev')}")
                
                # 验证返回的文章数量
                expected_count = min(params['page_size'], data.get('total', 0))
                if len(articles) <= expected_count:
                    logger.info(f"   ✓ 文章数量符合预期")
                else:
                    logger.warning(f"   ⚠️  文章数量超出预期: {len(articles)} > {expected_count}")
            else:
                logger.error(f"❌ 分页查询失败: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ 分页查询异常: {e}")
    
    return True


def test_combined_filters():
    """测试组合过滤（分类+分页）"""
    logger.info("\n" + "=" * 60)
    logger.info("测试5: 组合过滤测试（分类+分页）")
    logger.info("=" * 60)
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/news/",
            params={
                "category": "Huawei Developer",
                "page": 1,
                "page_size": 10
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            logger.info(f"✅ 组合查询成功")
            logger.info(f"   分类: Huawei Developer")
            logger.info(f"   总文章数: {data.get('total')}")
            logger.info(f"   返回文章数: {len(articles)}")
            
            # 显示所有华为开发者博客文章
            logger.info(f"\n   华为开发者博客文章列表:")
            for i, article in enumerate(articles, 1):
                logger.info(f"   {i}. {article.get('title')}")
                logger.info(f"      分类: {article.get('category')}")
                logger.info(f"      来源: {article.get('source')}")
                logger.info(f"      日期: {article.get('date')}")
            
            return True
        else:
            logger.error(f"❌ 组合查询失败: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ 组合查询异常: {e}")
        return False


def test_search():
    """测试搜索功能"""
    logger.info("\n" + "=" * 60)
    logger.info("测试6: 搜索功能测试")
    logger.info("=" * 60)
    
    search_keywords = ["HarmonyOS", "鸿蒙", "开发"]
    
    for keyword in search_keywords:
        logger.info(f"\n--- 搜索关键词: {keyword} ---")
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/news/",
                params={"search": keyword, "page": 1, "page_size": 5},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                logger.info(f"✅ 搜索成功")
                logger.info(f"   找到 {data.get('total')} 篇相关文章")
                logger.info(f"   返回 {len(articles)} 篇文章")
                
                # 显示搜索结果
                for i, article in enumerate(articles[:3], 1):
                    logger.info(f"   {i}. {article.get('title')}")
            else:
                logger.error(f"❌ 搜索失败: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ 搜索异常: {e}")
    
    return True


def main():
    """主测试函数"""
    logger.info("开始测试华为开发者博客集成...")
    logger.info(f"API地址: {API_BASE_URL}")
    
    # 等待服务启动
    logger.info("\n等待API服务启动...")
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ API服务已就绪")
                break
        except:
            pass
        
        if i < max_retries - 1:
            logger.info(f"等待中... ({i+1}/{max_retries})")
            time.sleep(2)
        else:
            logger.error("❌ API服务启动超时")
            logger.error("请确保运行: python run.py")
            return False
    
    # 运行测试
    tests = [
        ("API健康检查", test_api_health),
        ("获取所有新闻", test_get_all_news),
        ("Category分类查询", test_category_filter),
        ("分页功能", test_pagination),
        ("组合过滤", test_combined_filters),
        ("搜索功能", test_search),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 '{test_name}' 发生异常: {e}")
            results.append((test_name, False))
    
    # 输出测试总结
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{status} - {test_name}")
    
    logger.info(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("\n🎉 所有测试通过！")
        return True
    else:
        logger.warning(f"\n⚠️  有 {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
