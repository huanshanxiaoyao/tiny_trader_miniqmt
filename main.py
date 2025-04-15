import time
from datetime import datetime
from xtquant import xtdata
from mini_trader import MiniTrader
from data_provider import DataProvider
from risk_manager import RiskManager
from strategy.strategy_factory import StrategyFactory
from config import ACCOUNT_ID, TRADER_PATH, STRATEGY_CONFIG, DATA_CONFIG
from config import BASKET1, BASKET2, BASKET3, CODE2RELATED
from my_stock import MyStock
from logger import logger
import os
import sys

# 将项目根目录添加到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 全局变量
id2stock = {}  # 股票代码到MyStock对象的映射
strategies = []  # 策略列表
data_provider = None  # 数据提供者
risk_manager = None  # 风险管理器
trader = None  # 交易接口

def init_stocks():
    """初始化股票对象"""
    global id2stock
    logger.info("初始化股票对象...")

    active_codes = []
    active_codes.extend(BASKET1)
    active_codes.extend(BASKET2)
    active_codes.extend(BASKET3)
    for values in CODE2RELATED.values():
        active_codes.extend(values)
    logger.info(f"活跃股票数量: {active_codes}")
  
    # 为配置中的股票创建MyStock对象
    for code in active_codes:
        if code not in id2stock:
            id2stock[code] = MyStock(code)
            logger.info(f"创建股票对象: {code}")
    
    logger.info(f"共创建 {len(id2stock)} 个股票对象")
    return True

def init_strategies():
    """初始化策略"""
    global strategies, id2stock
    logger.info("初始化策略...")
    
    factory = StrategyFactory()
    for strategy_id in STRATEGY_CONFIG["enabled_strategies"]:
        # 创建策略实例
        strategy = factory.create_strategy(strategy_id)
        
        # 设置策略的目标股票对象
        target_stocks = []
        for code in strategy.target_codes:
            if code in id2stock:
                target_stocks.append(id2stock[code])
            else:
                logger.warning(f"警告: 股票 {code} 未初始化")
        
        strategy.target_stocks = target_stocks
        strategies.append(strategy)
        
        logger.info(f"创建策略: {strategy_id}, 目标股票数量: {len(target_stocks)}")
    
    logger.info(f"共创建 {len(strategies)} 个策略")
    return True

def prepare_data():
    """准备历史数据"""
    global data_provider, strategies
    logger.info("准备历史数据...")
    
    # 为每个策略准备数据
    for strategy in strategies:
        success = strategy.fill_data(data_provider)
        if not success:
            logger.warning(f"警告: 策略 {strategy.__class__.__name__} 数据准备失败")
        else:
            logger.info(f"策略 {strategy.__class__.__name__} 数据准备完成")
    
    return True

def on_tick_data(ticks):
    """
    行情数据回调函数
    :param ticks: 股票行情数据字典
    """
    global strategies, risk_manager, trader
    logger.info(f"接收行情数据: 数量={len(ticks)}, 股票代码列表={list(ticks.keys())}")
    for code, tick in ticks.items():
        logger.info(f"{code} 最新价: {tick}")
    # 遍历所有策略
    all_signals = []
    for strategy in strategies:
        # 获取策略交易信号
        signals = strategy.trigger(ticks)
        if signals:
            all_signals.extend(signals)
    
    if not all_signals:
        return
    
    # 风险评估
    reviewed_signals = risk_manager.evaluate_signals(all_signals)
    if not reviewed_signals:
        return
    
    # 执行交易
    for stock, trade_type, amount in reviewed_signals:
        if trade_type == 'buy':
            trader.buy_stock(stock, amount * 100, remark=f'strategy_{trade_type}')
        else:
            trader.sell_stock(stock, amount, remark=f'strategy_{trade_type}')
        
        logger.info(f"执行交易: {trade_type} {code} {amount}")

def main():
    """主函数"""
    global data_provider, risk_manager, trader
    
    logger.info(f"交易程序启动时间: {datetime.now()}")
    
    try:
        # 初始化交易接口
        trader = MiniTrader(TRADER_PATH, ACCOUNT_ID)
        if not trader.connect():
            logger.error("交易接口连接失败，程序退出")
            return
        
        # 初始化数据提供者
        data_provider = DataProvider()
        
        # 初始化风险管理器
        risk_manager = RiskManager()
        
        
        # 初始化股票对象
        if not init_stocks():
            logger.error("初始化股票对象失败，程序退出")
            return

        # 初始化策略
        if not init_strategies():
            logger.error("初始化策略失败，程序退出")
            return

        # 准备历史数据
        if not prepare_data():
            logger.error("准备历史数据失败，程序退出")
            return
        
        # 打印账户信息
        trader.print_summary()
  
        # 订阅行情
        stock_codes = list(id2stock.keys())
        stock_codes.append('899050.BJ')
        logger.info(f"订阅行情: {stock_codes}")
        xtdata.subscribe_whole_quote(stock_codes, callback=on_tick_data)
        
        # 主循环，保持程序运行
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        logger.info("\n程序手动终止")
    except Exception as e:
        logger.error(f"程序异常终止: {e}", exc_info=True)
    finally:
        # 取消订阅
        xtdata.unsubscribe_quote(list(id2stock.keys()))
        logger.info(f"程序结束时间: {datetime.now()}")

if __name__ == "__main__":
    main()