# -*- coding: gbk -*-
"""
基于波动的持仓优化策略
策略目标：利用周期内股价的波动，低点买入，高点时卖出，降低持仓成本，赚取收益
策略假设：选中的股票中长线稳健向上
策略编号:str1001
"""
from datetime import datetime, timedelta

class MyStock:
    """股票类，包含股票的基本信息和交易参数"""
    def __init__(self, code, related_industry_codes=None):
        self.code = code                      # 股票代码
        self.name = None
        self.today_buy_value = 0
        self.today_sell_value = 0 
        self.related_industry_codes = related_industry_codes or []  # 相关行业代码
        self.buy_threshold = 0.97             # 下跌买入阈值（默认0.95）
        self.sell_threshold = 1.03            # 上涨卖出阈值（默认1.05)
        self.buy_threshold_2 = 0.92           # 下跌买入阈值2（默认0.92）
        self.sell_threshold_2 = 1.08          # 上涨卖出阈值2（默认1.08)
        self.current_position = 0             # 当前持仓数量
        self.cost_price = 0                   # 成本价
        self.max_position = 300000              # 最大持仓数量（默认1000）
        self.min_position = 0               # 最小持仓数量（默认100）
        self.soft_max_position = 200000          # 软上限持仓数量（默认800）
        self.soft_min_position = 1000          # 软下限持仓数量（默认400）
        self.single_buy_amount = 1000          # 单次买入额度，默认1000
        self.last_buy_time = None            # 上次交易时间,记录秒为单位的值
        self.last_sell_time = None           # 上次交易时间,记录秒为单位的值
        self.interval =  120                  # 交易间隔（默认120s）


def init_mystock(C, code_list):
    """
    初始化股票对象
    
    Args:
        C: 全局上下文
        code_list: 目标股票代码列表
    
    Returns:
        dict: 股票代码到MyStock对象的映射
    """
    code2mystock = {}
    code2related_industry = {"832522.BJ":["300450.SZ","300457.SZ","300340.SZ"],
        "832491.BJ":["600406.SH","000400.SZ","002028.SZ","870299.BJ"],
        "835174.BJ":["600031.SH","000425.SZ","836942.BJ"],
        "836942.BJ":["832885.BJ","835640.BJ","835174.BJ"],
        "920116.BJ":["688066.SH","835640.BJ","832885.BJ"],
        "839493.BJ":["603019.SH","872808.BJ","688316.SH"]}
    
    # 获取当前持仓的股票代码数量和成本价
    positions = get_trade_detail_data(C.accID, 'stock', 'position')
    
    for code in code_list:
        stock = MyStock(code)
        ret = C.get_instrumentdetail(code)
        name = ret["InstrumentName"]
        stock.related_industry_codes = code2related_industry.get(code, [])
        stock.name = name
        
        # 设置当前持仓数量和成本价（如果有持仓）
        for position in positions:
            ret_code = '%s.%s'%(position.m_strInstrumentID, position.m_strExchangeID)
            if ret_code == code:
                stock.current_position = position.m_nVolume
                stock.cost_price = position.m_dOpenPrice
                print(f"股票{name}初始化信息: 当前持仓={stock.current_position}, 成本价={stock.cost_price:.2f}, 最大持仓={stock.max_position}, 最小持仓={stock.min_position}")
                break
        
        code2mystock[code] = stock
    
    return code2mystock

