from dotenv import load_dotenv
import os

#代码逻辑无关，且日常更改较多，放在.env文件中
load_dotenv()
try:
    PositionLevel = float(os.getenv("PositionLevel", "0.5"))  # 提供默认值 0.5
except (TypeError, ValueError):
    print("警告：PositionLevel 环境变量不是有效的数字，使用默认值 0.5")
    PositionLevel = 0.5