from datetime import datetime, timedelta
from .tick_data import TickData
import numpy as np
from logger import logger 

class TickSequence:
    """
    Tick序列类，用于维护一个按时间戳排序的tick列表，并提供分析功能
    """
    def __init__(self, stock_code, max_size=1000):
        """
        初始化Tick序列对象
        :param stock_code: 股票代码
        :param max_size: 序列最大容量，超过时将移除最旧的数据
        """
        self.stock_code = stock_code
        self.max_size = max_size
        self.ticks = []  # 按时间戳排序的tick列表
        self.last_update_time = 0  # 最后更新时间
    
    def add_tick(self, tick_data):
        """
        添加一个tick数据到序列
        :param tick_data: TickData对象或包含tick数据的字典
        :return: 添加是否成功
        """
        # 如果传入的是字典，转换为TickData对象
        if isinstance(tick_data, dict):
            tick = TickData(self.stock_code)
            tick.build_from_dict(tick_data)
        elif isinstance(tick_data, TickData):
            tick = tick_data
        else:
            return False
        
        # 检查时间戳是否有效
        if tick.time <= 0:
            return False
            
        # 检查是否是重复数据
        if self.ticks and tick.time <= self.last_update_time:
            # 如果时间戳相同，更新最后一个tick
            if tick.time == self.last_update_time:
                self.ticks[-1] = tick
                return True
            return False
        
        # 添加到序列并更新最后更新时间
        self.ticks.append(tick)
        self.last_update_time = tick.time
        
        # 如果超过最大容量，移除最旧的数据
        if len(self.ticks) > self.max_size:
            self.ticks = self.ticks[-self.max_size:]
            
        return True
    
    def get_latest_tick(self):
        """
        获取最新的tick数据
        :return: TickData对象或None
        """
        if not self.ticks:
            return None
        return self.ticks[-1]
    
    def get_ticks_in_timeframe(self, seconds=60):
        """
        获取指定时间范围内的tick数据
        :param seconds: 时间范围（秒）
        :return: 时间范围内的tick列表
        """
        if not self.ticks:
            return []
            
        now = self.ticks[-1].time
        start_time = now - seconds
        
        result = []
        for tick in reversed(self.ticks):
            if tick.time < start_time:
                break
            result.insert(0, tick)
            
        return result
    
    def calculate_price_trend(self, seconds=60):
        """
        计算指定时间范围内的价格趋势
        :param seconds: 时间范围（秒）
        :return: (趋势斜率, 价格变化百分比)
        """
        ticks = self.get_ticks_in_timeframe(seconds)
        if len(ticks) < 5:
            logger.warning(f"{self.stock_code} ticks数据不足，无法计算趋势，当前数据量：{len(ticks)}")
            return 0, 0
            
        # 提取时间和价格数据
        times = np.array([t.time for t in ticks])
        prices = np.array([t.lastPrice for t in ticks])
        
        # 计算线性回归
        times_norm = (times - times[0]) / (times[-1] - times[0]) if times[-1] != times[0] else np.zeros_like(times)
        A = np.vstack([times_norm, np.ones(len(times))]).T
        slope, _ = np.linalg.lstsq(A, prices, rcond=None)[0]
        
        # 计算价格变化百分比
        price_change_pct = (prices[-1] / prices[0] - 1) * 100 if prices[0] > 0 else 0
        
        return slope, price_change_pct
    
    def calculate_volume_trend(self, seconds=60):
        """
        计算指定时间范围内的成交量趋势
        :param seconds: 时间范围（秒）
        :return: 成交量趋势（正值表示增加，负值表示减少）
        """
        ticks = self.get_ticks_in_timeframe(seconds)
        if len(ticks) < 5:  # 至少需要5个数据点
            return 0
            
        # 计算每个时间点的成交量变化
        volumes = []
        for i in range(1, len(ticks)):
            vol_change = ticks[i].volume - ticks[i-1].volume
            if vol_change > 0:
                volumes.append(vol_change)
                
        if not volumes:
            return 0
            
        # 计算成交量变化趋势
        half = len(volumes) // 2
        if half == 0:
            return 0
            
        first_half = sum(volumes[:half])
        second_half = sum(volumes[half:])
        
        # 返回后半段与前半段的比值，大于1表示成交量增加
        return (second_half / first_half) if first_half > 0 else 1
    
    def calculate_bid_ask_pressure(self):
        """
        计算买卖盘压力比
        :return: 买卖盘压力比（>1表示买盘压力大，<1表示卖盘压力大）
        """
        latest = self.get_latest_tick()
        if not latest:
            return 1.0
            
        # 计算买盘总量和卖盘总量
        bid_vol_total = sum(latest.bidVol)
        ask_vol_total = sum(latest.askVol)
        
        # 返回买卖盘压力比
        return bid_vol_total / ask_vol_total if ask_vol_total > 0 else float('inf')
    
    def is_price_accelerating(self, seconds=300):
        """
        判断价格是否在加速上涨/下跌
        :param seconds: 时间范围（秒）
        :return: (是否加速, 方向) 方向: 1=上涨, -1=下跌, 0=震荡
        """
        ticks = self.get_ticks_in_timeframe(seconds)
        if len(ticks) < 10:  # 至少需要10个数据点
            return False, 0
            
        # 将时间范围分为前中后三段
        third = len(ticks) // 3
        if third == 0:
            return False, 0
            
        first_prices = [t.lastPrice for t in ticks[:third]]
        middle_prices = [t.lastPrice for t in ticks[third:2*third]]
        last_prices = [t.lastPrice for t in ticks[2*third:]]
        
        # 计算各段的价格变化率
        first_change = (middle_prices[0] / first_prices[0] - 1) if first_prices[0] > 0 else 0
        second_change = (last_prices[0] / middle_prices[0] - 1) if middle_prices[0] > 0 else 0
        
        # 判断是否加速
        is_accelerating = abs(second_change) > abs(first_change) * 1.2  # 后段变化率是前段的1.2倍以上
        
        # 判断方向
        direction = 0
        if second_change > 0 and first_change > 0:
            direction = 1  # 上涨
        elif second_change < 0 and first_change < 0:
            direction = -1  # 下跌
            
        return is_accelerating, direction
    
    def __len__(self):
        """
        返回序列中tick的数量
        """
        return len(self.ticks)
    
    def __str__(self):
        """
        返回Tick序列的字符串表示
        """
        latest = self.get_latest_tick()
        if not latest:
            return f"TickSequence({self.stock_code}) - 空序列"
            
        return (f"TickSequence({self.stock_code}) - {len(self.ticks)}条数据\n"
                f"最新: {latest}\n"
                f"买卖盘压力比: {self.calculate_bid_ask_pressure():.2f}")