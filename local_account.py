from datetime import datetime
from logger import logger, trader_logger
from base_account import BaseAccount

class LocalAccount(BaseAccount):
    """
    本地账户类，用于同步和管理服务器端的账户状态
    注意：无需从本地加载，只从服务端获取数据更新，阶段性保存到本地
    """
    def __init__(self, account_id, data_dir="online_account_data"):
        """
        初始化本地账户
        :param account_id: 账户ID
        """
        super().__init__(account_id, data_dir)
        self.is_simulated = False
        self.commission = 0
        self.created_at = 0
        self.positions = {}
        self.trades = []
        self.orders = []

        self.submit_trade_count = 0

        self.last_update_time = 0
        self.update_interval = 30      # 重新平衡的时间间隔，单位为秒

        logger.info(f"初始化本地账户: {account_id}")

    def init_log_files(self):
        # 确保数据目录存在
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        #这里无需从本地加载
   
    def need_update(self):
        current_time = int(datetime.now().timestamp())
        return  (current_time - self.last_update_time) > self.update_interval

    
    def update_positions(self, acc_info, positions_df, trades_df, orders_df, id2stock):
        """
        根据服务器端返回的账户信息和持仓信息更新账户状态
        :param acc_info: 账户信息字典，包含总资产、市值、可用资金、冻结资金等信息
        :param positions_df: 持仓信息DataFrame，包含股票代码、持仓数量等信息
        :param id2stock: 股票对象字典
        """
        try:
            self.total_asset = acc_info.get("TotalAsset", 0)

            self.market_value = acc_info.get("MarketValue", 0)
            
            self.free_cash = acc_info.get("FreeCash", 0)
            
            self.frozen_cash = acc_info.get("FrozenCash", 0)

            #下面是本地计算增加的字段 为了对其SimAccount
            self.cash = self.free_cash + self.frozen_cash
            self.update_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            
            # 计算当前仓位比例（市值占总资产的比例）
            if self.total_asset > 0:
                self.position_ratio = (1 - self.free_cash / self.total_asset)
            else:
                self.position_ratio = 0
                
            logger.info(f"更新账户信息: 总资产={self.total_asset:.2f}, 市值={self.market_value:.2f}, "
                        f"可用资金={self.free_cash:.2f}, 冻结资金={self.frozen_cash:.2f}，仓位比例={self.position_ratio:.2%}")
                
        except Exception as e:
            logger.error(f"更新账户信息失败: {e}", exc_info=True)

        # 更新股票的当前持仓
        try:
            if positions_df is not None and not positions_df.empty:
                # 清空当前持仓信息，重新从服务器数据填充
                self.positions = {}
                
                for _, row in positions_df.iterrows():
                    stock_code = row["StockCode"]
                    volume = row["Volume"]
                    free_volume = row["FreeVolume"]
                    open_price = row["OpenPrice"]
                    market_value = row["MarketValue"]
                    avg_price = row["AvgPrice"]
                    
                    # 更新self.positions字典
                    self.positions[stock_code] = {
                        'code': stock_code,
                        'volume': volume,
                        'can_use_volume': free_volume,
                        'cost': market_value if volume > 0 else 0,
                        'avg_price': avg_price,
                        'market_value': market_value,
                        'profit': 0,  # 这个可能需要后续计算
                        'profit_ratio': 0,  # 这个可能需要后续计算
                        'position_ratio': market_value / self.total_asset if self.total_asset > 0 else 0,
                        'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # 同时更新股票对象的信息
                    if stock_code in id2stock:
                        stock = id2stock[stock_code]
                        # 更新股票持仓信息
                        stock.current_position = volume
                        stock.free_position = free_volume
                        #stock.frozen_position = row["FrozenVolue"]
                        stock.open_price = open_price
                        stock.cost_price = avg_price
                        stock.market_value = market_value
                        #stock.on_road_position = row["OnRoadVolume"]
                        #stock.yesterday_position = row["YesterdayVolume"]
                        #stock.cost_price = market_value / volume if volume > 0 else 0
                        logger.info(f"更新股票 {stock_code} 持仓信息: 总持仓={stock.current_position}, 可用持仓={stock.free_position}, 成本价={stock.cost_price:.2f}, 开仓价={stock.open_price:.2f}")
                
                # 对于持仓表中没有的股票，将持仓设为0
                for stock_code, stock in id2stock.items():
                    if stock_code not in positions_df["StockCode"].values:
                        stock.current_position = 0
                        stock.free_position = 0
                        stock.frozen_position = 0
                        stock.market_value = 0
                        stock.on_road_position = 0
                        stock.yesterday_position = 0
                        #logger.info(f"股票 {stock_code} 不在持仓列表中，持仓设为0")
            else:
                logger.warning("持仓数据为空，无法更新股票持仓信息")
        except Exception as e:
            logger.error(f"更新股票持仓信息失败: {e}", exc_info=True)
            
        #更新交易信息
        try:
            if trades_df is not None and not trades_df.empty:
                # 清空当前交易记录，重新从服务器数据填充
                #注意，交易记录只返回当天的，所以对LocalAccount类保存的只有当天的交易记录
                self.trades = []
                
                for _, row in trades_df.iterrows():
                    stock_code = row["StockCode"]
                    trade_id = row["TradeId"]
                    trade_type = row["TradeType"]
                    if trade_type == 23:
                        trade_type = 'buy'
                    elif trade_type == 24:
                        trade_type = 'sell'
                    else:
                        logger.warning(f"未知的交易类型 {trade_type}，")
                        trade_type = str(trade_type)

                    volume = row["Volume"]
                    price = row["Price"]
                    trade_time = row["TradeTime"]
                    trade_value = volume * price
                    commission = 0
                    strategy = row.get("Strategy", "")
                    remark = row.get("Remark", "")
                    
                    # 创建交易记录字典
                    trade_record = {
                        'trade_id': trade_id,
                        'stock_code': stock_code,
                        'trade_type': trade_type,
                        'amount': volume,
                        'price': price,
                        'trade_value': trade_value,
                        'commission': commission,
                        'strategy': strategy,
                        'remark': remark,
                        'trade_time': trade_time
                    }
                    
                    # 添加到交易记录列表
                    self.trades.append(trade_record)
                    
                logger.info(f"更新交易记录成功，共 {len(self.trades)} 条记录")
            else:
                logger.warning("交易数据为空，无法更新交易信息")
        except Exception as e:
            logger.error(f"更新交易信息失败: {e}", exc_info=True)

        self.submit_trade_count = len(self.trades)

        #更新委托信息
        try:
            if orders_df is not None and not orders_df.empty:
                # 清空当前委托记录，重新从服务器数据填充
                self.orders = []
                
                for _, order in orders_df.iterrows():
                    # 创建委托记录字典
                    status = order["Status"]
                    if status == 56:
                        status = "done"
                    elif status == 50:
                        status = "waiting"
                    
                    order_type = order["OrderType"]
                    if order_type == 23:
                        order_type = 'buy'
                    elif order_type == 24:
                        order_type = 'sell'
                    else:
                        logger.warning(f"未知的委托类型 {order_type}，")
                        order_type = str(order_type)

                    order_record = {
                        'stock_code': order["StockCode"],
                        'volume': order["Volume"],
                        'price': order["Price"],
                        'order_id': order["OrderID"],
                        'strategy': order["Strategy"],
                        'status': status ,
                        'status_msg': order["StatusMsg"],
                        'remark': order["Remark"],
                        'order_type': order_type,
                        'traded_volume': order["TradedVolume"],
                        'traded_price': order["TradedPrice"],
                        'order_time': order["OrderTime"]
                    }
                    
                    # 添加到委托记录列表
                    self.orders.append(order_record)
                    
                logger.info(f"更新委托记录成功，共 {len(self.orders)} 条记录")
            else:
                logger.warning("委托数据为空，无法更新委托信息")
        except Exception as e:
            logger.error(f"更新委托信息失败: {e}", exc_info=True)
        
        self.last_update_time = int(datetime.now().timestamp())

        # 保存快照
        self._save_snapshot(acc_info, positions_df, trades_df, orders_df)

    def _save_snapshot(self, acc_info, positions_df, trades_df, orders_df):
        """
        保存账户、持仓和交易的快照到trader_logger
        :param acc_info: 账户信息字典
        :param positions_df: 持仓信息DataFrame
        :param trades_df: 交易信息DataFrame
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 记录账户信息快照
            trader_logger.info(f"[快照-账户信息] 时间={timestamp}, 总资产={acc_info.get('TotalAsset', 0):.2f}, "
                              f"市值={acc_info.get('MarketValue', 0):.2f}, 可用资金={acc_info.get('FreeCash', 0):.2f}, "
                              f"冻结资金={acc_info.get('FrozenCash', 0):.2f}, 仓位比例={self.position_ratio:.2%}")
            
            # 记录持仓信息快照
            if positions_df is not None and not positions_df.empty:
                trader_logger.info(f"[快照-持仓信息] 时间={timestamp}, 持仓数量={len(positions_df)}")
                for _, row in positions_df.iterrows():
                    stock_code = row["StockCode"]
                    volume = row["Volume"]
                    free_volume = row["FreeVolume"]
                    frozen_volume = row.get("FrozenVolue", 0)  # 注意原始数据中的拼写是FrozenVolue
                    open_price = row["OpenPrice"]
                    market_value = row["MarketValue"]
                    on_road_volume = row.get("OnRoadVolume", 0)
                    yesterday_volume = row.get("YesterdayVolume", 0)
                    avg_price = row["AvgPrice"]
                    
                    trader_logger.info(f"[快照-持仓明细] 股票={stock_code}, 总持仓={volume}, "
                                      f"可用持仓={free_volume}, 冻结持仓={frozen_volume}, "
                                      f"在途持仓={on_road_volume}, 昨日持仓={yesterday_volume}, "
                                      f"开仓价={open_price:.4f}, 市值={market_value:.2f}, 均价={avg_price:.4f}")
            else:
                trader_logger.info(f"[快照-持仓信息] 时间={timestamp}, 无持仓")
            
            # 记录交易信息快照
            if trades_df is not None and not trades_df.empty:
                trader_logger.info(f"[快照-交易信息] 时间={timestamp}, 交易数量={len(trades_df)}")
                for _, row in trades_df.iterrows():
                    stock_code = row["StockCode"]
                    volume = row["Volume"]
                    price = row["Price"]
                    trade_value = row.get("Value", volume * price)  # 优先使用Value字段，如果没有则计算
                    trade_type = row["TradeType"]
                    strategy = row.get("Strategy", "")
                    remark = row.get("Remark", "")
                    order_id = row.get("OrderId", "")
                    trade_id = row["TradeId"]
                    trade_time = row["TradeTime"]
                    
                    trader_logger.info(f"[快照-交易明细] 交易ID={trade_id}, 订单ID={order_id}, "
                                      f"股票={stock_code}, 策略={strategy}, "
                                      f"类型={trade_type}, 数量={volume}, 价格={price:.4f}, "
                                      f"交易额={trade_value:.2f}, 交易时间={trade_time}, "
                                      f"备注={remark}")
            else:
                trader_logger.info(f"[快照-交易信息] 时间={timestamp}, 无交易记录")

            # 记录委托信息快照
            if orders_df is not None and not orders_df.empty:
                trader_logger.info(f"[快照-委托信息] 时间={timestamp}, 委托数量={len(orders_df)}")
                for _, row in orders_df.iterrows():
                    stock_code = row["StockCode"]
                    volume = row["Volume"]
                    price = row["Price"]
                    order_id = row["OrderID"]
                    strategy = row.get("Strategy", "")
                    status = row["Status"]
                    status_msg = row.get("StatusMsg", "") # 根据实际情况确认字段名
                    order_type = row.get("OrderType", "") # 根据实际情况确认字段名
                    traded_volume = row.get("TradedVolume", 0)
                    traded_price = row.get("TradedPrice", 0.0)
                    order_time = row["OrderTime"]
                    remark = row.get("Remark", "")

                    trader_logger.info(f"[快照-委托明细] 订单ID={order_id}, 股票={stock_code}, 策略={strategy}, "
                                      f"状态={status}, 状态消息='{status_msg}', 类型={order_type}, "
                                      f"委托量={volume}, 委托价={price:.4f}, 成交量={traded_volume}, "
                                      f"成交均价={traded_price:.4f}, 委托时间={order_time}, 备注='{remark}'")
            else:
                trader_logger.info(f"[快照-委托信息] 时间={timestamp}, 无委托记录")
                
            trader_logger.info(f"[快照-完成] 时间={timestamp}")
            
        except Exception as e:
            logger.error(f"保存交易快照失败: {e}", exc_info=True)