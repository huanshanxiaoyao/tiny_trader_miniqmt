from datetime import datetime
from config import CODE2RELATED

class MyStock:
    """
    股票数据类，存储股票的基本信息和状态数据
    不包含交易逻辑和策略相关的参数
    """
    def __init__(self, code):
        self.code = code
        self.current_position = 0  # 当前持仓数量
        self.cost_price = 0        # 持仓成本
        self.last_buy_time = None  # 最后买入时间
        self.last_sell_time = None  # 最后卖出时间
        
        # 持仓信息
        self.current_position = 0             # 当前持仓数量
        self.cost_price = 0                   # 成本价
        self.market_value = 0                 # 持仓市值
        self.profit_loss = 0                  # 持仓盈亏

        # 行情数据
        self.current_price = 0                # 当前价格
        self.avg_price_10d = 0                # 10日均价

        # 从配置文件获取相关行业股票代码
        self.related_industry_codes = CODE2RELATED.get(code, [])

    def update_price(self, tick_data):
        """更新股票当前行情数据"""
        if not tick_data:
            return
        self.current_price = tick_data.get('lastPrice', 0)
        
        # 更新市值和盈亏
        if self.current_price > 0:
            self.market_value = self.current_position * self.current_price
            self.profit_loss = (self.current_price - self.cost_price) * self.current_position

    def update_position(self, volume_change, trade_price):
        """
        更新持仓信息
        :param volume_change: 交易数量（正数为买入，负数为卖出）
        :param trade_price: 交易价格
        """
        if volume_change == 0:
            return
            
        # 计算新的持仓成本
        if volume_change > 0:  # 买入
            total_cost = self.current_position * self.cost_price + volume_change * trade_price
            self.current_position += volume_change
            self.cost_price = total_cost / self.current_position if self.current_position > 0 else 0
        else:  # 卖出
            self.current_position += volume_change
            # 卖出不改变成本价，除非完全卖出
            if self.current_position <= 0:
                self.current_position = 0
                self.cost_price = 0

        # 更新市值和盈亏
        if self.current_price > 0:
            self.market_value = self.current_position * self.current_price
            self.profit_loss = (self.current_price - self.cost_price) * self.current_position

    def __str__(self):
        """返回股票信息的字符串表示"""
        return (f"股票代码: {self.code}\n"
                f"当前持仓: {self.current_position}\n"
                f"成本价: {self.cost_price:.2f}\n"
                f"当前价: {self.current_price:.2f}\n"
                f"持仓市值: {self.market_value:.2f}\n"
                f"持仓盈亏: {self.profit_loss:.2f}")