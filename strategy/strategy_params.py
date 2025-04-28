from stock_code_config import *

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
        "codeBJ2codeA":BJCODE2RELATED_A
    }
}

# 收集所有活跃的股票代码
Active_Codes = []
# 添加所有策略的目标股票
for k, v in STRATEGY_PARAMS.items():
    Active_Codes.extend(v["target_codes"])
# 添加所有关联的A股代码
for k, v in BJCODE2RELATED_A.items():
    Active_Codes.extend(v)
# 去除重复项
Active_Codes = list(set(Active_Codes))