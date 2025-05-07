from datetime import datetime
from xtquant import xtdata
from logger import logger
from utils import get_trading_days

class DataProvider:
    """
    数据提供者类
    用于获取历史行情数据和离线数据
    """
    @staticmethod
    def get_trading_calendar(start_date, end_date):
        #xtdata本来有接口，但需要收费，暂时先使用本地数据,目前只支持2024和2025年日期
        #return xtdata.get_trading_calendar(start_date, end_date)
        return get_trading_days(start_date, end_date) 

    @staticmethod
    def get_full_ticks(codes):
        data = xtdata.get_full_tick(codes)
        return data

    @staticmethod
    def get_market_data_ex(fields, codes, period, start_time):
        data = xtdata.get_market_data_ex(fields, codes, period, start_time)
        return data

    @staticmethod
    def get_local_data(fileds, codes, period, start_date, end_date):
        data = xtdata.get_local_data(fileds, codes, period, start_date, end_date)
        return data

    @staticmethod
    def download_history_data_incrementally(code_list, period='1d'):
        """
        增量下载指定股票代码列表的历史数据
        :param code_list: 股票代码列表
        :param period: 数据周期，默认为日线'1d'
        :return: 成功下载的股票数量
        """
        success_count = 0
        total_count = len(code_list)
        
        logger.info(f"开始增量下载 {total_count} 只股票的历史数据...")
        
        for i, code in enumerate(code_list):
            try:
                #增量接口不符合预期，先手动指标日期
                start_date = "20240101"
                end_date = "20250415"
                xtdata.download_history_data(code, period, start_date, end_date)
                success_count += 1
                if (i+1) % 10 == 0 or (i+1) == total_count:
                    logger.info(f"已下载 {i+1}/{total_count} 只股票的历史数据")
            except Exception as e:
                logger.error(f"下载 {code} 历史数据时出错: {str(e)}")
        
        logger.info(f"历史数据下载完成，成功: {success_count}/{total_count}")
        return success_count

    @staticmethod
    def get_daily_data(code_list, start_date, end_date):
        """
        获取指定日期范围内的股票日均价
        :param code_list: 股票代码列表
        :param start_date: 开始日期，格式：YYYYMMDD
        :param end_date: 结束日期，格式：YYYYMMDD
        :return: dict, key为股票代码，value为均价
        """
        # 确保数据下载
        #logger.info(f"尝试下载历史数据{code_list} {start_date} {end_date}")
        for code in code_list:
            xtdata.download_history_data(code, "1d", start_date, end_date)

        # 获取历史数据
        data = xtdata.get_market_data(
            ['close'],
            code_list,
            period='1d',
            start_time=start_date,
            end_time=end_date,
        )

        code2daily = {}
        if data is not None and 'close' in data:
            close_data = data['close']
            for code in code_list:
                if code in close_data.index:
                    prices = close_data.loc[code].values
                    valid_prices = prices[prices > 0]  # 过滤无效价格
                    if len(valid_prices) > 0:
                        code2daily[code] = valid_prices.tolist()  # 将 numpy array 转换为 list
                    else:
                        code2daily[code] = []
                        logger.warning(f"{code} 在指定时间段内没有有效的价格数据")
                else:
                    code2daily[code] = []
                    logger.warning(f"{code} 未在数据中找到")
        else:
            logger.error("获取历史数据失败")

        return code2daily


if __name__ == '__main__':
    data_provider = DataProvider()
    code_list = ["000001.SZ", "600000.SH","839493.BJ"]
    start_date = "20250427"
    end_date = "20250428"
    from config import BJ_ALL,BASKET2, SH50
    #prices = data_provider.get_daily_data(SH50, start_date, end_date)
    #for code, prices in prices.items():
    #    print(f"{code} prices: {type(prices)}, {prices}")
    data_provider.download_history_data_incrementally(SH50)
    data = xtdata.get_market_data(
            ['close'],
            ["601398.SH"],
            period='1d',
            start_time=start_date,
            end_time=end_date, )
    #print(data)
    
    # 解析并打印每天的数据
    if data is not None and 'close' in data:
        close_data = data['close']
        if "601398.SH" in close_data.index:
            # 获取日期索引和价格
            dates = close_data.columns
            prices = close_data.loc["601398.SH"].values
            
            print(f"{'日期':<12}{'收盘价':<10}")
            print("-" * 22)
            for date, price in zip(dates, prices):
                # 将日期从Timestamp转为字符串格式
                date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
                print(f"{date_str:<12}{price:<10.2f}")
        else:
            print("未找到601398.SH的数据")
    else:
        print("获取数据失败或数据结构不符合预期")
    
    