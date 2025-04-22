from datetime import datetime
from logger import logger

class RiskManager:
    """
    风险管理器，负责仓位控制和风险管理
    """
    def __init__(self):
        self.position_limits = {}      # 持仓限制 {股票代码: 最大持仓比例}
        self.max_position_ratio = 0.90 # 最大总持仓比例
        self.submit_trade_count = 0
        self.update_interval = 30      # 重新平衡的时间间隔，单位为秒
        self.buy_interval = 60        # 买入间隔，单位为秒
        self.last_update_time = 0
        logger.info("初始化风险管理器")
    

    def need_rebalance(self):
        current_time = int(datetime.now().timestamp())
        return self.submit_trade_count > 0 and (current_time - self.last_update_time) > self.update_interval

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