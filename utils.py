from trade_days import TradeDays

def get_trading_days(start_date, end_date):
    """
    获取指定日期范围内的交易日列表
    
    :param start_date: 开始日期，格式为"20240101"
    :param end_date: 结束日期，格式为"20240101"
    :return: 按时间顺序排列的交易日列表
    """
    # 确保输入格式正确
    if not (isinstance(start_date, str) and isinstance(end_date, str)):
        raise TypeError("日期必须是字符串格式")
    
    if len(start_date) != 8 or len(end_date) != 8:
        raise ValueError("日期格式必须为'YYYYMMDD'")
    
    # 获取在日期范围内的交易日
    trading_days = []
    for day in TradeDays:
        if start_date <= day <= end_date:
            trading_days.append(day)
    
    return trading_days