from datetime import datetime
from logger import logger
from base_account import BaseAccount

class LocalAccount(BaseAccount):
    """
    本地账户类，用于同步和管理服务器端的账户状态
    """
    def __init__(self, account_id):
        """
        初始化本地账户
        :param account_id: 账户ID
        """
        super().__init__(account_id)
        logger.info(f"初始化本地账户: {account_id}")
    
    def update_positions(self, account_info, positions, id2stock):
        """
        更新账户持仓信息
        :param account_info: 账户信息
        :param positions: 持仓信息
        :param id2stock: 股票代码到MyStock对象的映射
        """
        # 定义回调函数，用于更新股票对象的持仓信息
        def update_stock_position(code, position):
            if code in id2stock:
                id2stock[code].update_position(position)
        
        # 调用基类方法
        return super().update_positions(account_info, positions, update_stock_position)