from datetime import datetime, timedelta
from logger import logger  
from .base_strategy import BaseStrategy
from indicators import TechnicalIndicators
import numpy as np

class Strategy1003(BaseStrategy):
    """
    KDJ与价格分位数结合策略
    策略目标：利用KDJ指标的超买超卖信号，结合价格在长期分布中的位置进行交易
    策略逻辑：
        1. 当J值大于80且当前价格高于长期75分位数时卖出（超买+价格较高）
        2. 当J值小于40且当前价格低于长期中位数时买入（超卖+价格较低）
    """
    def __init__(self, codes):
        super().__init__(codes)
        self.str_remark = "str1003"
        # 历史数据
        self.code2daily = {}  # 股票代码到历史价格的映射
        
        # 策略参数
        self.kdj_period = 9        # KDJ计算周期
        self.long_period = 150     # 长期价格统计周期
        self.outlier_count = 3     # 长期统计时去除的异常值数量
        self.max_position = 10000   # 最大持仓数量
        self.min_position = 0      # 最小持仓数量
        self.single_trade_amount = 500  # 单次交易数量
        self.single_trade_value = 10000  # 单次交易金额
        self.interval = 300        # 交易间隔（秒）
        
        # 信号阈值
        self.j_high = 85           # J值超买阈值
        self.j_low = 40            # J值超卖阈值
        self.market_index = '899050.BJ'

    def trigger(self, ticks):
        """
        触发策略判断（实盘模式）
        :param ticks: 相关股票行情数据字典
        :return: list of (股票对象, 交易类型, 交易数量) 或 空列表
        """
        trade_signals = []
        
        # 遍历所有目标股票
        for stock in self.target_stocks:
            # 获取当前股票行情
            tick = ticks.get(stock.code)
            if not tick:
                continue
                
            current_price = tick['lastPrice']
            
            # 更新价格历史并执行策略
            if stock.code in self.code2daily:
                # 添加当前价格到历史数据
                prices = self.code2daily[stock.code]
                
                # 执行策略逻辑
                signal = self._execute_strategy(stock, prices, current_price)
                if signal:
                    trade_signals.append(signal)
        
        return trade_signals
    
    def back_test(self):
        """
        回测模式下的策略触发
        :return: list of (股票对象, 交易类型, 交易数量, idx) 或 空列表
        idx表示在回测数据中的位置，注意确保没有数据错位
        """
        backtest_signals = []
        
        # 遍历所有目标股票
        for stock in self.target_stocks:
            if stock.code not in self.code2daily:
                continue
            
            prices = self.code2daily[stock.code]
            if len(prices) < self.long_period:
                logger.warning(f"股票 {stock.code} 历史数据长度不足 {self.long_period} 天，跳过回测")
                continue
            
            round_count = len(prices) - self.long_period
            for i in range(round_count):
                current_price = prices[i + self.long_period]
                # 执行策略逻辑
                signal = self._execute_strategy(stock, prices[i:i+self.long_period], current_price)
                if signal:
                    #在交易信号中添加idx，方便后续反查交易日期
                    backtest_signals.append(signal + (i+self.long_period,))

        return backtest_signals
    
    def _execute_strategy(self, stock, prices, current_price):
        """
        执行策略逻辑
        :param stock: 股票对象
        :param prices: 历史价格序列,不包含当前价格
        :param current_price: 当前价格
        :return: (股票对象, 交易类型, 交易数量, 策略标记) 或 None
        """
        if len(prices) < self.long_period:
            logger.warning(f"股票 {stock.code} 历史数据长度不足 {self.long_period} 天，跳过")   
            return None
            
        # 计算KDJ指标
        k, d, j = TechnicalIndicators.kdj(
            prices, 
            n=self.kdj_period
        )
        
        # 计算长期价格分位数
        status, stats = TechnicalIndicators.longterm_median(
            prices, 
            period=self.long_period, 
            outlier_count=self.outlier_count
        )
        
        # 只有当两个指标都计算成功时才生成信号
        if k is not None and d is not None and j is not None and status:
            max_value, q3, median, q1, min_value = stats
            
            # 卖出信号：J值超买 + 价格高于75分位数
            if j > self.j_high and current_price > q3 and stock.current_position > 0:
                logger.info(f"触发卖出信号: 股票 {stock.code} J值={j:.2f} > {self.j_high}, 价格={current_price:.2f} > 75分位数={q3:.2f}")
                sell_amount = self.single_trade_value // current_price
                if sell_amount > 0:
                    return (stock, 'sell', sell_amount, self.str_remark)
            
            # 买入信号：J值超卖 + 价格低于中位数
            elif j < self.j_low and current_price < median:
                logger.info(f"触发买入信号: 股票 {stock.code} J值={j:.2f} < {self.j_low}, 价格={current_price:.2f} < 中位数={median:.2f}")
                buy_amount = self.single_trade_value // current_price
                return (stock, 'buy', buy_amount, self.str_remark)
        
        return None

    def fill_data(self, data_provider, start_date=None, end_date=None):
        """
        准备策略所需的历史数据
        :param data_provider: DataProvider对象
        :return: bool, 数据准备是否成功
        """
        try:
            # 获取所有目标股票代码
            code_list = [stock.code for stock in self.target_stocks]
            code_list.append(self.market_index)
            if not code_list:
                logger.warning("没有目标股票，无法获取历史数据")
                return False

            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
                end_date = datetime.now().strftime("%Y%m%d")
            
            trade_days = data_provider.get_trading_calendar(start_date, end_date)
            # 获取历史价格数据
            self.code2daily = data_provider.get_daily_data(code_list, start_date, end_date)
            
            # 数据完整性验证
            data_lengths = {}
            valid_codes = []
            for code in code_list:
                prices = self.code2daily.get(code, [])
                data_lengths[code] = len(prices)
                
                if len(prices) > self.long_period and len(prices) == len(trade_days):
                    valid_codes.append(code)
                else:
                    logger.info(f"股票{code} 获得的价格数量 {len(prices)} 不符合预期")
            
            # 只保留有效的数据
            self.code2daily = {code: self.code2daily[code] for code in valid_codes}
            
            logger.info(f"成功获取 {len(self.code2daily)} 只股票的有效历史价格数据")
            self.data_ready = True
            return True
            
        except Exception as e:
            logger.error(f"准备历史数据时发生错误: {e}", exc_info=True)
            return False