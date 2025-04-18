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
        self.str_remark = "str1002"
        # 历史数据
        self.code2daily = {}  # 股票代码到历史价格的映射
        
        # 策略参数
        self.short_period = 5        # 短期均线周期
        self.long_period = 20        # 长期均线周期
        self.max_position = 500     # 最大持仓数量
        self.min_position = 100      # 最小持仓数量
        self.single_trade_amount = 200  # 单次交易数量
        self.single_trade_value = 10000  # 单次交易金额
        self.interval = 300          # 交易间隔（秒）
        
        # 信号状态记录
        self.code2hit = {}        # 该策略每支股票每天只触发一次
        self.market_index = '899050.BJ'  # 指数代码

    def trigger(self, ticks):
        """
        触发策略判断
        :param ticks: 相关股票行情数据字典
        :return: list of (股票对象, 交易类型, 交易数量, 策略标识) 或 空列表
        """
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
                # 获取历史价格数据（不修改）
                prices = self.code2daily[stock.code]
            
                
                # 调用策略核心逻辑（prices 不包含最新价格
                singal  = self._execute_strategy(stock, prices, current_price)
                if singal:
                    trade_signals.append(singal)
                
        return trade_signals

    def _execute_strategy(self, stock, prices, current_price):
        """
        计算策略信号
        :param code: 股票代码
        :param prices: 价格序列
        :return: 交易信号元组 (股票对象, 交易类型, 交易数量, 策略标识) 或 None
        """
        # 确保有足够的数据计算均线
        if len(prices) < self.long_period:
            logger.warning(f"股票 {stock.code} 历史数据长度不足 {self.long_period} 天，跳过计算")
            return None
        
        # 检查今天是否已经触发过该股票的信号
        if stock.code in self.code2hit:
            return None
        # 计算需要的最大长度
        max_length = max(self.short_period, self.long_period) + 5
        
        # 直接创建合适长度的临时价格序列
        if len(prices) >= max_length:
            temp_prices = prices[-max_length+1:].copy()
        else:
            temp_prices = prices.copy()

        # 添加最新价格
        temp_prices.append(current_price)
            
        # 计算均线
        short_ma = np.mean(temp_prices[-self.short_period:])
        long_ma = np.mean(temp_prices[-self.long_period:])
        
        # 计算前一天的均线
        prev_short_ma = np.mean(temp_prices[-(self.short_period+1):-1])
        prev_long_ma = np.mean(temp_prices[-(self.long_period+1):-1])
        #logger.info(f"股票 {stock.code} 前一天的短期均线: {prev_short_ma}, 前一天的长期均线: {prev_long_ma}")
        #logger.info(f"股票 {stock.code} 当天的短期均线: {short_ma}, 当天的长期均线: {long_ma}")
        
        # 判断金叉
        golden_cross = prev_short_ma <= prev_long_ma and short_ma > long_ma
        # 判断死叉
        death_cross = prev_short_ma >= prev_long_ma and short_ma < long_ma

                
        # 生成信号 注意纯策略计算逻辑不检查持仓，不检查时间间隔
        # 实盘运行的时候 在risk_manage 中检查
        # 回测时候，在评估函数中处理
        if golden_cross:
            # 检查持仓上限
            buy_amount = self.single_trade_value // current_price
            logger.info(f"触发买入信号: 股票 {stock.code} 金叉")
            self.code2hit[stock.code] = 'buy'
            return (stock, 'buy', buy_amount, self.str_remark)
        elif death_cross:
            sell_amount = self.single_trade_value // current_price
            logger.info(f"触发卖出信号: 股票 {stock.code} 死叉")
            self.code2hit[stock.code] = 'sell'
            return (stock, 'sell', sell_amount, self.str_remark)
        
        return None
        
    def back_test(self):
        """
        回测策略在历史数据上的表现
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
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
                end_date = datetime.now().strftime("%Y%m%d")
            
            # 获取历史价格数据
            self.code2daily = data_provider.get_daily_data(code_list, start_date, end_date)
            
            # 初始化信号状态
            for code in code_list:
                prices = self.code2daily.get(code, [])
                if len(prices) >= self.long_period:    
                    logger.info(f"股票 {code} 历史数据长度: {len(prices)}")  
            
            # 清空code2hit字典，准备新的交易日
            self.code2hit = {}
            
            logger.info(f"成功获取 {len(self.code2daily)} 只股票的历史价格数据")
            self.data_ready = True
            return True
            
        except Exception as e:
            logger.error(f"准备历史数据时发生错误: {e}", exc_info=True)
            return False
           
 