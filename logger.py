import logging
import os
from datetime import datetime

# 确保日志目录存在
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 当前日期作为日志文件名的一部分
current_date = datetime.now().strftime('%Y%m%d')
log_file = os.path.join(log_dir, f'trading_{current_date}.log')

def setup_logger():
    """配置并返回全局日志记录器"""
    # 创建日志记录器
    logger = logging.getLogger('trading')
    logger.setLevel(logging.INFO)
    
    # 如果已经有处理器，不再添加
    if logger.handlers:
        return logger
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 全局日志记录器实例
logger = setup_logger()