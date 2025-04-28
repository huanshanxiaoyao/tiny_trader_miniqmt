from .base_strategy import BaseStrategy
from data.tick_sequence import TickSequence
import numpy as np
from logger import logger 

class Strategy1004(BaseStrategy):
    """
    北交所-A股联动策略
    当北交所股票对应的所有A股股票上涨，且至少2只涨幅>2%，
    同时北交所股票涨幅<1%时，生成买入信号
    TODO 1： 未考虑卖出逻辑，且不能T0 所以至少要第二天卖出，要想一下
    TODO 2: 关联股票的相关性，需要后续边验证，边完善
    TODO 3: 该策略是实时计算逻辑，不支持back_test 一些函数接口也略有不同
    """
    def __init__(self, codes, bj2a_map):
        super().__init__(codes)
        self.str_remark = "str1004"
        self.bj2a_map = bj2a_map
        self.a_codes = []  
        for a_codes in self.bj2a_map.values():
            self.a_codes.extend(a_codes)


        self.min_a_stocks = 2  # 最少需要2只A股满足条件
        self.a_min_increase = 0.02  # A股最小涨幅2%
        self.bj_max_increase = 0.01  # 北交所最大涨幅1%

        self.single_trade_value = 8000

        self.code2tick_seq =  {}  

        
    def trigger(self, ticks):
        """
        触发策略判断
        :param ticks: 相关股票行情数据字典
        :return: list of (股票对象, 交易类型, 交易数量, 策略标识) 或 空列表
        """
        trade_signals = []
        for code, tick in ticks.items():
            if code in self.bj2a_map or code in self.a_codes:
                if code not in self.code2tick_seq:
                    self.code2tick_seq[code] = TickSequence(code)          
                self.code2tick_seq[code].add_tick(tick)
        
        # 遍历所有目标股票
        for stock in self.target_stocks:
            bj_code = stock.code
            a_codes = self.bj2a_map.get(bj_code, [])
            if not a_codes or len(a_codes) < self.min_a_stocks:
                logger.warning(f"股票{bj_code}没有对应的A股股票或数量不足")
                return None
            
            if bj_code not in self.code2tick_seq:
                logger.warning(f"股票{bj_code}没有对应的tick序列")
                #TODO get_full_tick 获取最近的历史数据
                return None

            tick = ticks.get(stock.code)
            if not tick:
                continue
                
            current_price = tick['lastPrice']
            stock.current_price = current_price    

            slope, pct = self.code2tick_seq[bj_code].calculate_price_trend()
            #logger.info(f"股票{bj_code}涨幅 {pct:.2%} slope:{slope:.2f}")


            current_price = stock.current_price
            
            # 检查关联A股条件
            a_qualified = 0
            a_all_up = True
            qualified_stocks = []
            
            for a_code in a_codes:
                #TODO 需要增加成交量的判断，以及对比昨日收盘价格的编号
                #TODO 2
                if a_code not in self.code2tick_seq:
                    logger.warning(f"股票{a_code}没有对应的tick序列")
                    continue
                a_slope, a_pct = self.code2tick_seq[a_code].calculate_price_trend()
                    
                if a_pct > self.a_min_increase:
                    a_qualified += 1
                    qualified_stocks.append(f"{a_code}({a_pct:.2%})")
                if a_slope < 0:
                    a_all_up = False
            logger.info(f"A股上涨，{a_qualified}只超{self.a_min_increase:.0%}: {','.join(qualified_stocks)}")
            # 生成信号条件: 所有A股上涨且至少min_a_stocks只涨幅超过阈值
            if a_all_up and a_qualified >= self.min_a_stocks:
                volume = self.single_trade_value//current_price  # 使用预设的交易数量
                remark = f"A股全部上涨，{a_qualified}只超{self.a_min_increase:.0%}: {','.join(qualified_stocks)}"
                logger.info(f"触发买入信号: 股票 {bj_code} 涨幅 {pct:.2%} {remark}")
                trade_signals.append((stock, 'buy', volume, self.str_remark))

        return trade_signals

    def fill_data(self, data_provider):
        """
        目前先只依赖实时行情数据，不需要填充历史数据等
        """
        return