def refresh_position(C, code2mystock):
     # 获取当前持仓的股票代码数量和成本价
    now = int(datetime.now().timestamp())
    positions = get_trade_detail_data(C.accID, 'stock', 'position')

    # 获取当日成交数据 从这里面汇总计算每支股票当日的买入和卖出金额，以及每日总的程序化交易金额
    #注意 两个强假设1，接口返回当日全部的交易记录；2，依赖交易标记，来区分是否是程序化交易
    deals = get_trade_detail_data(C.accID, 'stock', 'deal')
    print(f"刷新持仓信息 at {now}, positions length={len(positions)}, deals length={len(deals)}")
    if deals:
        C.total_buy = 0
        C.total_sell = 0

    for code in code2mystock.keys():
        stock = code2mystock[code]
        stock.today_buy_value = 0
        stock.today_sell_value = 0

        for deal in deals:
            ret_code = '%s.%s'%(deal.m_strInstrumentID, deal.m_strExchangeID)
            if ret_code == code and deal.m_strRemark == 'str1001':#注意，如果后面修改了交易标记，这里也要修改
                print(f"deal:{deal.m_strRemark}, {deal.m_dTradeAmount}, {deal.m_nOffsetFlag}")
                if deal.m_nOffsetFlag == 48:
                    stock.today_buy_value += deal.m_dTradeAmount
                    C.total_buy += deal.m_dTradeAmount
                elif deal.m_nOffsetFlag == 49:
                    stock.today_sell_value += deal.m_dTradeAmount
                    C.total_sell += deal.m_dTradeAmount
                print(f"{stock.name} 今日买入金额={stock.today_buy_value:.2f}, 今日卖出金额={stock.today_sell_value:.2f}, ")
        #print(f"今日总买入金额={C.total_buy:.2f}, 今日总卖出金额={C.total_sell:.2f}")

        for position in positions:
            ret_code = '%s.%s'%(position.m_strInstrumentID, position.m_strExchangeID)
            if ret_code == code:
                stock.current_position = position.m_nVolume
                stock.cost_price = position.m_dOpenPrice
                print(f"{stock.name}: 当前持仓={stock.current_position}, 成本价={stock.cost_price:.2f}, 最大持仓={stock.max_position}, 最小持仓={stock.min_position}")
    
    


def init(C):
    """
    策略初始化函数
    """
    # 设置目标股票代码
    C.target_codes = ['832491.BJ', '832522.BJ', 
                      "835174.BJ", "836263.BJ", "831305.BJ", "430476.BJ", "832175.BJ", 
                      "920108.BJ", "920029.BJ", "831370.BJ", "833781.BJ", "920068.BJ", 
                      "871478.BJ", "831768.BJ", "430564.BJ", "833523.BJ", "873223.BJ", 
                      "430139.BJ", "833030.BJ", "870299.BJ", "920799.BJ", "872374.BJ", 
                      "831152.BJ",  "872895.BJ", "834261.BJ"]
    C.set_universe(C.target_codes)
    C.accID = '1911107358'
    C.need_refresh_position = 0
    C.total_buy = 0
    C.total_sell = 0
    C.only_sell_mode = False
    C.only_buy_mode = False
    
    # 初始化股票对象
    C.code2mystock = init_mystock(C, C.target_codes)  # 修正：使用 C.target_codes
    
    # 定义相关股票列表：目标代码 + BJ50指数 + 相关行业代码
    C.related_stocks = C.target_codes.copy() + ['899050.BJ']  # 修正：使用 C.target_codes
    # 添加所有股票的相关行业代码
    for stock in C.code2mystock.values():
        C.related_stocks.extend(stock.related_industry_codes)
    C.related_stocks = list(set(C.related_stocks))
    
    # 设置时间范围：end_time为昨天，start_time为10个交易日前
    today = datetime.now()
    end_time = (today - timedelta(days=1)).strftime("%Y%m%d")
    start_time = (today - timedelta(days=10)).strftime("%Y%m%d")
    
    C.start_time = start_time
    C.end_time = end_time
    C.code2avg = {}
    for code in C.related_stocks:
        download_history_data(code, "1d", C.start_time,"")

    # 获取历史数据
    data1 = C.get_market_data_ex(['close'], C.related_stocks, period='1d', 
                                start_time=C.start_time, end_time=C.end_time)
    print("BEGIN Get Data")
    
    # 检查是否成功获取数据
    if not data1:
        print("警告：未获取到任何历史数据")
        return
        
    # 处理每只股票的数据
    for k, v in data1.items():
        if k not in C.related_stocks:
            continue
            
        prices = []
        for idx, row in v.iterrows():
            price = row.get('close')
            if price and price > 0:  # 确保价格有效
                prices.append(price)
                
        # 只有在有效价格数据时才计算均值
        if prices:
            C.code2avg[k] = sum(prices) / len(prices)
        else:
            print(f"警告：{k} 没有有效的价格数据")
            C.code2avg[k] = 0
    
    print("历史均价数据：", C.code2avg)


