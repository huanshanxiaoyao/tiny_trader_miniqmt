import os
import json
import pandas as pd
from datetime import datetime
from sim_account import SimAccount
import sys

# 使用本地的sim_logger替代上层的logger
from sim_logger import logger

def unit_test():
    # 创建测试账户
    account_id = 'test_account2'
    initial_cash = 100000.0
    account = SimAccount(account_id, 'test_data', initial_cash)
    
    # 测试初始账户信息
    print("===== 初始账户信息 =====")
    account_info = account.get_account_info()
    print(f"账户ID: {account_info['account_id']}")
    print(f"可用资金: {account_info['cash']:.2f}")
    print(f"总资产: {account_info['total_asset']:.2f}")
    print(f"持仓数量: {account_info['position_count']}")
    
    # 测试买入股票
    print("\n===== 测试买入股票 =====")
    stock_code1 = "000001.SZ"
    buy_amount1 = 1000
    buy_price1 = 15.5
    commission_rate = 0.0003
    
    success = account.update_position(stock_code1, 'buy', buy_amount1, buy_price1, commission_rate)
    print(f"买入结果: {'成功' if success else '失败'}")
    
    # 测试账户信息更新
    print("\n===== 买入后账户信息 =====")
    account_info = account.get_account_info()
    print(f"可用资金: {account_info['cash']:.2f}")
    print(f"持仓市值: {account_info['market_value']:.2f}")
    print(f"总资产: {account_info['total_asset']:.2f}")
    print(f"持仓数量: {account_info['position_count']}")
    
    # 测试持仓信息
    print("\n===== 持仓信息 =====")
    positions = account.get_positions()
    for code, position in positions.items():
        print(f"股票代码: {code}")
        print(f"持仓数量: {position['volume']}")
        print(f"持仓成本: {position['cost']:.2f}")
        print(f"平均成本: {position['avg_price']:.2f}")
        print(f"开仓价格: {position['open_price']:.2f}")
        print(f"市值: {position['market_value']:.2f}")
    
    # 测试再次买入同一只股票
    print("\n===== 测试再次买入同一只股票 =====")
    buy_amount2 = 500
    buy_price2 = 16.0
    success = account.update_position(stock_code1, 'buy', buy_amount2, buy_price2, commission_rate)
    print(f"买入结果: {'成功' if success else '失败'}")
    
    # 测试持仓信息更新
    print("\n===== 再次买入后持仓信息 =====")
    positions = account.get_positions()
    position = positions[stock_code1]
    print(f"持仓数量: {position['volume']}")
    print(f"持仓成本: {position['cost']:.2f}")
    print(f"平均成本: {position['avg_price']:.2f}")
    print(f"开仓价格: {position['open_price']:.2f}")  # 应该保持不变
    print(f"市值: {position['market_value']:.2f}")
    
    # 测试买入另一只股票
    print("\n===== 测试买入另一只股票 =====")
    stock_code2 = "600000.SH"
    buy_amount3 = 800
    buy_price3 = 12.8
    success = account.update_position(stock_code2, 'buy', buy_amount3, buy_price3, commission_rate)
    print(f"买入结果: {'成功' if success else '失败'}")
    
    # 测试账户信息更新
    print("\n===== 买入第二只股票后账户信息 =====")
    account_info = account.get_account_info()
    print(f"可用资金: {account_info['cash']:.2f}")
    print(f"持仓市值: {account_info['market_value']:.2f}")
    print(f"总资产: {account_info['total_asset']:.2f}")
    print(f"持仓数量: {account_info['position_count']}")
    
    # 测试更新股票价格
    print("\n===== 测试更新股票价格 =====")
    price_dict = {
        stock_code1: 17.2,  # 价格上涨
        stock_code2: 12.5   # 价格下跌
    }
    account.update_prices(price_dict)
    
    # 测试价格更新后的持仓信息
    print("\n===== 价格更新后持仓信息 =====")
    positions = account.get_positions()
    for code, position in positions.items():
        print(f"股票代码: {code}")
        print(f"持仓数量: {position['volume']}")
        print(f"最新价格: {position.get('last_price', '未知')}")
        print(f"市值: {position['market_value']:.2f}")
        print(f"盈亏: {position['profit']:.2f}")
        print(f"盈亏比例: {position['profit_ratio']:.4f}")
    
    return 
    
    # 测试账户信息更新
    print("\n===== 价格更新后账户信息 =====")
    account_info = account.get_account_info()
    print(f"可用资金: {account_info['cash']:.2f}")
    print(f"持仓市值: {account_info['market_value']:.2f}")
    print(f"总资产: {account_info['total_asset']:.2f}")
    
    # 测试卖出部分持仓
    print("\n===== 测试卖出部分持仓 =====")
    sell_amount1 = 600
    sell_price1 = 17.5
    success = account.update_position(stock_code1, 'sell', sell_amount1, sell_price1, commission_rate)
    print(f"卖出结果: {'成功' if success else '失败'}")
    
    # 测试卖出后的持仓信息
    print("\n===== 卖出后持仓信息 =====")
    positions = account.get_positions()
    position = positions.get(stock_code1)
    if position:
        print(f"股票代码: {stock_code1}")
        print(f"持仓数量: {position['volume']}")
        print(f"持仓成本: {position['cost']:.2f}")
        print(f"平均成本: {position['avg_price']:.2f}")
    else:
        print(f"股票 {stock_code1} 已清仓")
    
    # 测试卖出全部持仓
    print("\n===== 测试卖出全部持仓 =====")
    # 获取剩余持仓数量
    remaining_amount = positions[stock_code1]['volume'] if stock_code1 in positions else 0
    if remaining_amount > 0:
        sell_price2 = 17.8
        success = account.update_position(stock_code1, 'sell', remaining_amount, sell_price2, commission_rate)
        print(f"卖出结果: {'成功' if success else '失败'}")
    
    # 测试清仓后的持仓信息
    print("\n===== 清仓后持仓信息 =====")
    positions = account.get_positions()
    if stock_code1 in positions:
        print(f"股票 {stock_code1} 仍有持仓")
    else:
        print(f"股票 {stock_code1} 已成功清仓")
    
    # 测试最终账户信息
    print("\n===== 最终账户信息 =====")
    account_info = account.get_account_info()
    print(f"可用资金: {account_info['cash']:.2f}")
    print(f"持仓市值: {account_info['market_value']:.2f}")
    print(f"总资产: {account_info['total_asset']:.2f}")
    print(f"持仓数量: {account_info['position_count']}")
    
    # 测试交易记录
    print("\n===== 交易记录 =====")
    trades_df = account.get_trades_df()
    if not trades_df.empty:
        print(f"交易记录数量: {len(trades_df)}")
        print(trades_df[['stock_code', 'trade_type', 'amount', 'price', 'trade_value', 'commission', 'trade_time']])
    else:
        print("无交易记录")
    
    # 重置账户
    #print("\n===== 重置账户 =====")
    #account.reset()
    #account_info = account.get_account_info()
    #print(f"重置后可用资金: {account_info['cash']:.2f}")
    #print(f"重置后持仓数量: {account_info['position_count']}")

if __name__ == '__main__':
    unit_test()