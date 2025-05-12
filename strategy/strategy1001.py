from datetime import datetime, timedelta
from xtquant import xtdata
from logger import logger  
from data_provider import DataProvider
from .base_strategy import BaseStrategy

class Strategy1001(BaseStrategy):
    """
    基于波动的持仓优化策略
    策略目标：利用周期内股价的波动，低点买入，高点时卖出，降低持仓成本，赚取收益
    策略假设：选中的股票中长线稳健向上
    """
    def __init__(self, codes, safe_range):
        super().__init__(codes)
        self.str_remark = "str1001"
        self.code2avg = {}
        self.code2daily = {}
        self.safe_range = safe_range
        # 策略参数
        self.buy_threshold = 0.95             # 下跌买入阈值
        self.sell_threshold = 1.05            # 上涨卖出阈值
        self.buy_threshold_2 = 0.92           # 下跌买入阈值2
        self.sell_threshold_2 = 1.08          # 上涨卖出阈值2

        self.max_position_value = 32000              # 最大持仓数量
        self.min_position_value = 0               # 最小持仓数量
        self.soft_max_position_value = 24000          # 软上限持仓数量
        self.soft_min_position_value = 8000          # 软下限持仓数量
        self.single_buy_value = 8000         # 单次交易数量

        self.market_index = '899050.BJ'

    def trigger(self, ticks):
        """
        触发策略判断
        :param ticks: 相关股票行情数据字典
        :return: list of (股票对象, 交易类型, 交易数量, 策略标识) 或 空列表
        """
        trade_signals = []

        market_tick = ticks.get(self.market_index)
        if not market_tick:
            market_tick_dict = xtdata.get_full_tick([self.market_index])
            market_tick = market_tick_dict.get(self.market_index)
            
        # 检查大盘状况
        market_rise = self._check_market(market_tick)
        if market_rise is None:
            logger.warning("获取大盘指标失败,set market_rise = 0")
            market_rise = 0

        # 遍历所有目标股票
        for stock in self.target_stocks:
            
            # 获取当前股票行情
            tick = ticks.get(stock.code)
            if not tick:
                continue
            safe_range = self.safe_range.get(stock.code, {})
            if not safe_range:
                logger.warning(f"股票 {stock.code} 未配置安全区间，跳过计算")
                continue
            current_price = tick['lastPrice']
            stock.current_price = current_price
            
            # 获取历史价格数据
            prices = self.code2daily.get(stock.code, [])
            
            # 调用策略核心逻辑
            signal = self._execute_strategy(stock, prices, current_price, market_rise, safe_range)
            if signal:
                trade_signals.append(signal)
                    
        return trade_signals

    def _execute_strategy(self, stock, prices, current_price, market_rise, safe_range):
        """
        计算策略信号
        :param stock: 股票对象
        :param prices: 价格序列
        :param current_price: 当前价格
        :param market_rise: 市场涨跌幅
        TODO 暂时删除了 :param industry_rise: 行业涨跌幅，以及对应逻辑，后续有完备的行业数据再考虑
        :return: 交易信号元组 (股票对象, 交易类型, 交易数量, 策略标识) 或 None
        """
        # 判断买入条件
        if self._should_buy(stock, current_price, market_rise, safe_range):
            amount = self.single_buy_value // current_price
            logger.info(f"触发买入条件，code:{stock.code},current_price:{current_price},cost_price:{stock.cost_price}")
            return (stock, 'buy', amount,  self.str_remark)
            
        # 判断卖出条件
        elif stock.current_position > 0 and self._should_sell(stock, current_price, market_rise, safe_range):
            logger.info(f"触发卖出条件，code:{stock.code},current_price:{current_price},cost_price:{stock.cost_price}")
            sell_amount = min(self.single_buy_value // current_price, 
                            stock.current_position - self.min_position_value // current_price)
            if sell_amount > 0:
                return (stock, 'sell', sell_amount,  self.str_remark)
        
        return None

    def _should_buy(self, stock, current_price, market_rise, safe_range):
        """判断是否应该买入"""

        short_sma5 = safe_range.get('short_sma5')
        short_ema8 = safe_range.get('short_ema8')
        short_atr10 = safe_range.get('short_atr10')
        long_ema55 = safe_range.get('long_ema55')
        long_atr20 = safe_range.get('long_atr20')

        if market_rise < -3:
            logger.info(f"大盘不好，跳过，code:{stock.code}, market_rise:{market_rise}")
            return False
        
        if current_price > long_ema55 + long_atr20 * 2:
            logger.info(f"当前价格高于长周期EMA55 + 2倍ATR20，跳过，code:{stock.code}, current_price:{current_price}, long_ema55:{long_ema55}, long_atr20:{long_atr20}")
            return False

        # 没有持仓时的买入条件
        if (stock.cost_price == 0 and ( current_price < self.code2avg.get(stock.code) * self.buy_threshold
            or current_price < short_sma5 - 0.3 * short_atr10 ) ):
            return True
        
        current_value = stock.current_position * current_price

        # 普通买入条件
        if (current_value < self.soft_max_position_value and 
            ( current_price < stock.cost_price * self.buy_threshold or current_price < short_sma5 - 0.5 * short_atr10 ) ):
            return True
            
        # 接近最大仓位的买入条件
        if (current_value >= self.soft_max_position_value and 
            current_value < self.max_position_value and 
            (current_price < stock.cost_price * self.buy_threshold_2 or current_price < short_sma5 - short_atr10 )):
            return True
            
        return False

    def _should_sell(self, stock, current_price, market_rise, safe_range):
        """判断是否应该卖出"""
        short_sma5 = safe_range.get('short_sma5')
        short_ema8 = safe_range.get('short_ema8')
        short_atr10 = safe_range.get('short_atr10')
        long_ema55 = safe_range.get('long_ema55')
        long_atr20 = safe_range.get('long_atr20')

        if  market_rise < 4 and current_price > long_ema55 + long_atr20 * 2:
            logger.info(f"当前价格高于长周期EMA55 + 2倍ATR20，卖出，code:{stock.code}, current_price:{current_price}, long_ema55:{long_ema55}, long_atr20:{long_atr20}")
            return True
        if  current_price > long_ema55 + long_atr20 * 3:
            logger.info(f"当前价格高于长周期EMA55 + 3倍ATR20，卖出，code:{stock.code}, current_price:{current_price}, long_ema55:{long_ema55}, long_atr20:{long_atr20}")
            return True 

        current_value = stock.current_position * current_price
        # 普通卖出条件
        if (current_value > self.soft_min_position_value and 
            (current_price > stock.cost_price * self.sell_threshold or current_price > short_ema8 + short_atr10) ):
            return True
            
        # 接近最小仓位的卖出条件
        if (current_value <= self.soft_min_position_value and 
            current_value > self.min_position_value and 
            current_price > stock.cost_price * self.sell_threshold_2):
            return True
            
        return False

    def fill_data(self):
        try:
            # 获取所有目标股票代码
            code_list = [stock.code for stock in self.target_stocks]
            if not code_list:
                logger.warning("没有目标股票，无法获取历史数据")
                return False
                
            # 计算日期范围（过去10天）
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')
            
            # 获取历史均价 - 修改这里，直接使用静态方法
            self.code2daily = DataProvider.get_daily_data(code_list, start_date, end_date)
            # 计算历史均价
            self.code2avg = {code: sum(prices) / len(prices) for code, prices in self.code2daily.items() if prices}
            
            # 检查数据是否获取成功
            if not self.code2avg:
                logger.error("获取历史均价数据失败")
                return False
                
            logger.info(f"成功获取 {len(self.code2avg)} 只股票的历史均价数据")
            self.data_ready = True
            return True
            
        except Exception as e:
            logger.error(f"准备历史数据时发生错误: {e}", exc_info=True)
            return False
