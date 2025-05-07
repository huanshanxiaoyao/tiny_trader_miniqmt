from .base_strategy import BaseStrategy
from data.tick_sequence import TickSequence
from data_provider import DataProvider
import numpy as np
import datetime
from logger import logger 

class Strategy1004(BaseStrategy):
    """
    北交所-A股联动策略
    当北交所股票对应的所有A股股票上涨，且至少2只涨幅>2%，
    同时北交所股票涨幅<1%时，生成买入信号
    TODO 1： 未考虑卖出逻辑，且不能T0 所以至少要第二天卖出，要想一下
    TODO 2: 关联股票的相关性，需要后续边验证，边完善
    TODO 3: 该策略是实时计算逻辑，不支持back_test 一些函数接口也略有不同
    """
    def __init__(self, codes, correlations):
        super().__init__(codes)
        self.str_remark = "str1004"

        self.correlations_results = correlations
        self.a_codes = []
        for k, v in self.correlations_results.items():
            sim_stocks = v['similar_stocks']
            for stock in sim_stocks:
                self.a_codes.append(stock.get('code'))

        self.min_a_stocks = 2  # 最少需要2只A股满足条件
        self.a_min_increase = 0.02  # A股最小涨幅2%
        self.bj_max_increase = 0.03  # 北交所最大涨幅3%

        self.single_trade_value = 8000

        self.code2tick_seq =  {}  

        
    def trigger(self, ticks):
        """
        触发策略判断
        :param ticks: 相关股票行情数据字典
        :return: list of (股票对象, 交易类型, 交易数量, 策略标识) 或 空列表
        """
        trade_signals = []
        for code, tick in ticks.items():
            if code in self.target_codes:
                if code not in self.code2tick_seq:
                    self.code2tick_seq[code] = TickSequence(code)          
                self.code2tick_seq[code].add_tick(tick)
        

        current_time = datetime.datetime.now()
        start_time_dt = current_time - datetime.timedelta(minutes=1)
        # 格式化为"YYYYMMDDHHMMSS"格式
        start_minutes = start_time_dt.strftime('%Y%m%d%H%M00')

        # 遍历所有目标股票
        for stock in self.target_stocks:
            bj_code = stock.code
            cor_result = self.correlations_results.get(bj_code, {})
            if not cor_result:
                logger.warning(f"股票{bj_code}没有对应的A股股票")
                continue
            
            if bj_code not in self.code2tick_seq:
                logger.warning(f"股票{bj_code}没有对应的tick序列")
                #TODO get_full_tick 获取最近的历史数据
                continue

            tick = ticks.get(bj_code)
            if not tick:
                continue
                
            current_price = tick['lastPrice']
            stock.current_price = current_price    

            slope, pct = self.code2tick_seq[bj_code].calculate_price_trend()
            logger.info(f"股票{bj_code}涨幅 {pct:.2%} slope:{slope:.2f}")

            # 北交所股票涨幅
            bj_increase = pct
            
            # 获取相关联的A股股票
            sim_stocks = cor_result.get('similar_stocks', [])
            if not sim_stocks:
                logger.warning(f"股票{bj_code}没有对应的A股相似股票")
                continue
                
            strong_buy = 0
            strong_sell = 0

            #获取分钟数据
            code2data = self.get_minute_data(self.a_codes, start_minutes)
            #获取最新tick数据，为了最新价格和昨日收盘
            code2realtime = DataProvider.get_full_ticks(self.a_codes)

            # 遍历所有关联的A股股票
            #这里逻辑有个调整，涨幅判断依赖实时取的分钟及数据，然后和昨日收盘价对比
            for a_stock in sim_stocks:
                a_code = a_stock['code']
                tick = code2realtime.get(a_code, {})
                lastPrice = tick.get('lastPrice', 0)
                lastClose = tick.get('lastClose', 0)
                openPrice = tick.get('open', 0)
                    
                if not lastPrice or not lastClose:
                    logger.warning(f"股票{a_code}没有对应的lastPrice,lastClose")
                    continue
                a_pct = lastPrice/lastClose - 1
                
                today_minutes = code2data.get(a_code, {})
                today_minute_voluem = today_minutes.get('volume', 0)
                history_minutes = self.code2minutes_data.get(a_code, {})
                history_avg_volume = history_minutes.get(start_minutes, 0)
                logger.info(f"股票{a_code}今日成交量 {today_minute_voluem}, 历史平均成交量 {history_avg_volume}")
                # 检查最近一分钟成交量是否是过去5个交易日同一时间成交量的3倍以上
                volume_multiple = today_minute_voluem / avg_volume if history_avg_volume else 0 
                volume_surge = volume_multiple >= 3.0
                
                
                # 如果满足成交量激增条件，且涨幅差大于3%，strong_buy加1
                if volume_surge and (a_pct - bj_increase > 0.03):
                    strong_buy += 1
                
                # 获取当前和昨日的z-score
                # 计算当前z-score
                # 获取北交所股票当前价格
                bj_current_price = stock.current_price
                # 获取A股股票当前价格
                a_current_price = lastPrice
                # 计算比值
                price_ratio = bj_current_price / a_current_price if a_current_price else 0
                # 计算z-score：(当前比值 - 均值) / 标准差
                mean = a_stock.get('mean', 0)
                std = a_stock.get('std', 1)  # 默认为1避免除以0
                current_z_score = (price_ratio - mean) / std if std else 0
                # 从历史数据中获取昨日z-score
                yesterday_z_score = a_stock.get('z_score', 0)
                logger.info(f"股票{a_code}当前z-score: {current_z_score:.2f}, 昨日z-score: {yesterday_z_score:.2f}, 今日涨幅: {a_pct:.2%}")
                
                # z-score相关判断
                if current_z_score < -1 and yesterday_z_score > -1:
                    strong_buy += 1
                
                if current_z_score > 0 and yesterday_z_score < 0:
                    strong_sell += 1
                
                if current_z_score > -0.5 and (current_z_score - yesterday_z_score) < -0.1:
                    strong_sell += 1
            
            # 生成交易信号
            if strong_sell > 1:
                volume = self.single_trade_value // current_price
                remark = f"A股强卖信号: strong_sell={strong_sell}"
                logger.info(f"触发卖出信号: 股票 {bj_code} 涨幅 {pct:.2%} {remark}")
                trade_signals.append((stock, 'sell', volume, self.str_remark))
            
            elif strong_buy > 1:
                # 检查北交所股票涨幅是否小于阈值
                if bj_increase < self.bj_max_increase:
                    volume = self.single_trade_value // current_price
                    remark = f"A股强买信号: strong_buy={strong_buy}"
                    logger.info(f"触发买入信号: 股票 {bj_code} 涨幅 {pct:.2%} {remark}")
                    trade_signals.append((stock, 'buy', volume, self.str_remark))

        return trade_signals

    def fill_data(self):
        """
        目前先只依赖实时行情数据，不需要填充历史数据等
        """
        self.load_history_minute_avg_volume(self.a_codes)
        return

    def load_history_minute_avg_volume(self, codes):
        """
        获取过去5个交易日交易时间范围内所有分钟的平均交易量
        交易时间范围：9:00-11:30和13:00-15:00
        :param codes: 股票代码列表
        :return: 无返回值，结果保存在self.code2minutes_data中
        """
        import numpy as np
        
        # 获取当前日期
        current_date = datetime.datetime.now()
        
        # 计算10天前的日期（为了确保能获取到5个交易日的数据）
        start_date = (current_date - datetime.timedelta(days=10)).strftime('%Y%m%d')
        end_date = current_date.strftime('%Y%m%d')
        
        # 初始化结果字典
        self.code2minutes_data = {}
        
        # 获取历史分钟数据
        data = DataProvider.get_local_data(['volume'], codes, '1m', start_date, end_date)
        
        if data is not None:
            # 遍历每个股票代码
            for code in codes:
                if code in data:
                    stock_df = data[code]
                    
                    # 初始化该股票的数据字典
                    self.code2minutes_data[code] = {}
                    
                    # 按时间点分组数据
                    time_point_data = {}
                    
                    # 遍历所有时间索引
                    for time_idx in stock_df.index:
                        time_str = str(time_idx)
                        
                        # 检查时间格式是否正确
                        if len(time_str) >= 12:
                            hour = int(time_str[8:10])
                            minute = int(time_str[10:12])
                            
                            # 检查是否在交易时间范围内（9:00-11:30和13:00-15:00）
                            is_trading_time = (
                                (9 <= hour < 11) or 
                                (hour == 11 and minute <= 30) or
                                (13 <= hour < 15)
                            )
                            
                            if is_trading_time:
                                # 提取时间点（小时和分钟）作为键
                                time_point = time_str[8:12]  # 例如：0930, 1345
                                
                                # 获取该时间点的交易量
                                volume = stock_df.loc[time_idx, 'volume']
                                
                                # 如果该时间点不在字典中，初始化为空列表
                                if time_point not in time_point_data:
                                    time_point_data[time_point] = []
                                
                                # 添加交易量到对应时间点的列表中
                                if not np.isnan(volume):
                                    time_point_data[time_point].append(volume)
                    
                    # 计算每个时间点的平均交易量（最多取最近5个交易日的数据）
                    for time_point, volumes in time_point_data.items():
                        # 取最近5个交易日的数据
                        recent_volumes = volumes[-5:] if len(volumes) > 5 else volumes
                        
                        if recent_volumes:
                            # 计算平均值
                            avg_volume = sum(recent_volumes) / len(recent_volumes)
                            
                            # 构建完整的时间点格式（YYYYMMDDHHMMSS）
                            # 使用当前日期作为基准
                            full_time_point = current_date.strftime('%Y%m%d') + time_point + '00'
                            
                            # 保存到结果字典中
                            self.code2minutes_data[code][full_time_point] = avg_volume
                
                else:
                    # 如果没有该股票的数据，初始化为空字典
                    self.code2minutes_data[code] = {}
        
        return

    def get_minute_data(self, codes, start_minutes):
        #TODO 从设计角度，这里的获取实时行情数据以及处理，应该作为一个独立于策略的模块，后续考虑优化

        code2data = {}
        data = DataProvider.get_market_data_ex(['close', 'open', 'high', 'low', 'volume'], codes, '1m', start_minutes)
        # 解析数据（适应实际数据格式）
        if data is not None:
            # 打印获取到的股票数量
            print(f"获取到的股票数量: {len(data)}")
        
            # 遍历每个股票的数据
            for code, stock_df in data.items():
                print(f"\n股票 {code} 的数据:")
                
                # 获取时间索引
                time_indices = stock_df.index
                print(f"获取到的数据时间点数量: {len(time_indices)}")
                
                # 初始化该股票的数据字典
                code2data[code] = {}
                
                # 如果有数据
                if len(time_indices) > 0:
                    # 获取最新的时间戳
                    latest_ts_str = str(time_indices[-1])
                    
                    # 存储时间戳
                    code2data[code]['timestamp'] = latest_ts_str
                    
                    # 获取最新的收盘价和成交量
                    if 'close' in stock_df.columns and 'volume' in stock_df.columns:
                        latest_close = stock_df['close'].iloc[-1]
                        latest_volume = stock_df['volume'].iloc[-1]
                        
                        # 存储收盘价和成交量
                        code2data[code]['close'] = latest_close
                        code2data[code]['volume'] = latest_volume
                        
                        print(f"最新数据 - 时间: {latest_ts_str}, 收盘价: {latest_close}, 成交量: {latest_volume}")
                    else:
                        print(f"数据缺失 - 股票 {code} 没有收盘价或成交量数据")
                else:
                    print(f"没有数据 - 股票 {code} 没有时间序列数据")
        
        return code2data