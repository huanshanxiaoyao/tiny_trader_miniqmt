import os
import json
import pandas as pd
from datetime import datetime
from logger import logger

class BaseAccount:
    """
    账户基类，定义账户的基本属性和方法
    """
    def __init__(self, account_id, data_dir="sim_data", initial_cash=1000000.0):
        """
        初始化账户基类
        :param account_id: 账户ID
        :param data_dir: 数据存储目录
        :param initial_cash: 初始资金
        """
        self.account_id = account_id
        self.is_simulated = True  # 默认为模拟账户，实盘账户要重置
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), data_dir)
        self.initial_cash = initial_cash

        self.account_file = os.path.join(self.data_dir, f"{account_id}.json")
        self.positions_file = os.path.join(self.data_dir, f"{account_id}_positions.json")
        self.trades_file = os.path.join(self.data_dir, f"{account_id}_trades.json")
        
    def init_log_files(self):
        # 确保数据目录存在
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # 尝试加载已有数据，如果不存在则初始化
        ret = False
        if os.path.exists(self.account_file):
            ret = self._load_account()
        if not ret:
            logger.warning(f"账户数据文件不存在或数据不完整，将使用初始资金 {self.initial_cash} 初始化账户")
            # 账户基本信息
            self.cash = self.initial_cash       # 可用资金
            self.free_cash = self.initial_cash  # 可使用的资金（考虑冻结资金后）
            self.frozen_cash = 0.0         # 冻结资金
            self.market_value = 0.0        # 持仓市值
            self.total_asset = self.cash # 总资产
            self.commission = 0.0          # 累计手续费
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.updated_at = self.created_at
            self.last_update_time = datetime.now()  # 兼容旧代码
            
            # 保存初始账户数据
            self._save_account()
        
        # 加载持仓数据
        if os.path.exists(self.positions_file):
            self._load_positions()
        else:
            # 持仓信息
            self.positions = {}  # 股票代码 -> 持仓信息
            self._save_positions()
        
        # 加载交易记录
        if os.path.exists(self.trades_file):
            self._load_trades()
        else:
            # 交易记录
            self.trades = []
            self._save_trades()
        
        logger.info(f"账户 {self.account_id} 初始化完成，总资产: {self.total_asset:.2f}")
    
    def update_prices(self, code2price):
        """
        更新持仓股票的价格
        :param code2price: 股票代码到价格的映射
        """
        updated = False
        # 先更新每个持仓的市值
        for code, price in code2price.items():
            if code in self.positions and price > 0:
                position = self.positions[code]
                old_market_value = position.get('market_value', 0.0)
                
                # 更新市值
                volume = position.get('volume', 0)
                new_market_value = volume * price
                position['market_value'] = new_market_value
                position['last_price'] = price
                
                # 更新盈亏
                cost = position.get('cost', 0.0)
                position['profit'] = new_market_value - cost
                if cost > 0:
                    position['profit_ratio'] = position['profit'] / cost
                else:
                    position['profit_ratio'] = 0.0
                
                updated = True
                logger.debug(f"更新股票 {code} 价格: {price}, 市值: {old_market_value:.2f} -> {new_market_value:.2f}")
        
        if updated:
            # 更新市值和总资产
            self._update_market_value()
            
            # 更新所有持仓的持仓比例
            for code, position in self.positions.items():
                if self.total_asset > 0:
                    position['position_ratio'] = position['market_value'] / self.total_asset
                else:
                    position['position_ratio'] = 0.0
            
            # 保存数据
            self._save_account()
            self._save_positions()
            
            logger.debug(f"更新账户市值: {self.market_value:.2f}, 总资产: {self.total_asset:.2f}")
        
        return updated

    def _load_account(self):
        """加载账户数据"""
        try:
            with open(self.account_file, 'r', encoding='utf-8') as f:
                account_data = json.load(f)
            
            # 检查必要的属性是否存在
            required_fields = ['cash', 'frozen_cash', 'market_value', 'total_asset', 'commission', 'created_at', 'updated_at']
            for field in required_fields:
                if field not in account_data:
                    raise ValueError(f"账户数据文件缺少必要字段: {field}")
            
            # 直接赋值，不使用默认值
            self.cash = account_data['cash']
            self.free_cash = account_data.get('free_cash', self.cash)  # 兼容旧数据
            self.frozen_cash = account_data['frozen_cash']
            self.market_value = account_data['market_value']
            self.total_asset = account_data['total_asset']
            self.commission = account_data['commission']
            self.created_at = account_data['created_at']
            self.updated_at = account_data['updated_at']
            
            # 兼容旧代码
            self.last_update_time = datetime.strptime(self.updated_at, "%Y-%m-%d %H:%M:%S") if isinstance(self.updated_at, str) else self.updated_at
            
            logger.info(f"加载账户数据成功: {self.account_id}")
        except Exception as e:
            logger.error(f"加载账户数据失败: {e}", exc_info=True)
            return False
        return True
    
    def _save_account(self):
        """保存账户数据"""
        try:
            account_data = {
                'account_id': self.account_id,
                'cash': self.cash,
                'free_cash': self.free_cash,
                'frozen_cash': self.frozen_cash,
                'market_value': self.market_value,
                'total_asset': self.total_asset,
                'commission': self.commission,
                'created_at': self.created_at,
                'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(self.account_file, 'w', encoding='utf-8') as f:
                json.dump(account_data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"保存账户数据成功: {self.account_id}")
        except Exception as e:
            logger.error(f"保存账户数据失败: {e}", exc_info=True)
    
    def _load_positions(self):
        """加载持仓数据"""
        try:
            with open(self.positions_file, 'r', encoding='utf-8') as f:
                self.positions = json.load(f)
            
            logger.info(f"加载持仓数据成功: {self.account_id}, 持仓数量: {len(self.positions)}")
        except Exception as e:
            logger.error(f"加载持仓数据失败: {e}", exc_info=True)
            self.positions = {}
    
    def _save_positions(self):
        """保存持仓数据"""
        try:
            with open(self.positions_file, 'w', encoding='utf-8') as f:
                json.dump(self.positions, f, ensure_ascii=False, indent=4)
            
            logger.info(f"保存持仓数据成功: {self.account_id}, 持仓数量: {len(self.positions)}")
        except Exception as e:
            logger.error(f"保存持仓数据失败: {e}", exc_info=True)
    
    def _load_trades(self):
        """加载交易记录"""
        try:
            with open(self.trades_file, 'r', encoding='utf-8') as f:
                self.trades = json.load(f)
            
            logger.info(f"加载交易记录成功: {self.account_id}, 交易记录数量: {len(self.trades)}")
        except Exception as e:
            logger.error(f"加载交易记录失败: {e}", exc_info=True)
            self.trades = []
    
    def _save_trades(self):
        """保存交易记录"""
        try:
            with open(self.trades_file, 'w', encoding='utf-8') as f:
                json.dump(self.trades, f, ensure_ascii=False, indent=4)
            
            logger.info(f"保存交易记录成功: {self.account_id}, 交易记录数量: {len(self.trades)}")
        except Exception as e:
            logger.error(f"保存交易记录失败: {e}", exc_info=True)
    
    def get_position(self, code):
        """
        获取指定股票的持仓信息
        :param code: 股票代码
        :return: 持仓信息，如果没有持仓则返回None
        """
        return self.positions.get(code)
    
    def get_positions(self):
        """获取所有持仓信息"""
        return self.positions
    
    def get_positions_df(self):
        """获取持仓信息DataFrame"""
        if not self.positions:
            return pd.DataFrame()
        
        positions_list = list(self.positions.values())
        return pd.DataFrame(positions_list)
    
    def get_trades(self):
        """获取交易记录"""
        return self.trades
    
    def get_trades_df(self):
        """获取交易记录DataFrame"""
        if not self.trades:
            return pd.DataFrame()
        
        return pd.DataFrame(self.trades)
    
    def get_account_info(self):
        """获取账户信息"""
        return {
            'account_id': self.account_id,
            'cash': self.cash,
            'free_cash': self.free_cash,
            'frozen_cash': self.frozen_cash,
            'market_value': self.market_value,
            'total_asset': self.total_asset,
            'commission': self.commission,
            'position_count': len(self.positions),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_update_time': self.last_update_time
        }
    
    def get_available_cash(self):
        """获取可使用资金"""
        return self.free_cash
    
    def get_total_asset(self):
        """获取总资产"""
        return self.total_asset
    
    def get_market_value(self):
        """获取持仓市值"""
        return self.market_value
    
    def _update_market_value(self):
        """更新市值和总资产"""
        self.market_value = sum(position.get('market_value', 0) for position in self.positions.values())
        self.total_asset = self.cash + self.market_value + self.frozen_cash
        self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_update_time = datetime.now()  # 兼容旧代码
    
    #def update_positions(self,):
    """本地模拟账户，和本地与服务器同步更新的账户，持仓的更新完全不同，这里不做实现，不提供相同接口"""
    
    def reset(self, initial_cash=1000000.0):
        """
        重置账户状态
        :param initial_cash: 重置后的初始资金
        :return: 是否重置成功
        """
        try:
            # 备份原数据
            backup_time = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # 检查文件是否存在再备份
            if os.path.exists(self.account_file):
                os.rename(self.account_file, f"{self.account_file}.{backup_time}.bak")
            if os.path.exists(self.positions_file):
                os.rename(self.positions_file, f"{self.positions_file}.{backup_time}.bak")
            if os.path.exists(self.trades_file):
                os.rename(self.trades_file, f"{self.trades_file}.{backup_time}.bak")
            
            # 重置账户数据
            self.cash = initial_cash
            self.free_cash = initial_cash
            self.frozen_cash = 0.0
            self.market_value = 0.0
            self.total_asset = initial_cash
            self.commission = 0.0
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.updated_at = self.created_at
            self.last_update_time = datetime.now()  # 兼容旧代码
            
            # 重置持仓和交易记录
            self.positions = {}
            self.trades = []
            
            # 保存数据
            self._save_account()
            self._save_positions()
            self._save_trades()
            
            logger.info(f"账户 {self.account_id} 已重置，初始资金: {initial_cash:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"重置账户失败: {e}", exc_info=True)
            return False