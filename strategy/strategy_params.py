from stock_code_config import *
import json

#TODO
correlation_file_path = "../stock_miner/shared/correlation_results.json"
try:
    with open(correlation_file_path, 'r', encoding='utf-8') as file:
        correlation_results = json.load(file)
except FileNotFoundError:
    print(f"File not found: {correlation_file_path}")
    correlation_results = {}

STRATEGY_PARAMS = {
    1001: {
        "target_codes": BJ50  # 策略目标股票代码
    },
    1002: {
        "target_codes": SH50  # 策略目标股票代码
    },
    1003: {
        "target_codes": SH50  # 策略目标股票代码
    },
    1004: {
        "target_codes": BJCODE2RELATED_A.keys(),
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