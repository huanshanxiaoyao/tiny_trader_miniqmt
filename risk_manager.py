from datetime import datetime
from logger import logger

class RiskManager:
    """
    风险管理类
    用于评估交易指令的风险，确保交易安全
    目前把仓位管理等功能放在这里，后续可以考虑拆分成单独的类
    """
    def __init__(self):

        #买入频率控制
        self.buy_interval = 60

        self.last_update_time = None
        self.update_interval = 5 #TODO
        self.submit_trade_count = 0
        pass

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