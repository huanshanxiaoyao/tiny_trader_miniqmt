from datetime import datetime
from logger import logger

class RiskManager:
    """
    风险管理类
    用于评估交易指令的风险，确保交易安全
    """
    def __init__(self):
        pass

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
        
        for stock, trade_type, amount in signals:
            # 这里可以添加风险评估逻辑
            # 如果通过风险评估，则添加到reviewed_signals并更新交易时间
            reviewed_signals.append((stock, trade_type, amount))
            
            # 更新股票的最后交易时间
            if trade_type == 'buy':
                stock.last_buy_time = current_time
                logger.info(f"更新股票 {stock.code} 最后买入时间: {datetime.fromtimestamp(current_time)}")
            elif trade_type == 'sell':
                stock.last_sell_time = current_time
                logger.info(f"更新股票 {stock.code} 最后卖出时间: {datetime.fromtimestamp(current_time)}")
        
        return reviewed_signals