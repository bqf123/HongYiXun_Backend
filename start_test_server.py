"""
启动测试服务器的辅助脚本
"""

import subprocess
import sys
import time
import requests
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_server_running():
    """检查服务器是否已经在运行"""
    try:
        response = requests.get("http://localhost:8001/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def main():
    logger.info("=" * 60)
    logger.info("华为开发者博客爬虫 - 测试服务器启动脚本")
    logger.info("=" * 60)
    
    # 检查服务器是否已经在运行
    if check_server_running():
        logger.info("✅ 服务器已经在运行")
        logger.info("   API地址: http://localhost:8001")
        logger.info("   API文档: http://localhost:8001/docs")
        logger.info("\n你可以直接运行测试脚本:")
        logger.info("   python test_huawei_developer_integration.py")
        return
    
    logger.info("正在启动服务器...")
    logger.info("这可能需要几分钟时间，请耐心等待...")
    
    try:
        # 启动服务器
        process = subprocess.Popen(
            [sys.executable, "run.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待服务器启动
        max_wait = 60  # 最多等待60秒
        for i in range(max_wait):
            if check_server_running():
                logger.info(f"\n✅ 服务器启动成功！")
                logger.info(f"   API地址: http://localhost:8001")
                logger.info(f"   API文档: http://localhost:8001/docs")
                logger.info(f"\n现在可以运行测试脚本:")
                logger.info(f"   python test_huawei_developer_integration.py")
                logger.info(f"\n按 Ctrl+C 停止服务器")
                
                # 保持服务器运行
                try:
                    process.wait()
                except KeyboardInterrupt:
                    logger.info("\n正在停止服务器...")
                    process.terminate()
                    process.wait()
                    logger.info("服务器已停止")
                return
            
            time.sleep(1)
            if i % 5 == 0:
                logger.info(f"等待服务器启动... ({i}/{max_wait}秒)")
        
        logger.error("❌ 服务器启动超时")
        process.terminate()
        
    except Exception as e:
        logger.error(f"❌ 启动服务器失败: {e}")
        logger.error("\n请手动启动服务器:")
        logger.error("   python run.py")


if __name__ == "__main__":
    main()
