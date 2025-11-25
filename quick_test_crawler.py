"""
快速测试华为开发者博客爬虫
"""

import logging
import sys

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_crawler():
    """测试爬虫基本功能"""
    logger.info("=" * 60)
    logger.info("快速测试：华为开发者博客爬虫")
    logger.info("=" * 60)
    
    try:
        logger.info("\n步骤1: 导入爬虫模块...")
        from services.huawei_developer_blog_crawler import HuaweiDeveloperBlogCrawler
        logger.info("✅ 爬虫模块导入成功")
        
        logger.info("\n步骤2: 初始化爬虫...")
        crawler = HuaweiDeveloperBlogCrawler()
        logger.info("✅ 爬虫初始化成功")
        
        logger.info("\n步骤3: 开始爬取文章（最多2篇，用于测试）...")
        logger.info("这可能需要1-2分钟，请耐心等待...")
        articles = crawler.crawl_all(max_articles=2)
        
        if articles:
            logger.info(f"\n✅ 爬取成功！共获取 {len(articles)} 篇文章")
            
            for i, article in enumerate(articles, 1):
                logger.info(f"\n--- 文章 {i} ---")
                logger.info(f"标题: {article.get('title')}")
                logger.info(f"URL: {article.get('url')}")
                logger.info(f"日期: {article.get('date')}")
                logger.info(f"分类: {article.get('category')}")
                logger.info(f"来源: {article.get('source')}")
                logger.info(f"内容块数: {len(article.get('content', []))}")
                logger.info(f"摘要: {article.get('summary', '')[:100]}...")
                
                # 显示前3个内容块
                content = article.get('content', [])
                logger.info(f"\n内容预览（前3块）:")
                for j, block in enumerate(content[:3], 1):
                    block_type = block.get('type')
                    block_value = block.get('value', '')
                    if block_type == 'text':
                        logger.info(f"  {j}. [文本] {block_value[:80]}...")
                    elif block_type == 'image':
                        logger.info(f"  {j}. [图片] {block_value}")
            
            logger.info("\n" + "=" * 60)
            logger.info("🎉 测试成功！爬虫工作正常")
            logger.info("=" * 60)
            logger.info("\n下一步:")
            logger.info("1. 启动服务器: python run.py")
            logger.info("2. 运行完整测试: python test_huawei_developer_integration.py")
            return True
        else:
            logger.warning("\n⚠️  未获取到文章，可能的原因:")
            logger.warning("1. 网络连接问题")
            logger.warning("2. 目标网站结构变化")
            logger.warning("3. Chrome浏览器或驱动问题")
            return False
            
    except ImportError as e:
        logger.error(f"\n❌ 导入错误: {e}")
        logger.error("请确保已安装所有依赖:")
        logger.error("  pip install -r requirements.txt")
        return False
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}")
        logger.error("\n可能的解决方案:")
        logger.error("1. 确保已安装Chrome浏览器")
        logger.error("2. 检查网络连接")
        logger.error("3. 查看详细错误信息")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_crawler()
    sys.exit(0 if success else 1)
