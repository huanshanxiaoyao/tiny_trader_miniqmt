from datetime import datetime
from logger import logger

class RiskManager:
    """
    风险管理器，负责仓位控制和风险管理
    """
    def __init__(self):
        self.position_limits = {}      # 持仓限制 {股票代码: 最大持仓比例}
        self.max_position_ratio = 0.90 # 最大总持仓比例
        logger.info("初始化风险管理器")
    
    def set_position_limit(self, code, max_ratio):
        """
        设置单个股票的持仓限制
        :param code: 股票代码
        :param max_ratio: 最大持仓比例
        """
        self.position_limits[code] = max_ratio
        logger.info(f"设置股票 {code} 的最大持仓比例为 {max_ratio:.2%}")
    
    def set_max_position_ratio(self, ratio):
        """
        设置最大总持仓比例
        :param ratio: 最大总持仓比例
        """
        self.max_position_ratio = ratio
        logger.info(f"设置最大总持仓比例为 {ratio:.2%}")
    
    def check_rebalance_need(self, account):
        """
        检查是否需要重新平衡持仓
        :param account: 账户对象
        :return: 是否需要重新平衡，以及原因
        """
        positions = account.get_positions()
        total_asset = account.get_total_asset()
        
        if total_asset <= 0:
            return False, "总资产为0，无需重新平衡"
        
        # 检查总持仓比例
        total_position_ratio = sum(pos.get('position_ratio', 0) for pos in positions.values())
        if total_position_ratio > self.max_position_ratio:
            return True, f"总持仓比例 {total_position_ratio:.2%} 超过最大限制 {self.max_position_ratio:.2%}"
        
        # 检查单个持仓是否超过限制
        for code, position in positions.items():
            position_ratio = position.get('position_ratio', 0)
            max_ratio = self.position_limits.get(code, 0.1)  # 默认单个股票最大持仓比例为10%
            if position_ratio > max_ratio:
                return True, f"股票 {code} 持仓比例 {position_ratio:.2%} 超过限制 {max_ratio:.2%}"
        
        return False, "持仓比例正常"
    
    def get_position_ratio(self, account, code):
        """
        获取指定股票的持仓比例
        :param account: 账户对象
        :param code: 股票代码
        :return: 持仓比例，如果没有持仓则返回0
        """
        position = account.get_position(code)
        if position:
            return position.get('position_ratio', 0.0)
        return 0.0
    
    def get_total_position_ratio(self, account):
        """
        获取总持仓比例
        :param account: 账户对象
        :return: 总持仓比例
        """
        positions = account.get_positions()
        return sum(pos.get('position_ratio', 0.0) for pos in positions.values())
    
    def get_max_buy_amount(self, account, code, price):
        """
        计算最大可买入数量
        :param account: 账户对象
        :param code: 股票代码
        :param price: 买入价格
        :return: 最大可买入数量
        """
        if price <= 0:
            return 0
        
        # 获取账户信息
        cash = account.get_available_cash()
        total_asset = account.get_total_asset()
        
        # 计算当前持仓比例
        current_ratio = self.get_position_ratio(account, code)
        total_ratio = self.get_total_position_ratio(account)
        
        # 获取该股票的最大持仓比例限制
        max_ratio = self.position_limits.get(code, 0.1)
        
        # 计算可用于买入的资金
        # 1. 基于现金限制
        max_cash = cash * 0.95  # 预留5%的现金缓冲
        
        # 2. 基于单个股票持仓比例限制
        max_position_value = total_asset * max_ratio
        current_position_value = total_asset * current_ratio
        max_buy_value_by_position = max_position_value - current_position_value
        
        # 3. 基于总持仓比例限制
        max_total_value = total_asset * self.max_position_ratio
        current_total_value = total_asset * total_ratio
        max_buy_value_by_total = max_total_value - current_total_value
        
        # 取三者的最小值
        max_buy_value = min(max_cash, max_buy_value_by_position, max_buy_value_by_total)
        
        # 如果为负数，则无法买入
        if max_buy_value <= 0:
            return 0
        
        # 计算最大可买入数量（考虑手续费）
        commission_rate = 0.0005  # 假设手续费率为0.05%
        max_amount = int(max_buy_value / (price * (1 + commission_rate)))
        
        # 确保为100的整数倍（A股交易规则）
        max_amount = (max_amount // 100) * 100
        
        return max_amount
    
    def get_max_sell_amount(self, account, code):
        """
        计算最大可卖出数量
        :param account: 账户对象
        :param code: 股票代码
        :return: 最大可卖出数量
        """
        position = account.get_position(code)
        if not position:
            return 0
        
        # 返回可用持仓数量
        return position.get('can_use_volume', 0)

    def need_rebalance(self):
        current_time = int(datetime.now().timestamp())
        return self.submit_trade_count > 0 and (current_time - self.last_update_time) > self.update_interval

    def update_positions(self, acc_info, positions_df, id2stock):
        """
        根据账户信息更新持仓数据
        :param acc_info: 账户信息字典，包含总资产、市值、可用资金、冻结资金等信息
        """
        try:
            self.total_asset = acc_info.get("TotalAsset", 0)

            self.market_value = acc_info.get("MarketValue", 0)
            
            self.free_cash = acc_info.get("FreeCash", 0)
            
            self.frozen_cash = acc_info.get("FrozenCash", 0)
            
            # 计算当前仓位比例（市值占总资产的比例）
            if self.total_asset > 0:
                self.position_ratio = self.market_value / self.total_asset
            else:
                self.position_ratio = 0
                
            logger.info(f"更新账户信息: 总资产={self.total_asset:.2f}, 市值={self.market_value:.2f}, "
                        f"可用资金={self.free_cash:.2f}, 仓位比例={self.position_ratio:.2%}")
                
        except Exception as e:
            logger.error(f"更新账户信息失败: {e}", exc_info=True)

        # 更新股票的当前持仓
        try:
            if positions_df is not None and not positions_df.empty:
                for _, row in positions_df.iterrows():
                    stock_code = row["StockCode"]
                    if stock_code in id2stock:
                        stock = id2stock[stock_code]
                        # 更新股票持仓信息
                        stock.current_position = row["Volume"]
                        stock.free_position = row["FreeVolume"]
                        #stock.frozen_position = row["FrozenVolue"]
                        stock.open_price = row["OpenPrice"]
                        #stock.market_value = row["MarketValue"]
                        #stock.on_road_position = row["OnRoadVolume"]
                        #stock.yesterday_position = row["YesterdayVolume"]
                        stock.cost_price = row["MarketValue"]/stock.current_position if stock.current_position > 0 else 0
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
            
        self.submit_trade_count = 0
        self.last_update_time = int(datetime.now().timestamp())

    def evaluate_signals(self, signals):
        """
        评估交易信号的风险
        :param signals: list of  (stock,  交易类型, 交易数量)
        :return: list of (股票stock, 交易类型, 交易数量), 经过风险评估后的交易信号
        """
        # TODO: 实现风险评估逻辑
        
        # 通过风险评估后，更新股票的交易时间
        reviewed_signals = []
        current_time = int(datetime.now().timestamp())
        
        for stock, trade_type, amount, remark in signals:
            # 如果通过风险评估，则添加到reviewed_signals并更新交易时间
            # 更新股票的最后交易时间
            if trade_type == 'buy':
                if current_time - stock.last_buy_time < self.buy_interval:
                    logger.warning(f"股票 {stock.code} 最近一次买入时间 {datetime.fromtimestamp(stock.last_buy_time)} 与当前时间 {datetime.fromtimestamp(current_time)} 间隔不足60秒，不允许再次买入")
                    continue
                stock.last_buy_time = current_time
                reviewed_signals.append((stock, trade_type, amount, remark))
                logger.info(f"更新股票 {stock.code} 最后买入时间: {datetime.fromtimestamp(current_time)}")
            elif trade_type == 'sell':
                if stock.current_position <= 0:
                    logger.warning(f"股票 {stock.code} 没有持仓，不允许卖出")
                    continue
                stock.last_sell_time = current_time
                reviewed_signals.append((stock, trade_type, amount, remark))
                logger.info(f"更新股票 {stock.code} 最后卖出时间: {datetime.fromtimestamp(current_time)}")
        self.submit_trade_count += len(reviewed_signals)
        return reviewed_signals