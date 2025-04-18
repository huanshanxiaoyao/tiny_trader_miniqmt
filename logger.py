import logging
from logging.handlers import RotatingFileHandler
import os

# 创建日志目录
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 创建主日志记录器
logger = logging.getLogger('main')
logger.setLevel(logging.INFO)

# 创建终端输出处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# 主日志文件处理器（保留原有的配置）
main_handler = RotatingFileHandler(
    os.path.join(log_dir, 'main.log'),
    maxBytes=16*1024*1024,  # 16MB
    backupCount=2,
    encoding='utf-8'
)
main_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(main_handler)

# 创建TICK数据专用的处理器
tick_handler = RotatingFileHandler(
    os.path.join(log_dir, 'tick.log'),
    maxBytes=50*1024*1024,  # 50MB
    backupCount=2,
    encoding='utf-8'
)
tick_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))

# 创建TICK专用的日志记录器
tick_logger = logging.getLogger('tick')
tick_logger.setLevel(logging.INFO)
tick_logger.addHandler(tick_handler)