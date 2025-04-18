import numpy as np

class TechnicalIndicators:
    """
    股票技术指标计算工具类
    包含常用的技术指标计算方法
    """
    
    @staticmethod
    def ma(prices, period):
        """
        计算移动平均线
        :param prices: 价格序列
        :param period: 周期
        :return: 移动平均线值
        """
        if len(prices) < period:
            return None
        return np.mean(prices[-period:])
    
    @staticmethod
    def ema(prices, period, smoothing=2):
        """
        计算指数移动平均线
        :param prices: 价格序列
        :param period: 周期
        :param smoothing: 平滑系数
        :return: EMA值
        """
        if len(prices) < period:
            return None
            
        ema = [sum(prices[:period]) / period]
        k = smoothing / (1 + period)
        
        for price in prices[period:]:
            ema.append(price * k + ema[-1] * (1 - k))
            
        return ema[-1]
    
    @staticmethod
    def macd(prices, fast_period=12, slow_period=26, signal_period=9):
        """
        计算MACD指标
        :param prices: 价格序列
        :param fast_period: 快线周期
        :param slow_period: 慢线周期
        :param signal_period: 信号线周期
        :return: (DIF, DEA, MACD柱状值)
        """
        if len(prices) < slow_period:
            return None, None, None
            
        # 计算快线和慢线的EMA
        ema_fast = []
        ema_slow = []
        
        # 初始化EMA值
        ema_fast.append(sum(prices[:fast_period]) / fast_period)
        ema_slow.append(sum(prices[:slow_period]) / slow_period)
        
        # 计算系数
        k_fast = 2 / (fast_period + 1)
        k_slow = 2 / (slow_period + 1)
        
        # 计算EMA序列
        for price in prices[fast_period:]:
            ema_fast.append(price * k_fast + ema_fast[-1] * (1 - k_fast))
            
        for price in prices[slow_period:]:
            ema_slow.append(price * k_slow + ema_slow[-1] * (1 - k_slow))
        
        # 确保两个序列长度一致
        diff_len = len(ema_fast) - len(ema_slow)
        if diff_len > 0:
            ema_fast = ema_fast[diff_len:]
        
        # 计算DIF
        dif = [fast - slow for fast, slow in zip(ema_fast, ema_slow)]
        
        # 计算DEA (DIF的EMA)
        if len(dif) < signal_period:
            return dif[-1], None, None
            
        dea = [sum(dif[:signal_period]) / signal_period]
        k_signal = 2 / (signal_period + 1)
        
        for d in dif[signal_period:]:
            dea.append(d * k_signal + dea[-1] * (1 - k_signal))
        
        # 计算MACD柱状值
        macd = 2 * (dif[-1] - dea[-1])
        
        return dif[-1], dea[-1], macd
    
    @staticmethod
    def kdj(prices, highs=None, lows=None, n=9, m1=3, m2=3):
        """
        计算KDJ指标
        :param prices: 收盘价序列
        :param highs: 最高价序列，如果为None则使用prices
        :param lows: 最低价序列，如果为None则使用prices
        :param n: RSV计算周期
        :param m1: K值平滑系数
        :param m2: D值平滑系数
        :return: (K, D, J)
        """
        if len(prices) < n:
            return None, None, None
            
        if highs is None:
            highs = prices
        if lows is None:
            lows = prices
            
        # 确保所有序列长度一致
        min_len = min(len(prices), len(highs), len(lows))
        prices = prices[-min_len:]
        highs = highs[-min_len:]
        lows = lows[-min_len:]
        
        # 计算RSV
        rsv_list = []
        for i in range(n-1, len(prices)):
            period_high = max(highs[i-n+1:i+1])
            period_low = min(lows[i-n+1:i+1])
            
            if period_high == period_low:
                rsv = 50
            else:
                rsv = (prices[i] - period_low) / (period_high - period_low) * 100
            rsv_list.append(rsv)
        
        # 计算K值
        k_list = [50]  # 初始K值为50
        for rsv in rsv_list:
            k = (m1-1) / m1 * k_list[-1] + 1 / m1 * rsv
            k_list.append(k)
        
        # 计算D值
        d_list = [50]  # 初始D值为50
        for k in k_list[1:]:
            d = (m2-1) / m2 * d_list[-1] + 1 / m2 * k
            d_list.append(d)
        
        # 计算J值
        j = 3 * k_list[-1] - 2 * d_list[-1]
        
        return k_list[-1], d_list[-1], j
    
    @staticmethod
    def rsi(prices, period=14):
        """
        计算RSI指标
        :param prices: 价格序列
        :param period: 周期
        :return: RSI值
        """
        if len(prices) < period + 1:
            return None
            
        # 计算价格变化
        deltas = np.diff(prices)
        
        # 分离上涨和下跌
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # 计算平均上涨和下跌
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
            
        # 计算相对强度
        rs = avg_gain / avg_loss
        
        # 计算RSI
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def bollinger_bands(prices, period=20, std_dev=2):
        """
        计算布林带
        :param prices: 价格序列
        :param period: 周期
        :param std_dev: 标准差倍数
        :return: (中轨, 上轨, 下轨)
        """
        if len(prices) < period:
            return None, None, None
            
        # 计算中轨(SMA)
        middle = np.mean(prices[-period:])
        
        # 计算标准差
        sigma = np.std(prices[-period:])
        
        # 计算上下轨
        upper = middle + std_dev * sigma
        lower = middle - std_dev * sigma
        
        return middle, upper, lower
    
    @staticmethod
    def obv(prices, volumes):
        """
        计算OBV(能量潮)指标
        :param prices: 价格序列
        :param volumes: 成交量序列
        :return: OBV值
        """
        if len(prices) < 2 or len(volumes) < 2:
            return None
            
        # 确保序列长度一致
        min_len = min(len(prices), len(volumes))
        prices = prices[-min_len:]
        volumes = volumes[-min_len:]
        
        obv = 0
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]:
                obv += volumes[i]
            elif prices[i] < prices[i-1]:
                obv -= volumes[i]
                
        return obv
    
    @staticmethod
    def longterm_median(prices, period=180, outlier_count=3):
        """
        计算长期中位数及分位数指标，去除异常值
        :param prices: 价格序列
        :param period: 计算周期，默认180天
        :param outlier_count: 去除的异常点数量，默认为3
        :return: (status, [max_value, q3, median, q1, min_value]) 
                 status为True表示计算成功，False表示计算失败
        """
        if len(prices) < period:
            return False, [None, None, None, None, None]
        
        # 获取最近period个价格点
        recent_prices = prices[-period:]
        
        # 排序价格
        sorted_prices = sorted(recent_prices)
        
        # 检查outlier_count是否合理
        if outlier_count * 2 >= len(sorted_prices):
            outlier_count = max(0, (len(sorted_prices) // 2) - 1)
        
        # 去除异常值
        filtered_prices = sorted_prices[outlier_count:-outlier_count] if outlier_count > 0 else sorted_prices
        
        if not filtered_prices:
            return False, [None, None, None, None, None]
        
        # 计算统计指标
        min_value = filtered_prices[0]
        max_value = filtered_prices[-1]
        
        # 计算中位数
        n = len(filtered_prices)
        if n % 2 == 0:
            median = (filtered_prices[n//2 - 1] + filtered_prices[n//2]) / 2
        else:
            median = filtered_prices[n//2]
        
        # 计算25%和75%分位数
        q1_idx = int(n * 0.25)
        q3_idx = int(n * 0.75)
        
        q1 = filtered_prices[q1_idx]
        q3 = filtered_prices[q3_idx]
        
        return True, [max_value, q3, median, q1, min_value]