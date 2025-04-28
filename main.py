import time
from datetime import datetime
import argparse
from xtquant import xtdata
from mini_trader import MiniTrader
from data_provider import DataProvider
from risk_manager import RiskManager
from local_account import LocalAccount
from strategy.strategy_factory import StrategyFactory
from strategy.strategy_params import STRATEGY_PARAMS, Active_Codes
from config import ACCOUNT_ID, TRADER_PATH, STRATEGY_CONFIG, DATA_CONFIG
from stock_code_config import BASKET1, BASKET2, BASKET3, CODE2RELATED,SH50,BJ50
from stock_code_config import BJSE_INDEX, SHSE_INDEX, HS_INDEX
from my_stock import MyStock
from logger import logger, tick_logger  # 修改导入语句
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

    #TODO 这里需要再思考一下，由于是先注册stock再注册策略，同时为了避免太多浪费，所以还需要一个个集合的hardcord在这里
    active_codes = Active_Codes
    #active_codes.extend(BASKET1)

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
    global strategies, risk_manager, trader, using_account, id2stock
    logger.info(f"接收行情数据: 数量={len(ticks)}, 股票代码列表={list(ticks.keys())}")
    #index_ticks = xtdata.get_full_tick(['899050.BJ'])
    #logger.info(f"指数行情数据: {index_ticks}")
    if using_account.is_simulated:
        trader.realtime_trigger(ticks)
    for code, tick in ticks.items():
        tick_logger.info(f"{code} : {tick}")  # 使用专门的tick_logger
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
    reviewed_signals = risk_manager.evaluate_signals(all_signals, using_account)
    if not reviewed_signals:
        return
    
    # 执行交易
    for stock, trade_type, amount, remark in reviewed_signals:
        if trade_type == 'buy':
            ret = trader.buy_stock(stock.code, amount, remark=f'{remark}')
        else:
            ret = trader.sell_stock(stock.code, amount, remark=f'{remark}')
        
        logger.info(f"执行交易: {trade_type} {stock.code} {amount}, ret: {ret}")

    #实盘实操的时候，需要从trader接口拉取服务器上的账户和交易信息，实盘模拟的时候，再simTrader里面直接调用了
    #所有这里只对实盘实操的时候生效
    if not using_account.is_simulated and (len(reviewed_signals) > 0 or using_account.need_update()):
        using_account.update_positions(trader.get_account_info(), trader.get_positions(), trader.get_trades(), id2stock)

# 在main函数中，修改模拟交易部分的代码
def main(use_sim=False, account_id=ACCOUNT_ID):
    """
    主函数
    :param use_sim: 是否使用模拟交易
    :param account_id: 交易账户ID
    """
    global data_provider, risk_manager, trader, using_account, id2stock
    
    logger.info(f"交易程序启动时间: {datetime.now()}")
            
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
    
    try:
        # 根据参数选择使用实盘交易还是模拟交易
        if use_sim:
            # 导入模拟交易所和模拟账户
            from simulate_exchange.sim_account import SimAccount
            from simulate_exchange.sim_trader import SimTrader
            from simulate_exchange.sim_config import SIM_ACCOUNT_ID1
            
            logger.info(f"使用模拟交易模式，账户ID: {account_id}")
            
            # 创建模拟账户和模拟交易接口
            sim_account = SimAccount(account_id)
            trader = SimTrader(sim_account)

            #mini_trader = MiniTrader(TRADER_PATH, account_id)
            #mini_trader.connect()
            using_account = sim_account

        else:
            # 使用实盘交易
            logger.info(f"使用实盘交易模式，账户ID: {account_id}")
            trader = MiniTrader(TRADER_PATH, account_id)
                    # 连接交易接口
            if not trader.connect():
                logger.error("交易接口连接失败，程序退出")
                return

            # 打印账户信息
            trader.print_summary()
            local_account = LocalAccount(ACCOUNT_ID)
            using_account = local_account
            using_account.update_positions(trader.get_account_info(), trader.get_positions(), trader.get_trades(), id2stock)
  
        # 订阅行情
        stock_codes = list(id2stock.keys())
        index_codes = [SHSE_INDEX, HS_INDEX, BJSE_INDEX]
        stock_codes.extend(index_codes)
        logger.info(f"订阅行情: {stock_codes}")
        xtdata.subscribe_whole_quote(stock_codes, callback=on_tick_data)
        
        # 主循环，保持程序运行,且做部分更新等判断
        round_count = 0
        while True:
            time.sleep(0.1)
            round_count += 1
            
    except KeyboardInterrupt:
        logger.info("\n程序手动终止")
    except Exception as e:
        logger.error(f"程序异常终止: {e}", exc_info=True)
    finally:
        # 取消订阅
        xtdata.unsubscribe_quote(list(id2stock.keys()))
        logger.info(f"程序结束时间: {datetime.now()}")

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='量化交易程序')
    parser.add_argument('--sim', action='store_true', help='使用模拟交易模式')
    parser.add_argument('--account', type=str, default="sim_id1", help='指定交易账户ID')
    
    args = parser.parse_args()
    
    # 将解析后的参数传递给main函数
    if args.sim:
        main(use_sim=args.sim, account_id=args.account)
    else:
        ###实盘交易
        main()