def calculate_industry_status(ticks, related_industry_codes):
    """
    计算行业相关股票的涨跌状态
    """
    industry_bad = False
    industry_rise_percent = 0
    industry_count = 0
    
    for code in related_industry_codes:
        tick = ticks.get(code)
        if not tick:
            continue
        # 修正：使用统一的键名
        last_price = tick.get('lastPrice') or tick.get('last_price', 0)
        open_price = tick.get('open') or tick.get('open_price', 0)
        
        if not open_price:  # 防止除以零
            continue
            
        rise_percent = (last_price / open_price - 1) * 100
        industry_rise_percent += rise_percent
        industry_count += 1
        
        if rise_percent < -5:
            industry_bad = True
            break
            
    if industry_count > 0:
        industry_rise_percent /= industry_count
        
    return industry_bad, industry_rise_percent

def handlebar(C):
    """
    策略主函数，每个周期调用一次
    Args:
        C: 全局上下文
    """
    # 获取所有related_stocks代码实时行情
    ticks = C.get_full_tick(C.related_stocks)
    #print(f"Start handlebar, length of ticks    {len(ticks)}")


    now = int(datetime.now().timestamp())
    if C.need_refresh_position > 0 or now % 60 == 0:
        print(f"today total_buy={C.total_buy:.2f}, total_sell={C.total_sell:.2f}")
        refresh_position(C, C.code2mystock)
        if C.need_refresh_position > 0:
            C.need_refresh_position -= 1
    
    # 获取BJ50指数行情，代表大盘行情
    bj50_tick = ticks.get('899050.BJ')
    if not bj50_tick:
        print("Failed to get BJ50 tick")
        return
    
    # 判断大盘是否学好（当前价格大于开盘价）
    if bj50_tick['lastClose'] > 0:
        market_rise_percent = (bj50_tick['lastPrice'] / bj50_tick['lastClose'] - 1) * 100
    else:
        print("警告：BJ50开盘价为0")
        return
    market_good = market_rise_percent > -5 #TODO
    
    # 对每一个目标代码进行交易决策
    for code, stock in C.code2mystock.items():
        tick = ticks.get(code)
        if not tick:
            continue
        
        # 为当前股票计算行业状态，使用其相关行业代码
        #industry_bad, industry_rise_percent = calculate_industry_status(ticks, stock.related_industry_codes)
        
        current_price = tick['lastPrice']
        lastClose = tick['lastClose']
        
        # 计算相对于10日均值的比例
        avg_price = C.code2avg.get(code, 0)

        pct = current_price / lastClose if lastClose else 1
        
        print(f"today total_buy={C.total_buy:.2f}, total_sell={C.total_sell:.2f}, stock_buy,{stock.today_buy_value},stock_sell,{stock.today_sell_value}")
        print(f"{code} 价格={current_price:.2f}, 均价={avg_price:.2f}, lastClose={lastClose:.2f}, pct={pct} bj50涨幅={market_rise_percent:.2f}%")
        
        # 买入条件：大盘学好，行业没有严重下跌，股票价格低于成本或均值，持仓未满
        # 买入条件：根据持仓量使用不同的买入阈值
        if (market_good and not C.only_sell_mode and
            ((stock.current_position == 0 and current_price < lastClose * 0.95) or  # 没有持仓时，价格低于历史均价的90%
             (stock.current_position < stock.soft_max_position and 
              current_price < lastClose * stock.buy_threshold) or
             (stock.current_position >= stock.soft_max_position and 
              stock.current_position < stock.max_position and 
              current_price < lastClose * stock.buy_threshold_2)) ):
            
            if stock.today_buy_value > 150000:
                print(f"股票{stock.name}今日买入金额={stock.today_buy_value:.2f} 超过额度，跳过买入")
                continue
            if C.total_buy > 800000:
                print(f"总买入金额={C.total_buy:.2f} 即将超过100万限额")
            if C.total_buy - C.total_sell > 50000:#每日手动更新，因为目前和人工下单混在一起
                print(f"总买入金额={C.total_buy:.2f} 超过额度，跳过买入")
                continue

            # 计算买入数量
            buy_amount = stock.single_buy_amount
            
            # 检查交易时间间隔
            current_time = int(datetime.now().timestamp())
            if stock.last_buy_time and current_time - stock.last_buy_time < stock.interval:
                print(f"{stock.name}距离上次买入时间不足{stock.interval}秒，不进行买入")
                continue
                
            # 提交买入指令,注意这里只是提交购买请求，并不一定成交，所以设定需要刷新的标记，下一轮会刷新持仓信息
            submit_buy_order(C, stock, buy_amount, current_price, "str1001")
            stock.last_buy_time = current_time
            C.need_refresh_position = 3
            
        # 卖出条件：大盘涨幅小，行业涨幅小，股票价格高于成本或均值，持仓充足
        # 卖出条件：根据持仓量使用不同的卖出阈值
        elif (market_rise_percent < 5  and not C.only_buy_mode and
              ((stock.current_position > stock.soft_min_position and 
                current_price > lastClose * stock.sell_threshold) or
               (stock.current_position <= stock.soft_min_position and 
                stock.current_position > stock.min_position and 
                current_price > lastClose * stock.sell_threshold_2)) ):

            if stock.today_sell_value > 100000:
                print(f"股票{stock.name}今日卖出金额={stock.today_sell_value:.2f} 超过额度，跳过卖出")
                continue
            if C.total_sell > 500000:
                print(f"总卖出金额={C.total_sell:.2f} 超过额度，跳过卖出")
                continue
            
            # 计算卖出数量
            sell_amount = stock.single_buy_amount
            sell_amount = min(sell_amount, stock.current_position - stock.min_position)
            if sell_amount > 0:
                # 检查卖出时间间隔
                current_time = int(datetime.now().timestamp())
                if stock.last_sell_time and current_time - stock.last_sell_time < stock.interval:
                    print(f"{stock.name}卖出时间间隔不足，跳过卖出")
                    continue
                    
                # 提交卖出指令 注意这里只是提交卖出请求，并不一定成交，所以设定需要刷新的标记，下一轮会刷新持仓信息
                submit_sell_order(C, stock, sell_amount, current_price, "str1001")
                stock.last_sell_time = current_time
                C.need_refresh_position = 3
                

def submit_sell_order(C, stock, sell_amount, price, strategy_remark):
    """
    提交卖出指令并更新持仓信息
    
    Args:
        C: 全局上下文
        code: 股票代码
        sell_amount: 卖出数量
        price: 卖出价格
        strategy_remark: 策略编号
    """
    code = stock.code
    # 执行卖出
    passorder(24, 1101, C.accID, code, 11, price, sell_amount, strategy_remark, 1, strategy_remark, C)
    
    # 记录交易日志
    print(f"卖出 {stock.name}: 价格={price}, 数量={sell_amount}")

def submit_buy_order(C, stock, buy_amount, price, strategy_remark):
    """
    提交买入指令并更新持仓信息
    
    Args:
        C: 全局上下文
        code: 股票代码
        buy_amount: 买入数量
        price: 买入价格
        strategy_remark: 策略编号
    """
    code = stock.code
    # 执行买入
    passorder(23, 1101, C.accID, code, 11, price, buy_amount, strategy_remark, 1, strategy_remark, C)
    
    # 记录交易日志
    print(f"买入 {stock.name}: 价格={price}, 数量={buy_amount}")