from datetime import datetime

class TickData:
    """
    Tick数据类，用于解析和保存股票实时行情数据
    """
    def __init__(self, stock_code):
        """
        初始化Tick数据对象
        :param stock_code: 股票代码
        """
        self.stock_code = stock_code
        
        # 基本价格信息
        self.time = 0                  # 时间戳(毫秒)
        self.lastPrice = 0.0           # 最新价
        self.open = 0.0                # 开盘价
        self.high = 0.0                # 最高价
        self.low = 0.0                 # 最低价
        self.lastClose = 0.0           # 昨收价
        
        # 成交量和成交额
        self.amount = 0.0              # 成交额
        self.volume = 0                # 成交量
        #self.pvolume = 0               # 当日累计成交量
        self.transactionNum = 0        # 成交笔数
        
        # 股票状态
        self.stockStatus = 0           # 股票状态
        
        # 期货相关
        #self.openInt = 0               # 持仓量
        #self.lastSettlementPrice = 0.0 # 昨结算价
        #self.settlementPrice = 0.0     # 结算价
        
        # 估值指标
        self.pe = 0.0                  # 市盈率
        
        # 盘口数据
        self.askPrice = [0.0] * 5      # 卖价档位
        self.bidPrice = [0.0] * 5      # 买价档位
        self.askVol = [0] * 5          # 卖量档位
        self.bidVol = [0] * 5          # 买量档位

        # 计算字段
        self.pct_chg = 0.0             # 涨跌幅

    def build_from_dict(self, data_dict):
        """
        从字典构建Tick数据对象
        :param data_dict: 包含tick数据的字典
        :return: self，便于链式调用
        """
        if not data_dict:
            return self
            
        # 基本价格信息
        self.time = data_dict.get('time', 0)//1000
        self.lastPrice = data_dict.get('lastPrice', 0.0)
        self.open = data_dict.get('open', 0.0)
        self.high = data_dict.get('high', 0.0)
        self.low = data_dict.get('low', 0.0)
        self.lastClose = data_dict.get('lastClose', 0.0)
        
        # 成交量和成交额
        self.amount = data_dict.get('amount', 0.0)
        self.volume = data_dict.get('volume', 0)
        self.pvolume = data_dict.get('pvolume', 0)
        #self.transactionNum = data_dict.get('transactionNum', 0)
        
        # 股票状态
        self.stockStatus = data_dict.get('stockStatus', 0)
        
        # 期货相关
        #self.openInt = data_dict.get('openInt', 0)
        #self.lastSettlementPrice = data_dict.get('lastSettlementPrice', 0.0)
        #self.settlementPrice = data_dict.get('settlementPrice', 0.0)
        
        # 估值指标
        self.pe = data_dict.get('pe', 0.0)
        
        # 盘口数据
        self.askPrice = data_dict.get('askPrice', [0.0] * 5)
        self.bidPrice = data_dict.get('bidPrice', [0.0] * 5)
        self.askVol = data_dict.get('askVol', [0] * 5)
        self.bidVol = data_dict.get('bidVol', [0] * 5)
        
        # 其他指标
        #self.volRatio = data_dict.get('volRatio', 0.0)
        #self.speed1Min = data_dict.get('speed1Min', 0.0)
        #self.speed5Min = data_dict.get('speed5Min', 0.0)
        
        # 计算涨跌幅
        if self.lastClose > 0:
            self.pct_chg = (self.lastPrice / self.lastClose - 1) * 100
        
        return self
    
    def get_datetime(self):
        """
        获取时间戳对应的datetime对象
        :return: datetime对象
        """
        if self.time > 0:
            return datetime.fromtimestamp(self.time / 1000)
        return None
    
    def __str__(self):
        """
        返回Tick数据的字符串表示
        """
        dt = self.get_datetime()
        time_str = dt.strftime('%Y-%m-%d %H:%M:%S') if dt else 'Unknown'
        
        return (f"TickData({self.stock_code}) - {time_str}\n"
                f"价格: {self.lastPrice:.2f} (开:{self.open:.2f} 高:{self.high:.2f} "
                f"低:{self.low:.2f} 昨收:{self.lastClose:.2f})\n"
                f"涨跌幅: {self.pct_chg:.2f}%\n"
                f"成交: 量 {self.volume} 额 {self.amount:.2f}")