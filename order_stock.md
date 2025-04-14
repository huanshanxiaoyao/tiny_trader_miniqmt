同步下单
order_stock(account, stock_code, order_type, order_volume, price_type, price, strategy_name, order_remark)
释义
对股票进行下单操作
参数
account - StockAccount 资金账号
stock_code - str 证券代码，如'600000.SH'
order_type - int 委托类型
order_volume - int 委托数量，股票以'股'为单位，债券以'张'为单位
price_type - int 报价类型
price - float 委托价格
strategy_name - str 策略名称
order_remark - str 委托备注
返回
系统生成的订单编号，成功委托后的订单编号为大于0的正整数，如果为-1表示委托失败
备注
无

示例：
account = StockAccount('1000000365')
#xt_trader为XtQuant API实例对象
order_id = xt_trader.order_stock(account, '600000.SH', xtconstant.STOCK_BUY, 1000, xtconstant.FIX_PRICE, 10.5, 'strategy1', 'order_test')

异步下单
order_stock_async(account, stock_code, order_type, order_volume, price_type, price, str释义
对股票进行异步下单操作，异步下单接口如果正常返回了下单请求序号seq，会收到on_order_stock_async_response的委托反馈ategy_name, order_remark)

示例
account = StockAccount('1000000365')
#xt_trader为XtQuant API实例对象
seq = xt_trader.order_stock_async(account, '600000.SH', xtconstant.STOCK_BUY, 1000, xtconstant.FIX_PRICE, 10.5, 'strategy1', 'order_test')

同步撤单
cancel_order_stock(account, order_id)
释义
根据订单编号对委托进行撤单操作
参数
account - StockAccount 资金账号
order_id - int 同步下单接口返回的订单编号,对于期货来说，是order结构中的order_sysid字段
返回
返回是否成功发出撤单指令，0: 成功, -1: 表示撤单失败

示例
account = StockAccount('1000000365')
order_id = 100
#xt_trader为XtQuant API实例对象
cancel_result = xt_trader.cancel_order_stock(account, order_id)
