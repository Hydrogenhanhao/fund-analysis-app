from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import json
from services.fund_service import FundService
from services.calculator import InvestmentCalculator
from models.fund import Fund
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, DECIMAL_PRECISION
from pyecharts.charts import Line
from pyecharts import options as opts
from datetime import datetime, timedelta
from pyecharts.commons.utils import JsCode

# 初始化应用
app = Flask(__name__)
app.secret_key = 'fund_analysis_system'


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

    # 生成表格HTML
    table_html = ""
    if not result_df.empty:
        # 确保列名完整
        result_df = result_df.rename(columns={
            '净值涨幅(%)': '净值涨幅(%)',
            '总涨幅(%)': '总涨幅(%)',
            '加额最新涨幅(%)': '加额最新涨幅(%)',
            '到手增额': '到手增额',
            '到手增幅': '到手增幅'
        })

        # 生成表格时强制设置列宽和表头样式
        table_html = '''
        <div class="table-responsive" style="overflow-x: auto; margin-top: 20px;">
            <table class="table table-striped table-hover" style="min-width: 1300px; table-layout: fixed;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="width: 100px; text-align: center; vertical-align: middle;">日期</th>
                        <th style="width: 80px; text-align: center; vertical-align: middle;">净值</th>
                        <th style="width: 80px; text-align: center; vertical-align: middle;">加额</th>
                        <th style="width: 80px; text-align: center; vertical-align: middle;">加份</th>
                        <th style="width: 100px; text-align: center; vertical-align: middle;">总额</th>
                        <th style="width: 80px; text-align: center; vertical-align: middle;">总份</th>
                        <th style="width: 100px; text-align: center; vertical-align: middle;">净值涨幅(%)</th>
                        <th style="width: 80px; text-align: center; vertical-align: middle;">总投入</th>
                        <th style="width: 80px; text-align: center; vertical-align: middle;">总涨幅(%)</th>
                        <th style="width: 120px; text-align: center; vertical-align: middle;">加额最新涨幅(%)</th>
                        <th style="width: 120px; text-align: center; vertical-align: middle;">到手增额</th>
                        <th style="width: 120px; text-align: center; vertical-align: middle;">到手增幅</th>
                    </tr>
                </thead>
                <tbody>
        '''
        # 添加数据行
        for _, row in result_df.iterrows():
            table_html += '<tr>'
            # 日期列
            table_html += f'<td style="text-align: left;">{row["日期"]}</td>'
            # 净值保留四位小数
            table_html += f'<td style="text-align: right;">{float(row["净值"]):.4f}</td>'
            # 其余数值保留两位小数
            for col in ['加额', '加份', '总额', '总份', '净值涨幅(%)', '总投入', '总涨幅(%)']:
                try:
                    v = row[col]
                    # 先处理数值转换
                    if isinstance(v, str) and '%' in v:
                        val = float(v.replace('%', ''))
                    else:
                        val = float(v)
                    # 总额、总份、总投入恒为黑色
                    if col in ['总额', '总份', '总投入']:
                        color = 'black'
                    else:
                        color = 'red' if val > 0 else ('blue' if val < 0 else 'black')
                    if '%' in str(v):
                        table_html += f'<td style="text-align: right; color: {color};">{val:.2f}%</td>'
                    else:
                        table_html += f'<td style="text-align: right; color: {color};">{val:.2f}</td>'
                except:
                    table_html += f'<td style="text-align: right;">{row[col]}</td>'
            # 加额最新涨幅
            try:
                val = float(row['加额最新涨幅(%)'].replace('%', ''))
            except:
                val = 0
            color = 'red' if val != 0 else 'black'
            table_html += f'<td style="text-align: right; color: {color};">{val:.2f}%</td>'
            # 到手增额和增幅
            def format_multi(val):
                if isinstance(val, str) and ('，' in val or ',' in val):
                    return '，'.join([
                        f"{float(x.replace('%','')):.2f}%" if '%' in x else f"{float(x):.2f}"
                        for x in val.replace('，', ',').split(',') if x
                    ])
                try:
                    if isinstance(val, str) and '%' in val:
                        return f"{float(val.replace('%','')):.2f}%"
                    return f"{float(val):.2f}"
                except:
                    return val
            table_html += f'<td style="text-align: right;">{format_multi(row["到手增额"])}</td>'
            table_html += f'<td style="text-align: right;">{format_multi(row["到手增幅"])}</td>'
            table_html += '</tr>'
        table_html += '</tbody></table></div>'
    else:
        table_html = '<p class="text-muted text-center py-3">暂无数据，请添加记录</p>'

    chart_html = generate_net_value_chart(history_df)

    return render_template(
        'index.html',
        funds=funds,
        current_fund_id=current_fund_id,
        current_fund_name=fund_name,
        table_html=table_html,
        chart_html=chart_html
    )

def generate_net_value_chart(history_df):
    """生成最近一个月的日期-净值折线图"""
    if history_df is None or history_df.empty or 'date' not in history_df or 'net_value' not in history_df:
        return '<div class="text-center text-muted py-5">暂无净值数据</div>'
    # 日期格式转换
    history_df['date'] = pd.to_datetime(history_df['date'])
    today = datetime.now()
    one_month_ago = today - timedelta(days=30)
    recent_df = history_df[history_df['date'] >= one_month_ago].sort_values('date').copy()
    if recent_df.empty:
        return '<div class="text-center text-muted py-5">近一个月无数据</div>'
    # 横坐标格式如 7.1
    recent_df['short_date'] = recent_df['date'].apply(lambda x: f"{x.month}.{x.day}")
    line = Line(init_opts=opts.InitOpts(width="100%", height="400px"))
    line.add_xaxis(recent_df['short_date'].tolist())
    # 准备加额数据用于颜色映射
    additions = recent_df['addition'].round(4).tolist()
    additions_json = json.dumps(additions)
    line.add_yaxis(
        series_name="净值",
        y_axis=recent_df['net_value'].round(4).tolist(),
        is_smooth=True,
        symbol="circle",
        symbol_size=10,
        label_opts=opts.LabelOpts(is_show=False),
        linestyle_opts=opts.LineStyleOpts(width=3, color="#1890ff"),
        itemstyle_opts=opts.ItemStyleOpts(color=JsCode(f"function(params) {{const additions = {additions_json};const value = additions[params.dataIndex];return value > 0 ? 'red' : value < 0 ? 'black' : 'blue';}}"))
    )
    line.set_global_opts(
        title_opts=opts.TitleOpts(title="近一个月净值趋势", pos_left="center"),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
        xaxis_opts=opts.AxisOpts(
            name="日期",
            axislabel_opts=opts.LabelOpts(rotate=30),
            interval=0
        ),
        yaxis_opts=opts.AxisOpts(
            name="净值",
            axislabel_opts=opts.LabelOpts(formatter=JsCode("function(value){return value.toFixed(4);}")),
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
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)