from strategy.strategy1001 import Strategy1001
from strategy.strategy1002 import Strategy1002
from config import STRATEGY_CONFIG
from my_stock import MyStock

class StrategyFactory:
    """策略工厂类"""
    @staticmethod
    def create_strategy(strategy_id):
        """
        创建策略实例
        :param strategy_id: 策略ID
        :return: 策略实例
        """
        # 从配置中获取目标股票代码
        if strategy_id not in STRATEGY_CONFIG["strategy_params"]:
            raise ValueError(f"策略ID {strategy_id} 未配置参数")
            
        target_codes = STRATEGY_CONFIG["strategy_params"][strategy_id]["target_codes"]
        
        # 创建对应策略实例
        if strategy_id == 1001:
            return Strategy1001(target_codes)
        elif strategy_id == 1002:
            return Strategy1002(target_codes)
        else:
            raise ValueError(f"未知的策略ID: {strategy_id}")