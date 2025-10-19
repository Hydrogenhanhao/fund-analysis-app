from models.db import Database
from datetime import datetime
import sqlite3

class Fund:
    """基金模型类"""
    def __init__(self, fund_id=None, fund_name=None):
        self.fund_id = fund_id
        self.fund_name = fund_name

    @classmethod
    def create(cls, fund_name):
        """创建新基金"""
        conn = Database.get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO funds (fund_name) VALUES (?)', (fund_name,))
            conn.commit()
            return cls(fund_id=cursor.lastrowid, fund_name=fund_name)
        except sqlite3.IntegrityError:
            # 基金名称已存在
            return None
        finally:
            conn.close()

    @classmethod
    def get_all(cls):
        """获取所有基金"""
        conn = Database.get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT fund_id, fund_name FROM funds ORDER BY create_time DESC')
        funds = [cls(fund_id=row['fund_id'], fund_name=row['fund_name']) for row in cursor.fetchall()]
        conn.close()
        return funds

    @classmethod
    def get_by_id(cls, fund_id):
        """通过ID获取基金"""
        conn = Database.get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT fund_id, fund_name FROM funds WHERE fund_id=?', (fund_id,))
        row = cursor.fetchone()
        conn.close()
        return cls(fund_id=row['fund_id'], fund_name=row['fund_name']) if row else None

    def save_data(self, date, net_value, addition=None, shares=None):
        """保存基金数据（支持更新）"""
        conn = Database.get_conn()
        cursor = conn.cursor()
        # 更新最后修改时间
        cursor.execute('UPDATE funds SET last_update=? WHERE fund_id=?', 
                      (datetime.now(), self.fund_id))
        # 保存/更新数据
        cursor.execute('''INSERT OR REPLACE INTO fund_data 
                         (fund_id, date, net_value, addition, shares) 
                         VALUES (?, ?, ?, ?, ?)''', 
                      (self.fund_id, date, net_value, addition, shares))
        conn.commit()
        conn.close()

    def update_name(self, new_name):
        """修改基金名称"""
        conn = Database.get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE funds SET fund_name=? WHERE fund_id=?', 
                          (new_name, self.fund_id))
            conn.commit()
            self.fund_name = new_name
            return True
        except sqlite3.IntegrityError:
            # 名称已存在
            return False
        finally:
            conn.close()

    def delete(self):
        """删除基金及关联数据"""
        conn = Database.get_conn()
        cursor = conn.cursor()
        try:
            # 先删除关联数据
            cursor.execute('DELETE FROM fund_data WHERE fund_id=?', (self.fund_id,))
            # 再删除基金
            cursor.execute('DELETE FROM funds WHERE fund_id=?', (self.fund_id,))
            conn.commit()
            return True
        except Exception as e:
            return False
        finally:
            conn.close()

    def get_history_data(self):
        """获取基金历史数据"""
        return Database.query_to_df('''
            SELECT date, net_value, addition, shares 
            FROM fund_data 
            WHERE fund_id=? 
            ORDER BY date
        ''', (self.fund_id,))