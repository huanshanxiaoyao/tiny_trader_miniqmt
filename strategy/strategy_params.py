from stock_code_config import *
import json

#TODO
correlation_file_path = "../stock_miner/shared/correlation_results.json"
safe_range_file_path = "../stock_miner/shared/stock_safe_range.json"
try:
    with open(correlation_file_path, 'r', encoding='utf-8') as file:
        correlation_results = json.load(file)
except FileNotFoundError:
    print(f"correlation file not found: {correlation_file_path}")
    correlation_results = {}

try:
    with open(safe_range_file_path, 'r', encoding='utf-8') as file:
        safe_range = json.load(file)
except FileNotFoundError:
    print(f"File not found: {correlation_file_path}")
    safe_range = {}

TempCodes = list(set(BJ50_Trust + HS300) - set(SH50))

STRATEGY_PARAMS = {
    1001: {
        "target_codes": TempCodes,  
        "safe_range": safe_range,
        "aggressiveness" : -2, # -2 超级保守， -1 保守， 0 平衡， 1 激进， 2 超级激进
    },
    1002: {
        "target_codes": SH50  # 策略目标股票代码
    },
    1003: {
        "target_codes": SH50  # 策略目标股票代码
    },
    1004: {
        "target_codes": correlation_results.keys(),
        "correlations":correlation_results
    }
}

# 收集所有活跃的股票代码
Active_Codes = []
# 添加所有策略的目标股票
for k, v in STRATEGY_PARAMS.items():
    Active_Codes.extend(v["target_codes"])
# 添加所有关联的A股代码
#for k, v in correlation_results.items():
#    Active_Codes.append(k)
#    sim_stocks = v['similar_stocks']
#    for sim_stock in sim_stocks:
#        Active_Codes.append(sim_stock['code'])
# 去除重复项
Active_Codes = list(set(Active_Codes))