import sys
import time
import pandas as pd
import os
import json
from xtquant.xttrader import XtQuantTrader
from xtquant.xttype import StockAccount
from xtquant import xtconstant
from datetime import datetime
from xtquant.xttrader import XtQuantTraderCallback
from xtquant import xtdata
import logging

# Configure logger
logger = logging.getLogger("account_updater")
logger.setLevel(logging.INFO)
# Create file handler
log_file = os.path.join("d:\\Users\\Jack\\xtquant\\logs", "account_updater.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 使用示例
# 在文件顶部导入区域添加
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 在 AccountUpdater 类中添加发送通知的方法
def send_notification(subject, message):
    """发送邮件通知"""
    try:
        # 邮件配置信息 - 请替换为你的实际信息
        sender = 'chong.su.hit@gmail.com'
        password = 'xnbubyjxbhlyjscd'  # 邮箱密码或授权码
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587  # 根据你的邮件服务商调整
        receivers = ['278171810@qq.com']  # 接收邮件的邮箱

        # 创建邮件内容
        msg = MIMEText(message, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = sender
        msg['To'] = ','.join(receivers)
        
        # 发送邮件
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # 使用TLS加密
        server.login(sender, password)
        server.sendmail(sender, receivers, msg.as_string())
        server.quit()
        
        logger.info(f"通知邮件已发送: {subject}")
        return True
    except Exception as e:
        logger.error(f"发送通知邮件失败: {str(e)}")
        return False


class AccountUpdater:

    def __init__(self, path, account_id, data_dir="d:\\Users\\Jack\\xtquant\\account_data"):
        self.path = path
        self.account_id = account_id
        self.session_id = int(time.time())
        self.trader = XtQuantTrader(path, self.session_id)
        self.account = StockAccount(account_id)
        self.data_dir = data_dir
        
        # Ensure data directories exist
        self._ensure_directories()
        
    
    def _ensure_directories(self):
        """Ensure data directories exist"""
        # Main data directory
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # Account info directory
        account_dir = os.path.join(self.data_dir, "account_positions")
        if not os.path.exists(account_dir):
            os.makedirs(account_dir)
            
        # Trade info directory
        trade_dir = os.path.join(self.data_dir, "trades_orders")
        if not os.path.exists(trade_dir):
            os.makedirs(trade_dir)
    
    def save_account_positions(self):
        """Save account and positions information to file"""
        today = datetime.now().strftime("%Y%m%d")
        file_path = os.path.join(self.data_dir, "account_positions", f"{today}.json")
        
        account_info = self.get_account_info()
        positions_df = self.get_positions()
        
        # Convert positions DataFrame to dict for JSON serialization
        positions_dict = positions_df.to_dict('records') if not positions_df.empty else []
        
        # Combine data
        data = {
            "account_info": account_info,
            "positions": positions_dict,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"账户和持仓信息已保存到 {file_path}")
        return file_path
    
    def save_trades_orders(self):
        """Save trades and orders information to file"""
        today = datetime.now().strftime("%Y%m%d")
        file_path = os.path.join(self.data_dir, "trades_orders", f"{today}.json")
        
        orders_df = self.get_orders()
        trades_df = self.get_trades()
        
        # Convert DataFrames to dict for JSON serialization
        orders_dict = orders_df.to_dict('records') if not orders_df.empty else []
        trades_dict = trades_df.to_dict('records') if not trades_df.empty else []
        
        # Combine data
        data = {
            "orders": orders_dict,
            "trades": trades_dict,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"委托和成交信息已保存到 {file_path}")
        return file_path
        
    def connect(self):
        """连接交易终端并订阅账户"""
        self.trader.start()
        if self.trader.connect() != 0:
            logger.error('【软件终端连接失败！】\n 请运行并登录miniQMT.EXE终端。')
            return False
            
        if self.trader.subscribe(self.account) != 0:
            logger.error('【账户信息订阅失败！】\n 账户配置错误，检查账号是否正确。')
            return False
            
        logger.info('【软件终端连接成功！】')
        logger.info('【账户信息订阅成功！】')
        return True

    def get_account_info(self):
        """获取账户资产信息"""
        asset = self.trader.query_stock_asset(self.account)
        if asset:
            return {
                "总资产": asset.total_asset,
                "持仓市值": asset.market_value,
                "可用资金": asset.cash,
                "冻结资金": asset.frozen_cash
            }
        return None

    def get_orders(self):
        """获取委托订单信息"""
        orders = self.trader.query_stock_orders(self.account)
        orders_df = pd.DataFrame([
            {
                "证券代码": order.stock_code,
                "委托数量": order.order_volume,
                "委托价格": order.price,
                "订单编号": order.order_id,
                "委托状态": order.status_msg,
                "报单时间": datetime.fromtimestamp(order.order_time).strftime('%H:%M:%S')
            }
            for order in orders
        ])
        return orders_df

    def get_trades(self):
        """获取成交信息"""
        trades = self.trader.query_stock_trades(self.account)
        trades_df = pd.DataFrame([
            {
                "StockCode": trade.stock_code,
                "Volume": trade.traded_volume,
                "Price": trade.traded_price,
                "Value": trade.traded_amount,
                "TradeType":trade.order_type,
                "Remark": trade.order_remark,
                "OrderId": trade.order_id,
                "TradeId": trade.traded_id,
                "TradeTime": datetime.fromtimestamp(trade.traded_time).strftime('%H:%M:%S')
            }
            for trade in trades
        ])
        return trades_df

    def get_positions(self):
        """获取持仓信息"""
        positions = self.trader.query_stock_positions(self.account)
        positions_df = pd.DataFrame([
            {
                "证券代码": position.stock_code,
                "持仓数量": position.volume,
                "可用数量": position.can_use_volume,
                "冻结数量": position.frozen_volume,
                "开仓价格": position.open_price,
                "持仓市值": position.market_value,
                "在途股份": position.on_road_volume,
                "昨夜持股": position.yesterday_volume
            }
            for position in positions
        ])
        return positions_df

    def print_summary(self):
        """打印账户汇总信息"""
        logger.info('-' * 18 + '【账户信息】' + '-' * 18)
        account_info = self.get_account_info()
        for key, value in account_info.items():
            logger.info(f"{key}: {value}")

        orders_df = self.get_orders()
        trades_df = self.get_trades()
        positions_df = self.get_positions()

        logger.info('-' * 18 + '【当日汇总】' + '-' * 18)
        logger.info(f"委托个数：{len(orders_df)} 成交个数：{len(trades_df)} 持仓数量：{len(positions_df)}")

        logger.info('-' * 18 + "【订单信息】" + '-' * 18)
        logger.info(str(orders_df) if not orders_df.empty else "无委托信息")

        logger.info('-' * 18 + "【成交信息】" + '-' * 18)
        logger.info(str(trades_df) if not trades_df.empty else "无成交信息")

        logger.info('-' * 18 + "【持仓信息】" + '-' * 18)
        logger.info(str(positions_df) if not positions_df.empty else "无持仓信息")



# 修改主函数部分
if __name__ == "__main__":
    path = r"D:\Apps\ZJ_QMT3\userdata_mini"
    account_id = "6681802088"
    
    try:
        trader = AccountUpdater(path, account_id)
        if trader.connect():
            # 打印账户信息
            trader.print_summary()
            trader.save_account_positions()
            trader.save_trades_orders()
            logger.info("账户数据更新成功")
            send_notification("账户数据更新成功", "message hello")
        else:
            error_msg = "无法连接到交易终端，请检查终端是否正常运行"
            logger.error(error_msg)
            send_notification("账户数据更新失败", error_msg)
            sys.exit(1)
    except Exception as e:
        error_msg = f"账户数据更新过程中发生错误: {str(e)}"
        logger.error(error_msg, exc_info=True)
        try:
            send_notification("账户数据更新失败", error_msg)
        except:
            logger.error("发送通知失败，请检查邮件配置")
        sys.exit(1)
