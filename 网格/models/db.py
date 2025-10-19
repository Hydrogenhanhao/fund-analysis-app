import sqlite3
import pandas as pd
from config import DATABASE_PATH

class Database:
    """数据库连接管理类"""
    @staticmethod
    def get_conn():
        """获取数据库连接"""
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # 支持按列名访问
        return conn

    @staticmethod
    def init_db():
        """初始化数据库表结构（修复注释格式）"""
        conn = Database.get_conn()
        cursor = conn.cursor()
        
        # 1. 基金信息表（使用--注释）
        cursor.execute('''CREATE TABLE IF NOT EXISTS funds (
                            fund_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            fund_name TEXT NOT NULL UNIQUE, -- 基金名称唯一
                            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                          )''')
        
        # 2. 基金数据表（删除#注释，改用--或直接删除注释）
        cursor.execute('''CREATE TABLE IF NOT EXISTS fund_data (
                            data_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            fund_id INTEGER NOT NULL, -- 关联基金ID
                            date TEXT NOT NULL, -- 日期（格式YYYY-MM-DD）
                            net_value REAL NOT NULL, -- 净值（非空）
                            addition REAL, -- 加额（可为空，正数加仓/负数减仓）
                            shares REAL, -- 加份（可为空）
                            FOREIGN KEY (fund_id) REFERENCES funds(fund_id),
                            UNIQUE(fund_id, date) -- 同一基金日期不可重复
                          )''')
        
        conn.commit()
        conn.close()

    @staticmethod
    def query_to_df(query, params=None):
        """执行查询并返回DataFrame"""
        conn = Database.get_conn()
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        return df