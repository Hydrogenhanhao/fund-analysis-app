from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import json
from services.fund_service import FundService
from services.calculator import InvestmentCalculator
from models.fund import Fund
from models.db import Database
from config_mobile import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, DECIMAL_PRECISION
from pyecharts.charts import Line
from pyecharts import options as opts
from datetime import datetime, timedelta
from pyecharts.commons.utils import JsCode

# 初始化应用
app = Flask(__name__)
app.secret_key = 'fund_analysis_mobile_system'

# 初始化数据库
Database.init_db()

# 确保有默认基金
if not FundService.get_fund_list():
    FundService.create_fund('默认基金')

@app.route('/', methods=['GET', 'POST'])
def index():
    funds = FundService.get_fund_list()
    current_fund_id = session.get('fund_id', funds[0].fund_id if funds else None)

    # 切换基金
    if request.method == 'POST' and 'fund_id' in request.form:
        current_fund_id = request.form['fund_id']
        session['fund_id'] = current_fund_id
        return redirect(url_for('index'))

    # 创建基金
    if request.method == 'POST' and 'new_fund' in request.form:
        fund_name = request.form['new_fund'].strip()
        if fund_name:
            fund, msg = FundService.create_fund(fund_name)
            if fund:
                session['fund_id'] = fund.fund_id
        return redirect(url_for('index'))

    # 更新基金名称
    if request.method == 'POST' and 'update_fund_name' in request.form:
        fund_id = request.form['fund_id']
        new_name = request.form['new_name'].strip()
        if fund_id and new_name:
            FundService.update_fund_name(fund_id, new_name)
        return redirect(url_for('index'))

    # 删除基金
    if request.method == 'POST' and 'delete_fund' in request.form:
        fund_id = request.form['fund_id']
        if fund_id:
            FundService.delete_fund(fund_id)
            # 重置会话如果当前基金被删除
            if session.get('fund_id') == fund_id:
                funds = FundService.get_fund_list()
                session['fund_id'] = funds[0].fund_id if funds else None
        return redirect(url_for('index'))

    # 提交数据
    if request.method == 'POST' and 'date' in request.form:
        if current_fund_id:
            fund = Fund.get_by_id(current_fund_id)
            if fund:
                date = request.form['date']
                net_value = float(request.form['net_value']) if request.form['net_value'] else 0
                addition = float(request.form['addition']) if request.form['addition'] else 0
                shares = float(request.form['shares']) if request.form['shares'] else 0
                fund.save_data(date, net_value, addition, shares)
        return redirect(url_for('index'))

    # 获取计算结果
    history_df, fund_name = FundService.get_fund_data(current_fund_id) if current_fund_id else (pd.DataFrame(), '')
    result_df = InvestmentCalculator.calculate(history_df)

    # 生成移动端优化的表格HTML
    table_html = generate_mobile_table(result_df)

    # 生成移动端优化的图表
    chart_html = generate_mobile_chart(history_df)

    return render_template(
        'mobile.html',
        funds=funds,
        current_fund_id=current_fund_id,
        current_fund_name=fund_name,
        table_html=table_html,
        chart_html=chart_html
    )

def generate_mobile_table(result_df):
    """生成移动端优化的表格HTML"""
    if result_df.empty:
        return '<div class="text-center text-muted py-4">暂无数据，请添加记录</div>'
    
    # 移动端表格：扩展为与桌面端一致的所有字段
    cols = [
        '日期', '净值', '加额', '加份', '总额', '总份',
        '净值涨幅(%)', '总投入', '总涨幅(%)', '加额最新涨幅(%)',
        '到手增额', '到手增幅'
    ]

    table_html = '''
    <div class="table-responsive mobile-table" style="margin-top: 10px;">
        <table class="table table-striped table-hover" style="min-width: 100%; table-layout: auto;">
            <thead class="table-dark">
                <tr>
    '''
    for c in cols:
        table_html += f'<th style="text-align: center; vertical-align: middle;">{c}</th>'
    table_html += '</tr></thead><tbody>'

    def get_field(series, col_name):
        # 尝试多种列名变体以提高兼容性
        if col_name in series.index:
            return series[col_name]
        alt = col_name.replace('(%)', '').strip()
        if alt in series.index:
            return series[alt]
        alt2 = alt + '(%)'
        if alt2 in series.index:
            return series[alt2]
        return ''

    def format_multi(val):
        if isinstance(val, str) and ('，' in val or ',' in val):
            parts = [x for x in val.replace('，', ',').split(',') if x]
            out = []
            for x in parts:
                if '%' in x:
                    try:
                        out.append(f"{float(x.replace('%','')):.2f}%")
                    except:
                        out.append(x)
                else:
                    try:
                        out.append(f"{float(x):.2f}")
                    except:
                        out.append(x)
            return '，'.join(out)
        try:
            if isinstance(val, str) and '%' in val:
                return f"{float(val.replace('%','')):.2f}%"
            return f"{float(val):.2f}"
        except:
            return val

    for _, row in result_df.iterrows():
        table_html += '<tr>'
        for col in cols:
            val = get_field(row, col)
            try:
                # 处理带%字符串
                if isinstance(val, str) and '%' in val:
                    num = float(val.replace('%', ''))
                    color = 'red' if num > 0 else ('blue' if num < 0 else 'black')
                    table_html += f'<td style="text-align: right; color: {color};">{num:.2f}%</td>'
                else:
                    num = float(val)
                    # 某些列始终为黑色
                    if col in ['总额', '总份', '总投入']:
                        color = 'black'
                    else:
                        color = 'red' if num > 0 else ('blue' if num < 0 else 'black')
                    # 日期特殊处理左对齐
                    if col == '日期':
                        table_html += f'<td style="text-align: left;">{val}</td>'
                    elif col == '净值':
                        table_html += f'<td style="text-align: right;">{num:.4f}</td>'
                    else:
                        table_html += f'<td style="text-align: right; color: {color};">{num:.2f}</td>'
            except Exception:
                # 特殊处理加额最新涨幅(%)，到手增额/增幅可能包含多值
                if col in ['加额最新涨幅(%)']:
                    raw = val
                    try:
                        v = float(str(raw).replace('%', ''))
                        color = 'red' if v != 0 else 'black'
                        table_html += f'<td style="text-align: right; color: {color};">{v:.2f}%</td>'
                    except:
                        table_html += f'<td style="text-align: right;">{raw}</td>'
                elif col in ['到手增额', '到手增幅']:
                    table_html += f'<td style="text-align: right;">{format_multi(val)}</td>'
                else:
                    table_html += f'<td style="text-align: right;">{val}</td>'
        table_html += '</tr>'

    table_html += '</tbody></table></div>'
    return table_html

