"""
SimTrader单元测试
测试模拟交易类的主要功能
"""
import os
import time
from datetime import datetime
import pandas as pd
from sim_account import SimAccount
from sim_trader import SimTrader

def unit_test():
    """
    SimTrader单元测试
    测试模拟交易的主要功能
    """
    # 创建测试账户
    account_id = 'test_trader_account'
    initial_cash = 1000000.0
    account = SimAccount(account_id, initial_cash)
    
    # 创建模拟交易接口
    trader = SimTrader(account)
    
    print("===== 测试模拟交易接口初始化 =====")
    print(f"交易延迟: {trader.trade_delay}秒")
    print(f"手续费率: {trader.commission_rate}")
    print(f"待处理订单数量: {len(trader.get_pending_orders())}")
    print(f"交易历史记录数量: {len(trader.get_trade_history())}")
    
    # 打印账户信息
    trader.print_summary()
    
    # 测试下单功能（无行情数据时）
    print("\n===== 测试下单功能（无行情数据时） =====")
    stock_code1 = "000001.SZ"
    buy_amount1 = 1000
    buy_price1 = 15.5
    
    order_id1 = trader.buy_stock(stock_code1, buy_amount1, buy_price1, "测试买入")
    print(f"订单ID: {order_id1}")
    
    # 检查待处理订单
    pending_orders = trader.get_pending_orders()
    print(f"待处理订单数量: {len(pending_orders)}")
    if pending_orders:
        order = pending_orders[0]
        print(f"订单状态: {order['status']}")
        print(f"股票代码: {order['stock_code']}")
        print(f"交易类型: {order['trade_type']}")
        print(f"交易数量: {order['amount']}")
        print(f"委托价格: {order['price']}")
    
    # 测试行情触发功能
    print("\n===== 测试行情触发功能 =====")
    # 模拟行情数据
    tick_data = {
        'time': 1744767365000, 
        'lastPrice': 15.45, 
        'open': 15.30, 
        'high': 15.88, 
        'low': 15.25, 
        'lastClose': 15.31, 
        'amount': 82508100.0, 
        'volume': 20528, 
        'pvolume': 20528, 
        'stockStatus': 0, 
        'openInt': 13, 
        'transactionNum': 0, 
        'lastSettlementPrice': 0.0, 
        'settlementPrice': 0.0, 
        'pe': 83.60, 
        'askPrice': [15.55, 15.60, 15.65, 15.70, 15.75], 
        'bidPrice': [15.40, 15.35, 15.30, 15.25, 15.20], 
        'askVol': [12, 1, 14, 33, 4], 
        'bidVol': [19, 5, 33, 10, 10], 
        'volRatio': 0.0, 
        'speed1Min': 0.0, 
        'speed5Min': 0.0
    }
    
    ticks = {stock_code1: tick_data}
    trader.realtime_trigger(ticks)
    
    # 检查订单是否仍在待处理（买入价格低于卖一价，不会成交）
    pending_orders = trader.get_pending_orders()
    print(f"行情触发后待处理订单数量: {len(pending_orders)}")
    
    # 测试可以成交的情况
    print("\n===== 测试可以成交的情况 =====")
    # 提高买入价格，使其高于卖一价
    buy_price2 = 15.6
    order_id2 = trader.buy_stock(stock_code1, buy_amount1, buy_price2, "测试买入（可成交）")
    
    # 行情触发
    trader.realtime_trigger(ticks)
    
    # 检查订单是否已成交
    pending_orders = trader.get_pending_orders()
    print(f"行情触发后待处理订单数量: {len(pending_orders)}")
    
    # 检查交易历史
    trade_history = trader.get_trade_history()
    print(f"交易历史记录数量: {len(trade_history)}")
    if trade_history:
        trade = trade_history[0]
        print(f"成交订单ID: {trade['order_id']}")
        print(f"成交状态: {trade['status']}")
        print(f"成交价格: {trade['execution_price']}")
        print(f"实际交易金额: {trade['actual_trade_value']}")
    
    # 检查账户持仓
    print("\n===== 检查账户持仓 =====")
    positions = account.get_positions()
    if stock_code1 in positions:
        position = positions[stock_code1]
        print(f"股票代码: {stock_code1}")
        print(f"持仓数量: {position['volume']}")
        print(f"持仓成本: {position['cost']:.2f}")
        print(f"平均成本: {position['avg_price']:.2f}")
    
    # 测试卖出功能
    print("\n===== 测试卖出功能 =====")
    # 更新行情数据（提高买一价）
    tick_data['bidPrice'] = [15.70, 15.65, 15.60, 15.55, 15.50]
    trader.realtime_trigger(ticks)
    
    # 卖出部分持仓
    sell_amount = 500
    sell_price = 15.65  # 低于买一价，应该可以成交
    order_id3 = trader.sell_stock(stock_code1, sell_amount, sell_price, "测试卖出")
    
    # 行情触发
    trader.realtime_trigger(ticks)
    
    # 检查交易历史
    trade_history = trader.get_trade_history()
    print(f"交易历史记录数量: {len(trade_history)}")
    
    # 检查账户持仓
    positions = account.get_positions()
    if stock_code1 in positions:
        position = positions[stock_code1]
        print(f"卖出后持仓数量: {position['volume']}")
    
    # 测试取消订单功能
    print("\n===== 测试取消订单功能 =====")
    # 创建一个新订单
    order_id4 = trader.sell_stock(stock_code1, 100, 16.0, "测试取消")
    
    # 取消订单
    cancel_result = trader.cancel_order(order_id4)
    print(f"取消订单结果: {'成功' if cancel_result else '失败'}")
    
    # 检查待处理订单
    pending_orders = trader.get_pending_orders()
    print(f"取消后待处理订单数量: {len(pending_orders)}")
    
    # 测试获取交易历史DataFrame
    print("\n===== 测试获取交易历史DataFrame =====")
    trades_df = trader.get_trade_history_df()
    if not trades_df.empty:
        print(f"交易历史DataFrame行数: {len(trades_df)}")
        print(f"交易历史DataFrame列: {list(trades_df.columns)}")
        print("交易历史DataFrame前2行:")
        print(trades_df.head(2)[['order_id', 'stock_code', 'trade_type', 'amount', 'price', 'execution_price', 'status']])
    
    # 测试多个股票同时触发
    print("\n===== 测试多个股票同时触发 =====")
    # 添加另一只股票的行情
    stock_code2 = "600000.SH"
    tick_data2 = tick_data.copy()
    tick_data2['lastPrice'] = 12.5
    tick_data2['askPrice'] = [12.55, 12.60, 12.65, 12.70, 12.75]
    tick_data2['bidPrice'] = [12.45, 12.40, 12.35, 12.30, 12.25]
    
    # 下单
    order_id5 = trader.buy_stock(stock_code2, 800, 12.60, "测试多股票")
    
    # 更新行情
    ticks = {stock_code1: tick_data, stock_code2: tick_data2}
    trader.realtime_trigger(ticks)
    
    # 检查交易历史
    trade_history = trader.get_trade_history()
    print(f"多股票触发后交易历史记录数量: {len(trade_history)}")
    
    # 检查账户持仓
    positions = account.get_positions()
    print(f"账户持仓股票数量: {len(positions)}")
    for code, position in positions.items():
        print(f"股票代码: {code}, 持仓数量: {position['volume']}")
    
    # 测试异常情况
    print("\n===== 测试异常情况 =====")
    # 测试交易数量为0
    order_id_invalid = trader.buy_stock(stock_code1, 0, 15.5, "测试无效数量")
    print(f"无效数量订单ID: {order_id_invalid}")
    
    # 测试资金不足
    large_amount = 10000000
    order_id_large = trader.buy_stock(stock_code1, large_amount, 15.5, "测试资金不足")
    trader.realtime_trigger(ticks)
    
    # 检查订单状态
    for order in trader.pending_orders:
        if order['order_id'] == order_id_large:
            print(f"资金不足订单状态: {order['status']}")
    
    # 清理测试数据
    print("\n===== 清理测试数据 =====")
    account.reset()
    print("测试完成，账户已重置")

if __name__ == '__main__':
    unit_test()