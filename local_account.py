from datetime import datetime
from logger import logger
from base_account import BaseAccount

class LocalAccount(BaseAccount):
    """
    本地账户类，用于同步和管理服务器端的账户状态
    """
    def __init__(self, account_id, data_dir="real_account_data"):
        """
        初始化本地账户
        :param account_id: 账户ID
        """
        super().__init__(account_id, data_dir)
        self.is_simulated = False
        logger.info(f"初始化本地账户: {account_id}")
        self.submit_trade_count = 0

        self.last_update_time = 0
        self.update_interval = 30      # 重新平衡的时间间隔，单位为秒

    def need_update(self):
        current_time = int(datetime.now().timestamp())
        return  (current_time - self.last_update_time) > self.update_interval

    
    def update_positions(self, acc_info, positions_df, id2stock):
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