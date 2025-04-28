from strategy.strategy1001 import Strategy1001
from strategy.strategy1002 import Strategy1002
from strategy.strategy1003 import Strategy1003
from strategy.strategy1004 import Strategy1004
from .strategy_params import STRATEGY_PARAMS
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
        if strategy_id not in STRATEGY_PARAMS:
            raise ValueError(f"策略ID {strategy_id} 未配置参数")
            
        target_codes = STRATEGY_PARAMS[strategy_id]["target_codes"]
        
        # 创建对应策略实例
        if strategy_id == 1001:
            return Strategy1001(target_codes)
        elif strategy_id == 1002:
            return Strategy1002(target_codes)
        elif strategy_id == 1003:
            return Strategy1003(target_codes)
        elif strategy_id == 1004:
            return Strategy1004(target_codes, STRATEGY_PARAMS[strategy_id]["codeBJ2codeA"])           
        else:
            raise ValueError(f"未知的策略ID: {strategy_id}")