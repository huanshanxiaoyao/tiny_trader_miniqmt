from datetime import datetime, timedelta
from logger import logger  
from .base_strategy import BaseStrategy
import numpy as np

class Strategy1002(BaseStrategy):
    """
    移动平均线金叉死叉策略
    策略目标：利用短期均线和长期均线的交叉信号进行交易
    策略逻辑：短期均线上穿长期均线形成金叉时买入，短期均线下穿长期均线形成死叉时卖出
    """
    def __init__(self, codes):
        super().__init__(codes)
        # 历史数据
        self.code2daily = {}  # 股票代码到历史价格的映射
        
        # 策略参数
        self.short_period = 5        # 短期均线周期
        self.long_period = 20        # 长期均线周期
        self.max_position = 1000     # 最大持仓数量
        self.min_position = 100      # 最小持仓数量
        self.single_trade_amount = 200  # 单次交易数量
        self.interval = 300          # 交易间隔（秒）
        
        # 信号状态记录
        self.code2signal = {}        # 记录每个股票的上一个信号状态
        self.market_index = '899050.BJ'

    def trigger(self, ticks):
        """
        触发策略判断
        :param ticks: 相关股票行情数据字典
        :return: list of (股票对象, 交易类型, 交易数量) 或 空列表
        """
        # 检查大盘状况
        market_tick = ticks.get(self.market_index)
        market_good, market_rise = self._check_market(market_tick)
        if not market_rise:
            logger.error("当前大盘不满足交易条件，不进行交易")
            return []
            
        trade_signals = []
        now = int(datetime.now().timestamp())
        
        # 遍历所有目标股票
        for stock in self.target_stocks:
            # 获取当前股票行情
            tick = ticks.get(stock.code)
            if not tick:
                continue
                
            current_price = tick['lastPrice']
            
            # 更新价格历史
            if stock.code in self.code2daily:
                # 添加当前价格到历史数据
                prices = self.code2daily[stock.code]
                prices.append(current_price)
                # 保留最近的N个价格点
                max_length = max(self.short_period, self.long_period) + 5
                if len(prices) > max_length:
                    prices = prices[-max_length:]
                self.code2daily[stock.code] = prices
                
                # 计算均线
                if len(prices) >= self.long_period:
                    short_ma = np.mean(prices[-self.short_period:])
                    long_ma = np.mean(prices[-self.long_period:])
                    
                    # 计算前一天的均线
                    prev_short_ma = np.mean(prices[-(self.short_period+1):-1])
                    prev_long_ma = np.mean(prices[-(self.long_period+1):-1])
                    
                    # 判断金叉
                    golden_cross = prev_short_ma <= prev_long_ma and short_ma > long_ma
                    # 判断死叉
                    death_cross = prev_short_ma >= prev_long_ma and short_ma < long_ma
                    
                    # 获取上一个信号状态
                    last_signal = self.code2signal.get(stock.code, None)
                    
                    # 买入信号
                    if golden_cross and last_signal != 'buy':
                        if self._can_buy(stock, now):
                            logger.info(f"触发买入信号: 股票 {stock.code} 金叉")
                            trade_signals.append((stock, 'buy', self.single_trade_amount))
                            self.code2signal[stock.code] = 'buy'
                    
                    # 卖出信号
                    elif death_cross and last_signal != 'sell':
                        if self._can_sell(stock, now):
                            logger.info(f"触发卖出信号: 股票 {stock.code} 死叉")
                            sell_amount = min(self.single_trade_amount, 
                                            stock.current_position - self.min_position)
                            if sell_amount > 0:
                                trade_signals.append((stock, 'sell', sell_amount))
                                self.code2signal[stock.code] = 'sell'
        
        return trade_signals

    def _can_buy(self, stock, current_time):
        """判断是否可以买入"""
        # 检查交易间隔
        if (hasattr(stock, 'last_buy_time') and stock.last_buy_time and 
            current_time - stock.last_buy_time < self.interval):
            return False
            
        # 检查持仓上限
        if stock.current_position >= self.max_position:
            return False
            
        return True
        
    def _can_sell(self, stock, current_time):
        """判断是否可以卖出"""
        # 检查交易间隔
        if (hasattr(stock, 'last_sell_time') and stock.last_sell_time and 
            current_time - stock.last_sell_time < self.interval):
            return False
            
        # 检查持仓下限
        if stock.current_position <= self.min_position:
            return False
            
        return True

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
                
            # 计算日期范围（过去30天，确保有足够数据计算长期均线）
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            # 获取历史价格数据
            self.code2daily = data_provider.get_daily_data(code_list, start_date, end_date)
            
            # 初始化信号状态
            for code in code_list:
                prices = self.code2daily.get(code, [])
                if len(prices) >= self.long_period:    
                    logger.info(f"股票 {code} 历史数据长度: {len(prices)}")  
                    self.code2signal[code] = "Begin"
            logger.info(f"成功获取 {len(self.code2daily)} 只股票的历史价格数据")
            self.data_ready = True
            return True
            
        except Exception as e:
            logger.error(f"准备历史数据时发生错误: {e}", exc_info=True)
            return False
           
 