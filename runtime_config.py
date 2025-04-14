# 日志配置
LOG_CONFIG = {
    "log_level": "INFO",
    "log_file": "trading.log",
    "console_output": True
}

# 运行时配置
RUNTIME_CONFIG = {
    "update_interval": 60,       # 数据更新间隔（秒）
    "max_retry_times": 3,        # 最大重试次数
    "retry_interval": 5,         # 重试间隔（秒）
    "heartbeat_interval": 30,    # 心跳检测间隔（秒）
}
