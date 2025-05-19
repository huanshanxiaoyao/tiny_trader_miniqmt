from stock_code_config import *
from dotenv import load_dotenv
import os

load_dotenv()
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
TRADER_PATH = os.getenv("TRADER_PATH")
# 策略配置
STRATEGY_CONFIG = {
    "enabled_strategies": [1001,1004],  # 启用的策略ID列表
    "backtest_strategies": [1002],  # 回测的策略ID列表
}


# 数据配置
DATA_CONFIG = {
    "history_days": 10,          # 历史数据天数
    "market_index": "899050.BJ"  # 市场指数代码
}