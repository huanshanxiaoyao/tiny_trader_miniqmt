import time
from datetime import datetime, timedelta
from data_provider import DataProvider
from strategy.strategy_factory import StrategyFactory
from config import STRATEGY_CONFIG, DATA_CONFIG, SH50, BASKET2, BJ50,BASKET3
from my_stock import MyStock
from logger import logger
from evaluator import Evaluator  # 假设有一个评估器类

def init_stocks(active_codes):
    """初始化股票对象"""
    id2stock = {}
    logger.info("初始化股票对象...")
    
    # 为配置中的股票创建MyStock对象
    for code in active_codes:
        if code not in id2stock:
            id2stock[code] = MyStock(code)
            logger.info(f"创建股票对象: {code}")
    
    logger.info(f"共创建 {len(id2stock)} 个股票对象")
    return id2stock

def init_strategies(id2stock):
    """初始化策略"""
    strategies = []
    logger.info("初始化策略...")
    
    factory = StrategyFactory()
    for strategy_id in STRATEGY_CONFIG["backtest_strategies"]:
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
    return strategies

def main():
    """
    回测主函数
    做一些默认约定，回测数据开始时间点:20240102
    策略模拟开始时间点，选在2024年的第151个交易日,方便部分策略对历史数据的依赖
    对北交所全部股票一起测试，假定有100万资金，看最终收益
    """
    logger.info(f"回测程序启动时间: {datetime.now()}")
    
    try:
        # 初始化数据提供者
        data_provider = DataProvider()
        
        # 初始化评估器
        evaluator = Evaluator()
        
        # 设置回测时间范围
        end_date = "20241231"
        start_date = "20240102"
        trade_days = data_provider.get_trading_calendar(start_date, end_date)
        
        # 初始化股票对象
        active_codes = []
        active_codes.extend(BASKET3)#TODO 先设定为Basket2
        id2stock = init_stocks(active_codes)
        if not id2stock:
            logger.error("初始化股票对象失败，程序退出")
            return

        # 初始化策略
        strategies = init_strategies(id2stock)
        if not strategies:
            logger.error("初始化策略失败，程序退出")
            return

        # 遍历每个策略进行回测
        for strategy in strategies:
            logger.info(f"开始回测策略: {strategy.__class__.__name__}")
            
            # 准备策略数据
            if not strategy.fill_data(data_provider, "20240102", "20241231"):
                logger.error(f"策略 {strategy.__class__.__name__} 数据准备失败，跳过该策略")
                continue
            
            # 执行回测
            signals = strategy.back_test()
            
            if signals:
                logger.info(f"策略 {strategy.__class__.__name__} 产生 {len(signals)} 个交易信号")
                
                # 评估策略表现
                score = evaluator.evaluate_strategy(
                    strategy.__class__.__name__,
                    signals,
                    strategy.target_stocks,
                    strategy.code2daily,
                    trade_days
                )
                
                logger.info(f"策略 {strategy.__class__.__name__} 评分: {score}")
            else:
                logger.warning(f"策略 {strategy.__class__.__name__} 未产生交易信号")
            
        logger.info("回测完成")
            
    except Exception as e:
        logger.error(f"回测过程发生错误: {e}", exc_info=True)
    finally:
        logger.info(f"回测程序结束时间: {datetime.now()}")

if __name__ == "__main__":
    main()