# -*- coding: utf-8 -*-
"""
申请开通QMT请添加微信咨询gjquant，获取更多资料访问https://miniqmt.com/
此代码脚本仅用于软件测试，不能用于实盘交易，以此代码进行交易本人不承担任何损失。
未经许可，以下代码禁止用于商业用途，如需转载请注明出处来自本网站。
"""
import sys
import time
import pandas as pd
from xtquant.xttrader import XtQuantTrader #创建交易对象使用
from xtquant.xttype import StockAccount #订阅账户信息使用
from xtquant import xtconstant #执行交易的时候需要引入
from datetime import datetime #时间戳改为日期时间格式的时候使用

#——————————————————————————————————————————————————————————————————————————————————————————————————————
#设置你的path='' 文件夹userdata_mini前面改为自己的QMT安装路径信息，acc=''引号内填入自己的账号
path = r'D:\Apps\ZJ_QMT\userdata_mini'
acct = "6681802088"
#创建交易对象
session_id = int(time.time())
xt_trader = XtQuantTrader(path, session_id)
#xttrader连接miniQMT终端
xt_trader.start()
if xt_trader.connect() == 0:
    print('【软件终端连接成功！】')
else:
    print('【软件终端连接失败！】','\n 请运行并登录miniQMT.EXE终端。','\n path=改成你的QMT安装路径')   
#订阅账户信息
ID = StockAccount(acct)
subscribe_result = xt_trader.subscribe(ID)
if subscribe_result == 0:
    print('【账户信息订阅成功！】')
else: 
    print('【账户信息订阅失败！】','\n 账户配置错误，检查账号是否正确。','\n acct=""内填加你的账号')
    sys.exit() #如果运行环境，账户都没配置好，后面的代码就不执行
#——————————————————————————————————————————————————————————————————————————————————————————————————————
#打印账户信息
asset = xt_trader.query_stock_asset(ID)
print('-'*18,'【{0}】'.format(asset.account_id),'-'*18) 
if asset:
    print(f"资产总额: {asset.total_asset}\n"  
   f"持仓市值：{asset.market_value}\n"
   f"可用资金：{asset.cash}\n"
   f"在途资金：{asset.frozen_cash}")
#——————————————————————————————————————————————————————————————————————————————————————————————————————

# 委托信息
def orders_df():
    orders_df = pd.DataFrame([(order.stock_code, order.order_volume, order.price, order.order_id, order.status_msg,datetime.fromtimestamp(order.order_time).strftime('%H:%M:%S'))
  for order in xt_trader.query_stock_orders(ID)],
 columns=['证券代码', '委托数量', '委托价格', '订单编号','委托状态','报单时间'])
    return orders_df

# 成交信息
def trades_df():
    trades_df = pd.DataFrame([(trade.stock_code, trade.traded_volume, trade.traded_price,trade.traded_amount,trade.order_id, trade.traded_id, 
   datetime.fromtimestamp(trade.traded_time).strftime('%H:%M:%S'))
  for trade in xt_trader.query_stock_trades(ID)],
 columns=['证券代码', '成交数量', '成交均价','成交金额','订单编号', '成交编号', '成交时间'])
    return trades_df

# 持仓信息
def positions_df():
    positions_df = pd.DataFrame([(position.stock_code, position.volume, position.can_use_volume, position.frozen_volume, 
  position.open_price, position.market_value, position.on_road_volume, position.yesterday_volume)
 for position in xt_trader.query_stock_positions(ID)],
columns=['证券代码', '持仓数量', '可用数量', '冻结数量', '开仓价格', '持仓市值', '在途股份', '昨夜持股'])
    return positions_df

# 打印汇总信息
print('-'*18, '【当日汇总】', '-'*18)
orders_df = orders_df()
trades_df = trades_df()
positions_df = positions_df()
print(f"委托个数：{len(orders_df)}成交个数：{len(trades_df)}持仓数量：{len(positions_df)}")
# 输出DataFrame
print('-'*18, "【订单信息】",'-'*18)
print(orders_df if not orders_df.empty else "无委托信息")

print('-'*18, "【成交信息】",'-'*18)
print(trades_df if not trades_df.empty else "无成交信息")

print('-'*18, "【持仓信息】",'-'*18)
print(positions_df if not positions_df.empty else "无持仓信息")
