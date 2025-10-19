import pandas as pd
from config import DECIMAL_PRECISION

class InvestmentCalculator:
    """投资计算服务（实现核心指标计算）"""
    @staticmethod
    def calculate(history_df):
        """计算所有指标"""
        if history_df is None or history_df.empty:
            return pd.DataFrame()
        
        df = history_df.copy()
        # 处理日期格式和空值
        df['date'] = pd.to_datetime(df['date'])
        df['addition'] = pd.to_numeric(df['addition'], errors='coerce').fillna(0)
        df['shares'] = pd.to_numeric(df['shares'], errors='coerce').fillna(0)
        df = df.sort_values('date').reset_index(drop=True)

        # ===== 加额/加份互算 =====
        for i in range(len(df)):
            net = df.loc[i, 'net_value']
            add = df.loc[i, 'addition']
            shr = df.loc[i, 'shares']
            
            if net == 0:
                continue  # 避免除零错误
            
            # 已知加额算加份
            if add != 0 and shr == 0:
                df.loc[i, 'shares'] = add / net
            # 已知加份算加额
            elif shr != 0 and add == 0:
                df.loc[i, 'addition'] = shr * net

        # ===== 初始化计算列 =====
        df['总额'] = 0.0
        df['总份'] = 0.0
        df['净值涨幅(%)'] = 0.0
        df['总投入'] = 0.0
        df['总涨幅(%)'] = 0.0
        df['加额最新涨幅(%)'] = 0.0
        df['到手增额'] = ''
        df['到手增幅'] = ''
        df['到手总增额'] = 0.0

        # ===== 第一天数据 =====
        if len(df) > 0:
            df.loc[0, '总份'] = df.loc[0, 'shares']
            df.loc[0, '总额'] = df.loc[0, 'addition']
            df.loc[0, '总投入'] = df.loc[0, 'addition']

        # ===== 后续日期计算 =====
        for i in range(1, len(df)):
            prev_total_shares = df.loc[i-1, '总份']
            current_net = df.loc[i, 'net_value']
            current_add = df.loc[i, 'addition']
            
            # 基础指标
            df.loc[i, '总份'] = prev_total_shares + df.loc[i, 'shares']
            df.loc[i, '总额'] = prev_total_shares * current_net + current_add
            df.loc[i, '总投入'] = df.loc[i-1, '总投入'] + current_add

            # 净值涨幅
            prev_net = df.loc[i-1, 'net_value']
            if prev_net != 0:
                df.loc[i, '净值涨幅(%)'] = (current_net - prev_net) / prev_net * 100

            # 总涨幅（新公式：(负额和+总额)/加额和-1）
            sum_pos = df.loc[:i, 'addition'][df.loc[:i, 'addition'] > 0].sum()
            sum_neg = abs(df.loc[:i, 'addition'][df.loc[:i, 'addition'] < 0].sum())
            if sum_pos != 0:
                total_increase_rate = (sum_neg + df.loc[i, '总额']) / sum_pos - 1
                df.loc[i, '总涨幅(%)'] = total_increase_rate * 100
            else:
                df.loc[i, '总涨幅(%)'] = 0  # 避免除零错误

            # 到手增额/增幅（仅加额为负时）
            if current_add < 0:
                剩余加份 = abs(df.loc[i, 'shares'])
                过往加额正 = df.loc[:i-1][df.loc[:i-1, 'addition'] > 0].sort_values('net_value')
                # 初始化剩余份额列（如不存在）
                if 'remaining_shares' not in df.columns:
                    df['remaining_shares'] = df['shares'].copy()
                
                增额列表, 增幅列表 = [], []
                过往加额正 = df.loc[:i-1][(df.loc[:i-1, 'addition'] > 0) & (df.loc[:i-1, 'remaining_shares'] > 1e-8)].sort_values('net_value')
                
                for idx, row in 过往加额正.iterrows():
                    if 剩余加份 <= 1e-8:
                        break
                    可用加份 = row['remaining_shares']
                    用份 = min(剩余加份, 可用加份)
                    
                    if 用份 > 0:
                        增额 = 用份 * (current_net - row['net_value'])
                        增幅 = (current_net - row['net_value']) / row['net_value'] * 100
                        增额列表.append(f"{增额:.2f}")
                        增幅列表.append(f"{增幅:.2f}%")
                        # 更新剩余份额
                        df.at[idx, 'remaining_shares'] -= 用份
                    # 记录完全提取时的净值
                    if df.at[idx, 'remaining_shares'] <= 1e-8:
                        df.at[idx, 'final_net_value'] = current_net
                    剩余加份 -= 用份
                
                df.loc[i, '到手增额'] = '，'.join(增额列表)
                df.loc[i, '到手增幅'] = '，'.join([f"{float(x.replace('%','')):.2f}%" for x in 增幅列表])

        # ===== 加额最新涨幅 =====
        最新净值 = df.iloc[-1]['net_value'] if not df.empty else 0
        # 计算加额最新涨幅，已完全提取的使用提取时净值
        df['加额最新涨幅(%)'] = df.apply(
            lambda row: 0 if row['addition'] < 0 
    else (row['final_net_value'] - row['net_value']) / row['net_value'] * 100 
    if (row['addition'] != 0 and not pd.isna(row.get('final_net_value'))) 
    else (最新净值 - row['net_value']) / row['net_value'] * 100 
    if row['addition'] != 0 
    else 0, 
            axis=1
        )

        # ===== 到手总增额（累加）=====
        def sum_gain(row):
            if row['到手增额']:
                return sum(float(x) for x in row['到手增额'].split('，') if x)
            return 0
        df['到手增额_数值'] = df.apply(sum_gain, axis=1)
        df['到手总增额'] = df['到手增额_数值'].cumsum()

        # ===== 格式化输出 =====
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        for col in ['净值涨幅(%)', '总涨幅(%)', '加额最新涨幅(%)']:
            df[col] = df[col].round(2).astype(str) + '%'
        
        # 重命名列并保留需要的字段
        result_df = df[[
            'date', 'net_value', 'addition', 'shares', '总额', '总份', 
            '净值涨幅(%)', '总投入', '总涨幅(%)', '加额最新涨幅(%)', 
            '到手增额', '到手增幅', '到手总增额'
        ]].rename(columns={
            'date': '日期',
            'net_value': '净值',
            'addition': '加额',
            'shares': '加份'
        })

        # 设置数值精度
        float_cols = ['净值', '加额', '加份', '总额', '总份', '总投入', '到手总增额']
        for col in float_cols:
            result_df[col] = result_df[col].round(DECIMAL_PRECISION)

        return result_df