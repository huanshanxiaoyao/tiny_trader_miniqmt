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


    def evaluate_signals(self, signals, account):
        """
        评估交易信号的风险
        :param signals: list of  (stock,  交易类型, 交易数量)
        :return: list of (股票stock, 交易类型, 交易数量), 经过风险评估后的交易信号
        """
        reviewed_signals = []
        # 实现风险评估逻辑
        # 检查账户总仓位是否超过限制
        total_position_value = account.get_market_value()
        total_asset_value = account.get_total_asset()

        if total_asset_value == 0:
            logger.warning("账户总资产为0，不允许交易")
            return reviewed_signals
        
        # 计算仓位比例
        position_ratio = total_position_value / total_asset_value if total_asset_value > 0 else 0
        only_sell_mode = False
        
        # 判断是否超过最大仓位比例
        if position_ratio > self.max_position_ratio:
            logger.warning(f"当前总仓位比例 {position_ratio:.2%} 超过最大限制 {self.max_position_ratio:.2%}，只允许卖出操作")
            only_sell_mode = True
        
        # 通过风险评估后，更新股票的交易时间
        
        current_time = int(datetime.now().timestamp())
        
        for stock, trade_type, amount, remark in signals:
            # 如果通过风险评估，则添加到reviewed_signals并更新交易时间
            # 更新股票的最后交易时间
            if trade_type == 'buy' and not only_sell_mode:
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
        return reviewed_signals