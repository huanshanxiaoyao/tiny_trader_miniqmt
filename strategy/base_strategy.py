from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """策略基类"""
    def __init__(self, target_codes):
        self.target_codes = target_codes
        #初始化的时候只有股票代码列表，还没有生成mystock对象
        #预期mystock对象 从全局获取，全局维持一份#TODO
        self.target_stocks = []                   
        self.data_ready = False                        # 数据准备状态标志
        
    @abstractmethod
    def fill_data(self, data_provider, start_time=None, end_time=None):
        """
        准备策略所需的历史数据或离线数据
        :param data_provider: DataProvider对象，提供数据获取接口
        :param start_time: 开始时间，可选参数
        :param end_time: 结束时间，可选参数
        :return: bool, 数据准备是否成功
        """
        pass
        
    @abstractmethod
    def trigger(self, ticks):
        """
        策略触发接口
        :param ticks: 相关股票行情数据字典
        :return: market_rise
        """
        pass

    def _check_market(self, market_tick):
        """检查大盘状况, 可复用也可以覆盖"""
        if not market_tick or market_tick.get('open', 0) <= 0:
            return None
            
        market_rise = (market_tick['lastPrice'] / market_tick['open'] - 1) * 100
        
        return market_rise
    def need_update(self):
        ###LocalAccount需要主动去查询是否更新，
        ###SimAccount 在模拟交易的时候直接调用了更新
        ###为了对其接口
        return False