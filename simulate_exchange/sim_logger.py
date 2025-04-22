import logging
import os
from datetime import datetime

# 创建日志目录
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 生成日志文件名，包含日期
log_file = os.path.join(log_dir, f'simulate_exchange_{datetime.now().strftime("%Y%m%d")}.log')

# 创建logger
logger = logging.getLogger('simulate_exchange')
logger.setLevel(logging.INFO)

# 清除已有的处理器，避免重复
if logger.handlers:
    logger.handlers.clear()

# 创建文件处理器
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 创建格式化器
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加处理器到logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)