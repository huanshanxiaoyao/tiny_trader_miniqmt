from datetime import datetime
import pandas as pd
from sim_logger import logger  # 使用本地的sim_logger

class SimTrader:
    """
    模拟交易类
    用于模拟实盘交易，处理交易请求
    account SimAccount: 模拟账户对象
    """
    class PriceType(Enum):
        """价格类型"""
        LAST_PRICE = 0  # 最新价
        OPEN_PRICE = 1  # 开盘价
        #TODO

    def __init__(self, account):
        # 模拟账户
        self.account = account
        # 待处理的交易请求列表
        self.pending_orders = []
        # 已完成的交易记录
        self.trade_history = []
        # 交易手续费率
        self.commission_rate = 0.0005
        
        self.code2tick = {}
        
        logger.info(f"初始化模拟交易接口，账户ID: {account.account_id}")
    
    def connect(self):
        """连接交易接口"""
        logger.info("连接模拟交易接口成功")
        return True
    
    def buy_stock(self, stock_code, amount, price_type=self.PriceType.LAST_PRICE, price=None, remark=None):
        """
        买入股票
        :param stock_code: 股票代码
        :param amount: 买入数量
        :param price_type: 价格类型 暂时没用，只是为了对其实盘的Trader接口，保持一致
        :param price: 买入价格，如果为None则使用市价
        :param remark: 备注
        :return: 订单ID
        """
        # 如果没有指定价格，则获取当前行情价格
        if price is None and stock_code in self.code2tick:
            tick_data = self.code2tick[stock_code]
            price = tick_data.get('askPrice', [0])[0]  # 使用卖一价
            if price <= 0:
                price = tick_data.get('lastPrice', 0)  # 如果卖一价无效，使用最新价
        
        # 如果仍然没有有效价格，则返回失败
        if price is None or price <= 0:
            logger.warning(f"无法获取有效价格，买入失败: {stock_code}")
            return None
        
        return self.handle_order(self.account, stock_code, 'buy', amount, price, remark)
    
    def sell_stock(self, stock_code, amount, price_type=self.PriceType.LAST_PRICE, price=None, remark=None):
        """
        卖出股票
        :param stock_code: 股票代码
        :param amount: 卖出数量
        :param price_type: 价格类型 暂时没用，只是为了对其实盘的Trader接口，保持一致
        :param price: 卖出价格，如果为None则使用市价
        :param remark: 备注
        :return: 订单ID
        """
        # 如果没有指定价格，则获取当前行情价格
        if price is None and stock_code in self.code2tick:
            tick_data = self.code2tick[stock_code]
            price = tick_data.get('bidPrice', [0])[0]  # 使用买一价
            if price <= 0:
                price = tick_data.get('lastPrice', 0)  # 如果买一价无效，使用最新价
        
        # 如果仍然没有有效价格，则返回失败
        if price is None or price <= 0:
            logger.warning(f"无法获取有效价格，卖出失败: {stock_code}")
            return None
        
        return self.handle_order(self.account, stock_code, 'sell', amount, price, remark)
    
    def get_account_info(self):
        """获取账户信息"""
        return {
            'account_id': self.account.account_id,
            'cash': self.account.cash,
            'total_asset': self.account.total_asset,
            'market_value': self.account.market_value
        }
    
    def get_positions(self):
        """获取持仓信息"""
        return self.account.get_positions()
    
    def print_summary(self):
        """打印账户摘要信息"""
        account_info = self.get_account_info()
        positions = self.get_positions()
        
        logger.info("=" * 50)
        logger.info(f"账户ID: {account_info['account_id']}")
        logger.info(f"可用资金: {account_info['cash']:.2f}")
        logger.info(f"持仓市值: {account_info['market_value']:.2f}")
        logger.info(f"总资产: {account_info['total_asset']:.2f}")
        logger.info(f"持仓数量: {len(positions)}")
        
        if positions:
            logger.info("-" * 50)
            logger.info("持仓明细:")
            for code, position in positions.items():
                logger.info(f"股票: {code}, 数量: {position['volume']}, 可用: {position['can_use_volume']}, "
                           f"成本: {position['avg_price']:.2f}, 市值: {position['market_value']:.2f}")
        
        logger.info("=" * 50)

    def handle_order(self, account, stock_code, trade_type, amount, price, remark=None):
        """
        处理交易请求，添加到列表，并尝试执行
        :param account: 模拟账户对象
        :param stock_code: 待交易股票代码
        :param trade_type: 交易类型 'buy' 或 'sell'
        :param amount: 交易数量
        :param price: 交易价格
        :param remark: 备注
        :return: 订单ID
        """
        try:
            # 生成订单ID
            order_id = f"{stock_code}_{trade_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                  
            # 如果交易数量为0，则不处理
            if amount <= 0:
                logger.warning(f"交易数量为0，不处理订单")
                return None
            
            # 计算交易金额
            trade_value = amount * price
            
            # 计算手续费
            commission = trade_value * self.commission_rate
            
            # 创建订单
            order = {
                'order_id': order_id,
                'stock_code': stock_code,
                'trade_type': trade_type,
                'amount': amount,
                'price': price,
                'trade_value': trade_value,
                'commission': commission,
                'remark': remark,
                'status': 'pending',
                'create_time': datetime.now(),
                'account': account
            }
            
            # 添加到待处理订单列表
            self.pending_orders.append(order)

            # 尝试立即执行订单（原order_trigger逻辑）
            try:
                # 如果有该股票的行情数据，则检查是否可以成交
                if stock_code in self.code2tick:
                    self._check_order_execution(order)
                else:
                    logger.info(f"暂无股票 {stock_code} 的行情数据，订单 {order_id} 将等待行情触发")
            except Exception as e:
                logger.error(f"触发订单处理失败: {e}", exc_info=True)
            
            logger.info(f"创建订单: {order_id}, 股票: {stock_code}, 类型: {trade_type}, 数量: {amount}, 价格: {price}")
            
            return order_id
            
        except Exception as e:
            logger.error(f"处理订单失败: {e}", exc_info=True)
            return None
    
    def realtime_trigger(self, ticks):
        """
        处理实时行情数据，触发订单成交
        :param ticks: 股票代码到行情数据的字典 {code: tick_data}
        """
        try:
            # 构造code2price字典，用于更新账户持仓价格
            code2price = {}
            
            # 更新内部行情缓存
            for code, tick_data in ticks.items():
                self.code2tick[code] = tick_data
                
                # 同时提取lastPrice到code2price字典
                last_price = tick_data.get('lastPrice')
                if last_price is not None and last_price > 0:
                    code2price[code] = last_price
            
            # 调用account的update_price接口更新持仓股票的价格
            if code2price and hasattr(self.account, 'update_price'):
                self.account.update_price(code2price)
            
            # 遍历待处理订单，检查是否可以成交
            pending_orders = self.pending_orders.copy()  # 创建副本避免遍历时修改
            for order in pending_orders:
                self._check_order_execution(order)
            
            # 清理已完成或失败的订单
            self.pending_orders = [order for order in self.pending_orders if order['status'] == 'pending']
            logger.info(f"实时行情触发完成，处理了 {len(ticks)} 只股票的行情数据")
        except Exception as e:
            logger.error(f"处理实时行情数据失败: {e}", exc_info=True)
    
    def _check_order_execution(self, order):
        """
        检查订单是否可以成交
        :param order: 订单信息
        """
        try:
            if order['status'] != 'pending':
                return
            
            stock_code = order['stock_code']
            trade_type = order['trade_type']
            amount = order['amount']
            order_price = order['price']
            
            # 如果没有该股票的行情数据，则无法判断是否可以成交
            if stock_code not in self.code2tick:
                return
            
            tick_data = self.code2tick[stock_code]
            last_price = tick_data.get('lastPrice')
            
            # 如果没有最新价，则无法判断是否可以成交
            if last_price is None:
                return
            
            can_execute = False
            execution_price = order_price  # 默认以委托价格成交
            
            if trade_type == 'buy':
                # 买单成交条件：委托价格 >= 卖一价
                ask_prices = tick_data.get('askPrice', [])
                if isinstance(ask_prices, list) and len(ask_prices) > 0 and order_price >= ask_prices[0]:
                    can_execute = True
                    execution_price = min(order_price, ask_prices[0])  # 以较低的价格成交
            elif trade_type == 'sell':
                # 卖单成交条件：委托价格 <= 买一价
                bid_prices = tick_data.get('bidPrice', [])
                if isinstance(bid_prices, list) and len(bid_prices) > 0 and order_price <= bid_prices[0]:
                    can_execute = True
                    execution_price = max(order_price, bid_prices[0])  # 以较高的价格成交
            
            if can_execute:
                self._execute_order(order, execution_price)
        except Exception as e:
            logger.error(f"检查订单成交失败: {e}", exc_info=True)
    
    def _execute_order(self, order, execution_price):
        """
        执行订单成交
        :param order: 订单信息
        :param execution_price: 成交价格
        """
        success = False 
        try:
            account = order['account']
            stock_code = order['stock_code']
            trade_type = order['trade_type']
            amount = order['amount']
            
            # 重新计算交易金额和手续费（基于实际成交价格）
            trade_value = amount * execution_price
            commission = trade_value * self.commission_rate
            
            # 更新账户持仓
            success = account.update_position(stock_code, trade_type, amount, execution_price, self.commission_rate)
            
            if success:
                # 更新订单状态
                order['status'] = 'completed'
                order['execution_price'] = execution_price
                order['execution_time'] = datetime.now()
                order['actual_trade_value'] = trade_value
                order['actual_commission'] = commission
                
                # 添加到交易历史
                self.trade_history.append(order)
                
                logger.info(f"订单成交: {order['order_id']}, 股票: {stock_code}, 类型: {trade_type}, "
                           f"数量: {amount}, 价格: {execution_price:.2f}, 交易额: {trade_value:.2f}")
            else:
                # 更新订单状态为失败
                order['status'] = 'failed'
                logger.warning(f"订单执行失败: {order['order_id']}, 可能是资金不足或持仓不足")
        except Exception as e:
            logger.error(f"执行订单成交失败: {e}", exc_info=True)
            order['status'] = 'failed'
        
        return success

    def get_pending_orders(self):
        """
        获取待处理订单列表
        :return: 待处理订单列表
        """
        return self.pending_orders
    
    def get_trade_history(self):
        """
        获取交易历史
        :return: 交易历史列表
        """
        return self.trade_history
    
    def get_trade_history_df(self):
        """
        获取交易历史数据框
        :return: 交易历史数据框
        """
        if not self.trade_history:
            return pd.DataFrame()
        
        # 转换为DataFrame
        df = pd.DataFrame(self.trade_history)
        
        # 删除account列
        if 'account' in df.columns:
            df = df.drop(columns=['account'])
        
        return df
    
    def cancel_order(self, order_id):
        """
        取消订单
        :param order_id: 订单ID
        :return: 是否成功取消
        """
        for order in self.pending_orders:
            if order['order_id'] == order_id:
                order['status'] = 'cancelled'
                self.pending_orders.remove(order)
                logger.info(f"取消订单: {order_id}")
                return True
        
        logger.warning(f"未找到订单: {order_id}")
        return False