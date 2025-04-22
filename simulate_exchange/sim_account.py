import os
import json
import pandas as pd
from datetime import datetime
from sim_logger import logger  # 修改为使用本地的sim_logger
from base_account import BaseAccount

class SimAccount(BaseAccount):
    """
    模拟账户类
    用于模拟实盘交易账户，保持与真实账户一致的属性
    支持数据持久化，确保每次重启时能保持数据一致性
    """
    def __init__(self, account_id, data_dir="sim_data", initial_cash=1000000.0):
        """
        初始化模拟账户
        :param account_id: 账户ID
        :param data_dir: 数据存储目录
        :param initial_cash: 初始资金
        """
        # 调整data_dir路径，使其位于simulate_exchange的上一级目录
        adjusted_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), data_dir)
        
        # 调用父类初始化方法
        super().__init__(account_id, adjusted_data_dir, initial_cash)
        
        logger.info(f"模拟账户 {account_id} 初始化完成，总资产: {self.total_asset:.2f}")
    
    def update_position(self, stock_code, trade_type, amount, price, commission_rate):
        """
        更新持仓
        :param stock_code: 股票代码
        :param trade_type: 交易类型，'buy'表示买入增加持仓，'sell'表示卖出减少持仓
        :param amount: 交易数量
        :param price: 交易价格
        :param commission_rate: 手续费率
        :return: 是否更新成功
        """
        try:
            # 计算交易金额和手续费
            trade_value = amount * price
            commission = trade_value * commission_rate
            
            # 记录交易时间
            trade_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if trade_type == 'buy':
                # 检查资金是否足够
                if self.cash < trade_value + commission:
                    logger.warning(f"资金不足，无法买入: 需要 {trade_value + commission:.2f}, 可用 {self.cash:.2f}")
                    return False
                
                # 更新资金
                self.cash -= (trade_value + commission)
                self.free_cash = self.cash  # 更新可用资金
                self.commission += commission
                
                # 更新持仓
                if stock_code in self.positions:
                    # 计算新的持仓成本和数量
                    old_amount = self.positions[stock_code]['volume']
                    old_cost = self.positions[stock_code]['cost']
                    new_amount = old_amount + amount
                    new_cost = old_cost + trade_value
                    
                    # 更新持仓信息
                    self.positions[stock_code]['volume'] = new_amount
                    self.positions[stock_code]['can_use_volume'] = new_amount
                    self.positions[stock_code]['cost'] = new_cost
                    self.positions[stock_code]['avg_price'] = new_cost / new_amount
                    self.positions[stock_code]['market_value'] = new_amount * price
                    self.positions[stock_code]['updated_at'] = trade_time
                else:
                    # 新建持仓
                    self.positions[stock_code] = {
                        'code': stock_code,  # 兼容BaseAccount
                        'stock_code': stock_code,
                        'volume': amount,
                        'can_use_volume': amount,  # 可用数量
                        'frozen_volume': 0,        # 冻结数量
                        'cost': trade_value,
                        'avg_price': price,
                        'open_price': price,       # 记录第一次买入价格
                        'last_price': price,       # 最新价格
                        'market_value': trade_value,
                        'profit': 0.0,
                        'profit_ratio': 0.0,
                        'created_at': trade_time,
                        'updated_at': trade_time
                    }
                
                logger.info(f"买入成功: 股票 {stock_code}, 数量 {amount}, 价格 {price:.2f}, 交易额 {trade_value:.2f}, 手续费 {commission:.2f}")
                
            elif trade_type == 'sell':
                # 检查持仓是否足够
                if stock_code not in self.positions or self.positions[stock_code]['volume'] < amount:
                    logger.warning(f"持仓不足，无法卖出: 需要 {amount}, 可用 {self.positions.get(stock_code, {}).get('volume', 0)}")
                    return False
                
                # 计算卖出部分的成本
                old_amount = self.positions[stock_code]['volume']
                old_cost = self.positions[stock_code]['cost']
                sell_cost_ratio = amount / old_amount
                sell_cost = old_cost * sell_cost_ratio
                
                # 计算卖出收益
                sell_profit = trade_value - sell_cost - commission
                
                # 更新资金
                self.cash += (trade_value - commission)
                self.free_cash = self.cash  # 更新可用资金
                self.commission += commission
                
                # 更新持仓
                new_amount = old_amount - amount
                if new_amount > 0:
                    # 更新持仓信息
                    new_cost = old_cost * (1 - sell_cost_ratio)
                    self.positions[stock_code]['volume'] = new_amount
                    self.positions[stock_code]['can_use_volume'] = new_amount
                    self.positions[stock_code]['cost'] = new_cost
                    self.positions[stock_code]['avg_price'] = new_cost / new_amount
                    self.positions[stock_code]['last_price'] = price
                    self.positions[stock_code]['market_value'] = new_amount * price
                    self.positions[stock_code]['updated_at'] = trade_time
                else:
                    # 清空持仓
                    del self.positions[stock_code]
                
                logger.info(f"卖出成功: 股票 {stock_code}, 数量 {amount}, 价格 {price:.2f}, 交易额 {trade_value:.2f}, 手续费 {commission:.2f}, 收益 {sell_profit:.2f}")
            
            else:
                logger.warning(f"不支持的交易类型: {trade_type}")
                return False
            
            # 添加交易记录
            trade_record = {
                'trade_id': f"{stock_code}_{trade_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'stock_code': stock_code,
                'trade_type': trade_type,
                'amount': amount,
                'price': price,
                'trade_value': trade_value,
                'commission': commission,
                'trade_time': trade_time
            }
            
            if trade_type == 'sell':
                trade_record['profit'] = sell_profit
            
            self.trades.append(trade_record)
            
            # 更新市值和总资产
            self._update_market_value()
            
            # 保存数据
            self._save_account()
            self._save_positions()
            self._save_trades()
            
            return True
            
        except Exception as e:
            logger.error(f"更新持仓失败: {e}", exc_info=True)
            return False
    
    def update_prices(self, price_dict):
        """
        更新持仓股票的最新价格
        :param price_dict: 股票代码 -> 最新价格的字典
        """
        # 直接调用父类的update_price方法
        return self.update_price(price_dict)

def unit_test():
    """单元测试函数已移至unit_test_sim_account.py"""
    from unit_test_sim_account import unit_test
    unit_test()

if __name__ == '__main__':
    unit_test()

