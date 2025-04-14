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
    def fill_data(self, data_provider):
        """
        准备策略所需的历史数据或离线数据
        :param data_provider: DataProvider对象，提供数据获取接口
        :return: bool, 数据准备是否成功
        """
        pass
        
    @abstractmethod
    def trigger(self, ticks):
        """
        策略触发接口
        :param ticks: 相关股票行情数据字典
        :return: (交易类型, 交易数量) 或 None
        """
        pass