from datetime import datetime
from logger import logger
from risk_config import PositionLevel

class RiskManager:
    """
    风险管理器，负责仓位控制和风险管理
    """
    def __init__(self):
        self.max_position_ratio = PositionLevel # 最大总持仓比例

        self.buy_interval = 60        # 买入间隔，单位为秒

        # 个股的仓位控制，后续可能放到配置文件中
        self.max_position_value = 32000              
        self.min_position_value = 0               
        self.soft_max_position_value = 24000          
        self.soft_min_position_value = 8000          
        self.single_buy_value = 8000         
    
        logger.info("初始化风险管理器")

    def check_account_limits(self, account):
        """
        检查账户总仓位是否超过限制，并计算可用资金
        :param account: 账户对象
        :return: float, 可用资金数量。如果超过仓位限制，返回0表示不允许买入
        """
        total_asset = account.get_total_asset()
        market_value = account.get_market_value()
        free_cash = account.get_free_cash()
        frozen_cash = total_asset - market_value - free_cash
        frozen_cash2 = account.get_frozen_cash()
        if frozen_cash != frozen_cash2:
            logger.warning(f"账户 {account.account_id} 总资产: {total_asset:.2f}, 市值: {market_value:.2f}, 可用资金: {free_cash:.2f}, 冻结资金: {frozen_cash:.2f}, 冻结资金2: {frozen_cash2:.2f}")
        
        # 计算当前仓位比例
        position_ratio = account.get_position_ratio()
        
        # 判断是否超过最大仓位比例
        if position_ratio > self.max_position_ratio:
            logger.warning(f"当前总仓位比例 {position_ratio:.2%} 超过最大限制 {self.max_position_ratio:.2%}，不允许买入")
            return 0
        
        # 计算在不超过最大仓位比例的情况下，可以额外投入的资金
        max_allowed_market_value = total_asset * self.max_position_ratio
        additional_allowed_value = max_allowed_market_value - market_value - frozen_cash
        
        # 取可用资金和允许额外投入资金的较小值
        available_cash = min(free_cash, additional_allowed_value)
        
        logger.info(f"当前总资产: {total_asset:.2f}, 市值: {market_value:.2f}, 仓位比例: {position_ratio:.2%},最大允许市值: {max_allowed_market_value:.2f}, 额外允许投入: {additional_allowed_value:.2f}")
        
        return available_cash

    def check_today_deal(self, account, stock, remark, trade_type):
        """
        检查股票在当天是否已经进行过交易
        :param account: 账户对象
        :param stock: 股票对象
        :param remark: 交易备注
        :param trade_type: 交易类型
        :return: bool, 如果当天已经有相同备注的交易则返回True，否则返回False
        """
        # 获取当前日期
        today = datetime.now().strftime('%Y%m%d')
        
        # 获取账户的交易记录
        orders = account.get_orders()
        
        # 检查是否有当天的相同股票、相同备注的交易记录
        for order in orders:
            # 实盘运行时候，这里获得到交易记录都是今天的
            #将日期的判断删除，如果是回测，需要注意
            if (order['stock_code'] == stock.code):
                logger.info(f" {stock.code} ,{remark}, {trade_type} check {order}")
                if order.get("strategy", "") == remark  and order.get("status","") in ["done","waiting"] and order.get("order_type","") == trade_type:
                    logger.warning(f"股票 {stock.code} {remark}今日已委托 ，不允许再次买入")
                    return True
                else:
                    logger.warning(f"股票 {stock.code} 今日已成交 ，但remark不匹配，请检查{remark}, trade_info:{order}")
                
        return False
    
    def evaluate_signals(self, signals, account):
        """
        评估交易信号的风险
        :param signals: list of  (stock,  交易类型, 交易数量)
        :return: list of (股票stock, 交易类型, 交易数量), 经过风险评估后的交易信号
        """
        reviewed_signals = []
        
        # 检查账户限制，获取可用资金
        available_cash = self.check_account_limits(account)
        only_sell_mode = (available_cash <= 0)
        
        current_time = int(datetime.now().timestamp())
        
        for stock, trade_type, amount, remark in signals:
            # 如果通过风险评估，则添加到reviewed_signals并更新交易时间
            # 更新股票的最后交易时间
            if trade_type == 'buy' and not only_sell_mode:
                # 计算此次交易需要的资金
                if stock.current_price <= 0:
                    logger.warning(f"股票 {stock.code} 价格为 {stock.current_price:.2f}，不允许买入")
                    continue
                required_cash = amount * stock.current_price
                
                # 检查资金是否足够
                if required_cash > available_cash:
                    logger.warning(f"股票 {stock.code} 买入需要资金 {required_cash:.2f}，超过可用资金 {available_cash:.2f}，不允许买入")
                    continue
                
                if current_time - stock.last_buy_time < self.buy_interval:
                    logger.warning(f"股票 {stock.code} 最近一次买入时间 {datetime.fromtimestamp(stock.last_buy_time)} 与当前时间 {datetime.fromtimestamp(current_time)} 间隔不足60秒，不允许再次买入")
                    continue
                if self.check_today_deal(account, stock, remark, trade_type):
                    logger.warning(f"股票 {stock.code} 今日已成交 ，不允许再次买入")
                    continue
                
                # 更新可用资金
                available_cash -= required_cash
                
                stock.last_buy_time = current_time
                reviewed_signals.append((stock, trade_type, amount, remark))
                #logger.info(f"更新股票 {stock.code} 最后买入时间: {datetime.fromtimestamp(current_time)}")
            elif trade_type == 'sell':
                if stock.free_position <= 0:
                    logger.warning(f"股票 {stock.code} 没有持仓，不允许卖出")
                    continue
                stock.last_sell_time = current_time
                reviewed_signals.append((stock, trade_type, amount, remark))
                #logger.info(f"更新股票 {stock.code} 最后卖出时间: {datetime.fromtimestamp(current_time)}")
        return reviewed_signals