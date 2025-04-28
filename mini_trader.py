import sys
import time
import pandas as pd
from xtquant.xttrader import XtQuantTrader
from xtquant.xttype import StockAccount
from xtquant import xtconstant
from datetime import datetime
from xtquant.xttrader import XtQuantTraderCallback
from xtquant import xtdata
from logger import logger

class MiniTraderCallback(XtQuantTraderCallback):
    def on_disconnected(self):
        logger.warning(f'{datetime.now()} 连接断开')

    def on_stock_order(self, order):
        logger.info(f'{datetime.now()} 委托回调 {order.order_remark}')

    def on_stock_trade(self, trade):
        direction = "买入" if trade.offset_flag == 48 else "卖出"
        logger.info(f'{datetime.now()} 成交回调: {direction} {trade.order_remark} '
                   f'成交价格: {trade.traded_price} 成交数量: {trade.traded_volume}')

    def on_order_error(self, order_error):
        logger.error(f"委托错误: {order_error.order_remark} {order_error.error_msg}")

    def on_order_stock_async_response(self, response):
        logger.info(f"异步委托回调: {response.order_remark}")

class MiniTrader:
    def __init__(self, path, account_id):
        self.path = path
        self.account_id = account_id
        self.session_id = int(time.time())
        self.trader = XtQuantTrader(path, self.session_id)
        self.account = StockAccount(account_id)
        self.callback = MiniTraderCallback()
        self.trader.register_callback(self.callback)
        
    def connect(self):
        """连接交易终端并订阅账户"""
        self.trader.start()
        if self.trader.connect() != 0:
            logger.error('【软件终端连接失败！】\n 请运行并登录miniQMT.EXE终端。')
            return False
            
        if self.trader.subscribe(self.account) != 0:
            logger.error('【账户信息订阅失败！】\n 账户配置错误，检查账号是否正确。')
            return False
            
        logger.info('【软件终端连接成功！】')
        logger.info('【账户信息订阅成功！】')
        return True

    def get_account_info(self):
        """获取账户资产信息"""
        asset = self.trader.query_stock_asset(self.account)
        if asset:
            return {
                "TotalAsset": asset.total_asset,
                "MarketValue": asset.market_value,
                "FreeCash": asset.cash,
                "FrozenCash": asset.frozen_cash
            }
        return None

    def get_orders(self):
        """获取委托订单信息"""
        orders = self.trader.query_stock_orders(self.account)
        orders_df = pd.DataFrame([
            {
                "证券代码": order.stock_code,
                "委托数量": order.order_volume,
                "委托价格": order.price,
                "订单编号": order.order_id,
                "委托状态": order.status_msg,
                "报单时间": datetime.fromtimestamp(order.order_time).strftime('%H:%M:%S')
            }
            for order in orders
        ])
        return orders_df

    def get_trades(self):
        """获取成交信息"""
        trades = self.trader.query_stock_trades(self.account)
        trades_df = pd.DataFrame([
            {
                "StockCode": trade.stock_code,
                "Volume": trade.traded_volume,
                "Price": trade.traded_price,
                "Value": trade.traded_amount,
                "TradeType":trade.order_type,
                "OrderId": trade.order_id,
                "TradeId": trade.traded_id,
                "TradeTime": datetime.fromtimestamp(trade.traded_time).strftime('%H:%M:%S')
            }
            for trade in trades
        ])
        return trades_df

    def get_positions(self):
        """获取持仓信息"""
        positions = self.trader.query_stock_positions(self.account)
        positions_df = pd.DataFrame([
            {
                "StockCode": position.stock_code,
                "Volume": position.volume,
                "FreeVolume": position.can_use_volume,
                "FrozenVolue": position.frozen_volume,
                "OpenPrice": position.open_price,
                "MarketValue": position.market_value,
                "OnRoadVolume": position.on_road_volume,
                "YesterdayVolume": position.yesterday_volume
            }
            for position in positions
        ])
        return positions_df

    def print_summary(self):
        """打印账户汇总信息"""
        logger.info('-' * 18 + '【账户信息】' + '-' * 18)
        account_info = self.get_account_info()
        for key, value in account_info.items():
            logger.info(f"{key}: {value}")

        orders_df = self.get_orders()
        trades_df = self.get_trades()
        positions_df = self.get_positions()

        logger.info('-' * 18 + '【当日汇总】' + '-' * 18)
        logger.info(f"委托个数：{len(orders_df)} 成交个数：{len(trades_df)} 持仓数量：{len(positions_df)}")

        logger.info('-' * 18 + "【订单信息】" + '-' * 18)
        logger.info(str(orders_df) if not orders_df.empty else "无委托信息")

        logger.info('-' * 18 + "【成交信息】" + '-' * 18)
        logger.info(str(trades_df) if not trades_df.empty else "无成交信息")

        logger.info('-' * 18 + "【持仓信息】" + '-' * 18)
        logger.info(str(positions_df) if not positions_df.empty else "无持仓信息")

    def buy_stock(self, stock_code, amount, price_type=xtconstant.LATEST_PRICE, price=-1, remark=''):
        """
        买入股票
        :param stock_code: 股票代码
        :param amount: 目标买入金额
        :param price_type: 价格类型，默认市价
        :param price: 委托价格，市价委托时无效
        :param remark: 委托备注
        :return: 异步委托序号
        """
        # 获取账户可用资金
        asset = self.trader.query_stock_asset(self.account)
        available_cash = asset.cash
    
        # 获取当前价格 #TODO
        if price_type == xtconstant.LATEST_PRICE:
            full_tick = xtdata.get_full_tick([stock_code])
            current_price = full_tick[stock_code]['lastPrice']
        else:
            current_price = price
        
                # 确定买入金额
        buy_amount = min(amount, available_cash/current_price)
        buy_volume = buy_amount
        
        if buy_volume <= 0:
            logger.warning(f"可买数量为0，可用资金：{available_cash}，目标金额：{amount}")
            return None

        logger.info(f"买入 {stock_code}: 金额{amount}, 价格类型{price_type}, 价格{price},  备注{remark}, 可用资金{available_cash}")    
        return self.trader.order_stock_async(
            self.account,
            stock_code,
            xtconstant.STOCK_BUY,
            buy_volume,
            price_type,
            current_price,
            remark or 'buy',
            remark +"_"+ stock_code
        )

    def sell_stock(self, stock_code, volume, price_type=xtconstant.LATEST_PRICE, price=-1, remark=''):
        """
        卖出股票
        :param stock_code: 股票代码
        :param volume: 目标卖出数量
        :param price_type: 价格类型，默认市价
        :param price: 委托价格，市价委托时无效
        :param remark: 委托备注
        :return: 异步委托序号
        """
        # 获取持仓信息
        positions = self.trader.query_stock_positions(self.account)
        position_available = {p.stock_code: p.can_use_volume for p in positions}
        
        # 确定可卖数量
        available_volume = position_available.get(stock_code, 0)
        sell_volume = min(volume, available_volume)
        
        if sell_volume <= 0:
            logger.warning(f"可卖数量为0，持仓可用：{available_volume}，目标数量：{volume}")
            return None
            
        logger.info(f"卖出 {stock_code}: 数量{sell_volume}股")
        return self.trader.order_stock_async(
            self.account,
            stock_code,
            xtconstant.STOCK_SELL,
            sell_volume,
            price_type,
            price,
            remark or 'sell',
            remark +"_"+ stock_code
        )

# 使用示例
if __name__ == "__main__":
    path = r"D:\Apps\ZJ_QMT\userdata_mini"
    account_id = "6681802088"
    
    trader = MiniTrader(path, account_id)
    if trader.connect():
        # 打印账户信息
        trader.print_summary()
        
        # 买入示例：买入浦发银行2万元
        #trader.buy_stock('600000.SH', 20000, remark='buy_example')
        
        # 卖出示例：卖出500股
        #trader.sell_stock('513130.SH', 500, remark='sell_example')