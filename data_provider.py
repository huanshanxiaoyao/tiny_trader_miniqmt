from datetime import datetime
from xtquant import xtdata
from logger import logger

class DataProvider:
    """
    数据提供者类
    用于获取历史行情数据和离线数据
    """
    def __init__(self):
        pass

    def get_daily_data(self, code_list, start_date, end_date):
        """
        获取指定日期范围内的股票日均价
        :param code_list: 股票代码列表
        :param start_date: 开始日期，格式：YYYYMMDD
        :param end_date: 结束日期，格式：YYYYMMDD
        :return: dict, key为股票代码，value为均价
        """
        # 确保数据下载
        logger.info(f"尝试下载历史数据{code_list} {start_date} {end_date}")
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
            # 对每个股票代码计算均价
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
    start_date = "20250301"
    end_date = "20250401"
    prices = data_provider.get_daily_data(code_list, start_date, end_date)
    for code, prices in prices.items():
        print(f"{code} prices: {type(prices)}, {prices}")