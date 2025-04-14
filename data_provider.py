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

    def get_daily_avg(self, code_list, start_date, end_date):
        """
        获取指定日期范围内的股票日均价
        :param code_list: 股票代码列表
        :param start_date: 开始日期，格式：YYYYMMDD
        :param end_date: 结束日期，格式：YYYYMMDD
        :return: dict, key为股票代码，value为均价
        """
        # 确保数据下载
        for code in code_list:
            xtdata.download_history_data(code, "1d", start_date, end_date)

        # 获取历史数据
        data = xtdata.get_market_data(
            ['close'],
            code_list,
            period='1d',
            start_time=start_date,
            end_time=end_date
        )

        # 计算均价
        code2avg = {}
        if data is not None and 'close' in data:
            close_data = data['close']
            for code in code_list:
                prices = close_data.get(code, [])
                valid_prices = [p for p in prices if p > 0]  # 过滤无效价格
                if valid_prices:
                    code2avg[code] = sum(valid_prices) / len(valid_prices)
                else:
                    code2avg[code] = 0
                    logger.warning(f"{code} 在指定时间段内没有有效的价格数据")
        else:
            logger.error("获取历史数据失败")

        return code2avg


if __name__ == '__main__':
    data_provider = DataProvider()
    code_list = ['000001.SZ', '600000.SH']
    start_date = '20240101'
    end_date = '20240501'
    avg_prices = data_provider.get_daily_avg(code_list, start_date, end_date)
    print(avg_prices)