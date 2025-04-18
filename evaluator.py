from datetime import datetime
from logger import logger

class Evaluator:
    """
    策略评估器，用于评估策略的回测效果
    """
    def __init__(self):
        self.evaluation_results = {}  # 存储各个策略的评估结果
        self.market_index = '899050.BJ'
    
    def evaluate_strategy(self, strategy_name, signals, target_stocks, code2daily, trade_days, initial_cash=1000000):
        """
        评估策略的回测效果
        
        :param strategy_name: 策略名称
        :param signals: 交易信号列表，每个信号为 (股票对象, 交易类型, 交易数量, 策略标记，idx)
        :param target_stocks: 目标股票列表
        :param code2daily: 股票代码到价格序列的映射字典，用于获取历史价格
        :param trade_days: 交易日列表
        :param initial_cash: 初始资金，默认100万
        :return: 评估结果字典
        """
        logger.info(f"开始评估策略: {strategy_name}")
        
        # 保存价格数据引用
        self.code2daily = code2daily or {}
        
        # 初始化评估状态
        cash = initial_cash  # 初始现金
        positions = {stock.code: 0 for stock in target_stocks}  # 初始持仓
        trades = []  # 交易记录
        daily_values = []  # 每日资产价值
        
        # 按照idx排序信号（确保按时间顺序处理）
        sorted_signals = sorted(signals, key=lambda x: x[3])
        
        # 处理每个交易信号
        for signal in sorted_signals:
            stock, trade_type, amount, str_remark, idx = signal
            
            # 获取交易日期和价格（假设在回测数据中可以获取）
            # 这里需要根据实际数据结构调整
            trade_date = self._get_date_from_idx(idx, trade_days)  # 需要实现这个方法
            trade_price = self._get_price_from_idx(stock.code, idx)  # 需要实现这个方法
            
            if trade_price <= 0:
                logger.warning(f"交易价格异常: {trade_price}，跳过此信号")
                continue
                
            # 执行交易
            if trade_type == 'buy':
                
                if amount <= 0:
                    logger.warning(f"计算的买入数量为0，跳过此买入信号")
                    continue
                    
                # 买入操作
                cost = trade_price * amount
                if cost <= cash:
                    cash -= cost
                    positions[stock.code] += amount
                    trades.append({
                        'date': trade_date,
                        'code': stock.code,
                        'type': 'buy',
                        'price': trade_price,
                        'amount': amount,
                        'cost': cost,
                        'cash_after': cash
                    })
                    logger.info(f"买入: {stock.code} {amount}股，价格: {trade_price}，花费: {cost}，剩余现金: {cash}, 交易日期: {trade_date}")
                else:
                    logger.warning(f"现金不足，无法买入: {stock.code} {amount}股，需要: {cost}，现有: {cash}")
            
            elif trade_type == 'sell':
                # 卖出操作
                if positions[stock.code] > 0:
                    # 如果持仓不足，则卖出所有剩余持仓
                    actual_sell_amount = min(positions[stock.code], amount)
                    income = trade_price * actual_sell_amount
                    cash += income
                    positions[stock.code] -= actual_sell_amount
                    trades.append({
                        'date': trade_date,
                        'code': stock.code,
                        'type': 'sell',
                        'price': trade_price,
                        'amount': actual_sell_amount,
                        'income': income,
                        'cash_after': cash
                    })
                    
                    if actual_sell_amount < amount:
                        logger.warning(f"持仓不足，部分卖出: {stock.code} {actual_sell_amount}股（原计划卖出{amount}股），价格: {trade_price}，收入: {income}，剩余现金: {cash}")
                    else:
                        logger.info(f"卖出: {stock.code} {actual_sell_amount}股，价格: {trade_price}，收入: {income}，剩余现金: {cash},交易日期: {trade_date}")
                else:
                    logger.warning(f"没有持仓，无法卖出: {stock.code}")
            
            # 计算当前总资产价值
            total_value = self._calculate_total_value(cash, positions, idx)
            curr_market_index_price = self._get_price_from_idx(self.market_index, idx)
            
            # 检查是否已存在相同日期的记录
            existing_entry = next((item for item in daily_values if item['date'] == trade_date), None)
            if existing_entry:
                # 如果存在相同日期的记录，则更新资产价值
                existing_entry['value'] = total_value
            else:
                # 如果不存在，则添加新记录
                daily_values.append({
                    'date': trade_date,
                    'value': total_value,
                    'market_index': curr_market_index_price,
                    'cash': cash
                })
        
        # 计算评估指标
        initial_value = initial_cash
        final_value = daily_values[-1]['value'] if daily_values else initial_cash
        total_return = (final_value / initial_value - 1) * 100
        
        # 存储评估结果
        result = {
            'strategy_name': strategy_name,
            'initial_cash': initial_cash,
            'final_cash': cash,
            'final_positions': positions,
            'final_value': final_value,
            'total_return': total_return,
            'trade_count': len(trades),
            #'trades': trades,
            #'daily_values': daily_values
        }
        
        self.evaluation_results[strategy_name] = result
        
        logger.info(f"策略评估完成: {strategy_name}, 总收益率: {total_return:.2f}%")
        for value in daily_values:
            logger.info(f"每日资产价值: {value['date']}, {value['value']:.2f}, 市场指数: {value['market_index']:.2f},cash: {value['cash']:.2f}")
        return result
    
    def _get_date_from_idx(self, idx, trade_days):
        """
        从索引获取日期
        使用TradeDays获取真实交易日期
        :param idx: 日期索引
        :return: 日期字符串
        """
        # 从trade_days获取真实交易日期
        if 0 <= idx < len(trade_days):
            return trade_days[idx]
        else:
            # 索引超出范围时使用相对日期
            logger.warning(f"日期索引 {idx} 超出交易日范围 [0, {len(trade_days)-1}]")
            return f"Day-{idx}"
    
    def _get_price_from_idx(self, code, idx):
        """
        从索引获取价格
        :param code: 股票代码
        :param idx: 价格索引
        :return: 价格
        """
        if not self.code2daily or code not in self.code2daily:
            logger.warning(f"没有找到股票 {code} 的价格数据")
            return 0.0
            
        prices = self.code2daily.get(code, [])
        if idx < 0 or idx >= len(prices):
            logger.warning(f"股票 {code} 的价格索引 {idx} 超出范围 [0, {len(prices)-1}]")
            return 0.0
            
        return prices[idx]
    
    def _calculate_total_value(self, cash, positions, idx):
        """
        计算当前总资产价值
        :param cash: 现金
        :param positions: 持仓
        :param idx: 当前索引
        :return: 总资产价值
        """
        total_value = cash
        
        # 计算所有持仓的市值
        for code, amount in positions.items():
            if amount > 0:
                price = self._get_price_from_idx(code, idx)
                total_value += price * amount
        
        return total_value
    
    def get_evaluation_result(self, strategy_name):
        """
        获取指定策略的评估结果
        :param strategy_name: 策略名称
        :return: 评估结果字典
        """
        return self.evaluation_results.get(strategy_name)
    
    def compare_strategies(self, strategy_names=None):
        """
        比较多个策略的表现
        :param strategy_names: 要比较的策略名称列表，如果为None则比较所有策略
        :return: 比较结果
        """
        if strategy_names is None:
            strategy_names = list(self.evaluation_results.keys())
        
        comparison = []
        for name in strategy_names:
            result = self.evaluation_results.get(name)
            if result:
                comparison.append({
                    'strategy_name': name,
                    'total_return': result['total_return'],
                    'trade_count': result['trade_count'],
                    'final_value': result['final_value']
                })
        
        # 按总收益率排序
        comparison.sort(key=lambda x: x['total_return'], reverse=True)
        
        return comparison