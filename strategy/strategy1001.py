from datetime import datetime
from logger import logger  
from .base_strategy import BaseStrategy

class Strategy1001(BaseStrategy):
    """
    基于波动的持仓优化策略
    策略目标：利用周期内股价的波动，低点买入，高点时卖出，降低持仓成本，赚取收益
    策略假设：选中的股票中长线稳健向上
    """
    def __init__(self, stocks):
        super().__init__(stocks)
        self.code2avg = {}
        # 策略参数
        self.buy_threshold = 0.95             # 下跌买入阈值
        self.sell_threshold = 1.05            # 上涨卖出阈值
        self.buy_threshold_2 = 0.92           # 下跌买入阈值2
        self.sell_threshold_2 = 1.08          # 上涨卖出阈值2
        self.max_position = 1000              # 最大持仓数量
        self.min_position = 100               # 最小持仓数量
        self.soft_max_position = 800          # 软上限持仓数量
        self.soft_min_position = 400          # 软下限持仓数量
        self.single_buy_amount = 100          # 单次交易数量
        self.interval = 120                   # 交易间隔（秒）

        self.market_index = '899050.BJ'

    def trigger(self, ticks):
        """
        触发策略判断
        :param ticks: 相关股票行情数据字典
        :return: list of (股票代码, 交易类型, 交易数量) 或 空列表
        """
        market_tick = ticks.get(self.market_index)
        # 检查大盘状况
        market_status = self._check_market(market_tick)
        if not market_status:
            return []

        market_good, market_rise = market_status
        trade_signals = []
        now = int(datetime.now().timestamp())

        # 遍历所有目标股票
        for stock in self.target_stocks:
            # 检查行业状况
            industry_bad, industry_rise = self._check_industry(ticks, stock)
            
            # 获取当前股票行情
            tick = ticks.get(stock.code)
            if not tick:
                continue
                
            current_price = tick['lastPrice']
            
            # 判断买入条件
            if self._should_buy(stock, current_price, industry_bad, now):
                trade_signals.append((stock, 'buy', self.single_buy_amount))
                
            # 判断卖出条件
            elif self._should_sell(stock, current_price, industry_rise, now):
                sell_amount = min(self.single_buy_amount, 
                                stock.current_position - self.min_position)
                if sell_amount > 0:
                    trade_signals.append((stock, 'sell', sell_amount))
                    
        return trade_signals

    def _check_industry(self, ticks, stock):
        """检查行业状况"""
        industry_bad = False
        industry_rise = 0
        count = 0
        
        for code in stock.related_industry_codes:
            tick = ticks.get(code)
            if not tick or tick.get('open', 0) <= 0:
                continue
                
            rise = (tick['lastPrice'] / tick['open'] - 1) * 100
            industry_rise += rise
            count += 1
            
            if rise < -5:
                industry_bad = True
                break
                
        if count > 0:
            industry_rise /= count
            
        return industry_bad, industry_rise

    def _should_buy(self, stock, current_price, industry_bad, current_time):
        """判断是否应该买入"""
        if (hasattr(stock, 'last_buy_time') and stock.last_buy_time and 
            current_time - stock.last_buy_time < self.interval):
            return False
            
        if stock.current_position >= self.max_position:
            return False
            
        if industry_bad:
            return False
            
        # 没有持仓时的买入条件
        if (stock.cost_price == 0 and 
            current_price < self.code2avg.get(stock.code, 0) * 0.9):
            return True
            
        # 普通买入条件
        if (stock.current_position < self.soft_max_position and 
            current_price < stock.cost_price * self.buy_threshold):
            return True
            
        # 接近最大仓位的买入条件
        if (stock.current_position >= self.soft_max_position and 
            stock.current_position < self.max_position and 
            current_price < stock.cost_price * self.buy_threshold_2):
            return True
            
        return False

    def _should_sell(self, stock, current_price, industry_rise, current_time):
        """判断是否应该卖出"""
        if (hasattr(stock, 'last_sell_time') and stock.last_sell_time and 
            current_time - stock.last_sell_time < self.interval):
            return False
            
        if stock.current_position <= self.min_position:
            return False
            
        if industry_rise >= 5:
            return False
            
        # 普通卖出条件
        if (stock.current_position > self.soft_min_position and 
            current_price > stock.cost_price * self.sell_threshold):
            return True
            
        # 接近最小仓位的卖出条件
        if (stock.current_position <= self.soft_min_position and 
            stock.current_position > self.min_position and 
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
            self.code2avg = data_provider.get_daily_avg(code_list, start_date, end_date)
            
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

    def _check_market(self, market_tick):
        """检查大盘状况"""
        if not market_tick:
            return None
            
        # 计算大盘涨跌幅
        if market_tick.get('open', 0) <= 0:
            return None
            
        market_rise = (market_tick['lastPrice'] / market_tick['open'] - 1) * 100
        
        # 判断大盘状况
        market_good = market_rise > -2  # 大盘跌幅小于2%认为是好的
        
        return market_good, market_rise