def generate_mobile_chart(history_df):
    """生成移动端优化的图表"""
    if history_df is None or history_df.empty or 'date' not in history_df or 'net_value' not in history_df:
        return '<div class="text-center text-muted py-4">暂无净值数据</div>'
    
    # 日期格式转换
    history_df['date'] = pd.to_datetime(history_df['date'])
    today = datetime.now()
    one_month_ago = today - timedelta(days=30)
    recent_df = history_df[history_df['date'] >= one_month_ago].sort_values('date').copy()
    
    if recent_df.empty:
        return '<div class="text-center text-muted py-4">近一个月无数据</div>'
    
    # 移动端图表：简化显示
    recent_df['short_date'] = recent_df['date'].apply(lambda x: f"{x.month}.{x.day}")
    
    line = Line(init_opts=opts.InitOpts(width="100%", height="300px"))  # 降低高度
    line.add_xaxis(recent_df['short_date'].tolist())
    
    # 准备加额数据用于颜色映射
    additions = recent_df['addition'].round(4).tolist()
    additions_json = json.dumps(additions)
    
    line.add_yaxis(
        series_name="净值",
        y_axis=recent_df['net_value'].round(4).tolist(),
        is_smooth=True,
        symbol="circle",
        symbol_size=8,  # 减小符号大小
        label_opts=opts.LabelOpts(is_show=False),
        linestyle_opts=opts.LineStyleOpts(width=2, color="#1890ff"),
        itemstyle_opts=opts.ItemStyleOpts(
            color=JsCode(f"function(params) {{const additions = {additions_json};const value = additions[params.dataIndex];return value > 0 ? 'red' : value < 0 ? 'black' : 'blue';}}")
        )
    )
    
    line.set_global_opts(
        title_opts=opts.TitleOpts(title="净值趋势", pos_left="center", title_textstyle_opts=opts.TextStyleOpts(font_size=16)),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
        xaxis_opts=opts.AxisOpts(
            name="日期",
            axislabel_opts=opts.LabelOpts(rotate=30, font_size=10),
            interval=0
        ),
        yaxis_opts=opts.AxisOpts(
            name="净值",
            axislabel_opts=opts.LabelOpts(formatter=JsCode("function(value){return value.toFixed(4);}"), font_size=10),
            min_='dataMin',
            max_='dataMax'
        )
    )
    
    return line.render_embed()

@app.route('/delete_fund/<fund_id>', methods=['POST'])
def delete_fund(fund_id):
    # 执行删除
    success, msg = FundService.delete_fund(fund_id)
    # 如果删除成功且删除的是当前选中基金，自动切换到第一个基金
    if success and session.get('fund_id') == fund_id:
        remaining_funds = FundService.get_fund_list()
        if remaining_funds:
            session['fund_id'] = remaining_funds[0].fund_id
        else:
            # 如果所有基金都被删除，创建默认基金
            fund, _ = FundService.create_fund('默认基金')
            session['fund_id'] = fund.fund_id
    return redirect(url_for('index'))

if __name__ == '__main__':
    print(f"移动端基金分析系统启动中...")
    print(f"访问地址: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"手机访问: http://[您的电脑IP]:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
