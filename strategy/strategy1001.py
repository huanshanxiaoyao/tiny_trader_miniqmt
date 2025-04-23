from datetime import datetime, timedelta
from xtquant import xtdata
from logger import logger  
from .base_strategy import BaseStrategy

class Strategy1001(BaseStrategy):
    """
    基于波动的持仓优化策略
    策略目标：利用周期内股价的波动，低点买入，高点时卖出，降低持仓成本，赚取收益
    策略假设：选中的股票中长线稳健向上
    """
    def __init__(self, codes):
        super().__init__(codes)
        self.code2avg = {}
        self.code2daily = {}
        # 策略参数
        self.buy_threshold = 0.95             # 下跌买入阈值
        self.sell_threshold = 1.05            # 上涨卖出阈值
        self.buy_threshold_2 = 0.92           # 下跌买入阈值2
        self.sell_threshold_2 = 1.08          # 上涨卖出阈值2

        #这些可能要挪到RiskManager里面去，更好？
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
        market_good = True if market_rise > -2 else False

        # 遍历所有目标股票
        for stock in self.target_stocks:
            # 检查行业状况
            #industry_rise = self._check_industry(ticks, stock)
            industry_rise = 0 #TODO
            
            # 获取当前股票行情
            tick = ticks.get(stock.code)
            if not tick:
                continue
                
            current_price = tick['lastPrice']
            
            # 获取历史价格数据
            prices = self.code2daily.get(stock.code, [])
            
            # 调用策略核心逻辑
            signal = self._execute_strategy(stock, prices, current_price, market_rise, industry_rise)
            if signal:
                trade_signals.append(signal)
                    
        return trade_signals

    def _execute_strategy(self, stock, prices, current_price, market_rise, industry_rise):
        """
        计算策略信号
        :param stock: 股票对象
        :param prices: 价格序列
        :param current_price: 当前价格
        :param market_rise: 市场涨跌幅
        :param industry_rise: 行业涨跌幅
        :return: 交易信号元组 (股票对象, 交易类型, 交易数量, 策略标识) 或 None
        """
       
        # 判断买入条件
        if self._should_buy(stock, current_price, market_rise, industry_rise):
            amount = self.single_buy_value // current_price
            return (stock, 'buy', amount, 'str1001')
            
        # 判断卖出条件
        elif stock.current_position > 0 and self._should_sell(stock, current_price, market_rise, industry_rise):
            logger.info(f"触发卖出条件，code:{stock.code},current_price:{current_price},cost_price:{stock.cost_price}")
            sell_amount = min(self.single_buy_value // current_price, 
                            stock.current_position - self.min_position_value // current_price)
            if sell_amount > 0:
                return (stock, 'sell', sell_amount, 'str1001')
        
        return None

    def _check_industry(self, ticks, stock):
        """检查行业状况"""
        industry_rise = 0
        count = 0
        
        for code in stock.related_industry_codes:
            tick = ticks.get(code)
            if not tick or tick.get('open', 0) <= 0:
                continue
                
            rise = (tick['lastPrice'] / tick['open'] - 1) * 100
            industry_rise += rise
            count += 1
                
        if count > 0:
            industry_rise /= count
        else:
            logger.warning(f"获取行业数据失败，codes:{stock.related_industry_codes}")

            
        return industry_rise

    def _should_buy(self, stock, current_price, market_rise, industry_rise):
        """判断是否应该买入"""

        if market_rise < -1 or industry_rise < 0:
            return False

        # 没有持仓时的买入条件
        if (stock.cost_price == 0 and 
            current_price < self.code2avg.get(stock.code) * self.buy_threshold):
            return True
        
        current_value = stock.current_position * current_price

        # 普通买入条件
        if (current_value < self.soft_max_position_value and 
            current_price < stock.cost_price * self.buy_threshold):
            return True
            
        # 接近最大仓位的买入条件
        if (current_value >= self.soft_max_position_value and 
            current_value < self.max_position_value and 
            current_price < stock.cost_price * self.buy_threshold_2):
            return True
            
        return False

    def _should_sell(self, stock, current_price, market_rise, industry_rise):
        """判断是否应该卖出"""
        if stock.cost_price / current_price < 0.97:
            logger.info(f"检查卖出条件，code:{stock.code},current_price:{current_price},cost_price:{stock.cost_price}")
        if industry_rise >= 5 or market_rise > 4:
            return False

        current_value = stock.current_position * current_price
        # 普通卖出条件
        if (current_value > self.soft_min_position_value and 
            current_price > stock.cost_price * self.sell_threshold):
            return True
            
        # 接近最小仓位的卖出条件
        if (current_value <= self.soft_min_position_value and 
            current_value > self.min_position_value and 
            current_price > stock.cost_price * self.sell_threshold_2):
            return True
            
        return False

    def fill_data(self, data_provider):
        """
        准备策略所需的历史数据
        :param data_provider: DataProvider对象
        :return: bool, 数据准备是否成功
        """
        try:
            # 获取所有目标股票代码
            code_list = [stock.code for stock in self.target_stocks]
            if not code_list:
                logger.warning("没有目标股票，无法获取历史数据")
                return False
                
            # 计算日期范围（过去10天）
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=10)).strftime('%Y%m%d')
            
            # 获取历史均价
            self.code2daily = data_provider.get_daily_data(code_list, start_date, end_date)
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
