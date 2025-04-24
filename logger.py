import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
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

# 主日志文件处理器（按天轮转）
main_handler = TimedRotatingFileHandler(
    os.path.join(log_dir, 'main.log'),
    when='midnight',  # 每天午夜轮转
    interval=1,       # 间隔为1天
    backupCount=30,   # 保留30天的日志
    encoding='utf-8'
)
main_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
main_handler.suffix = "%Y%m%d"  # 设置日志文件后缀格式为YYYYMMDD
logger.addHandler(main_handler)

# 创建TICK数据专用的处理器（按天轮转）
tick_handler = TimedRotatingFileHandler(
    os.path.join(log_dir, 'tick.log'),
    when='midnight',  # 每天午夜轮转
    interval=1,       # 间隔为1天
    backupCount=30,   # 保留30天的日志
    encoding='utf-8'
)
tick_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
tick_handler.suffix = "%Y%m%d"  # 设置日志文件后缀格式为YYYYMMDD

# 创建TICK专用的日志记录器
tick_logger = logging.getLogger('tick')
tick_logger.setLevel(logging.INFO)
tick_logger.addHandler(tick_handler)