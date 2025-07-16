# 网格计算器 - 实时基金分析系统

## 功能介绍
- 多基金管理：创建、切换和删除基金
- 数据录入：输入净值、加额和加份数据
- 实时计算：自动计算总额、总份、涨幅等关键指标
- 数据可视化：净值趋势图表展示
- 实时更新：数据提交后自动刷新页面

## 环境要求
- Python 3.7+ 
- 依赖库：详见 requirements.txt

## 安装步骤
1. 克隆或下载项目到本地
2. 安装依赖包：
   ```
   pip install -r requirements.txt
   ```

## 本地运行
1. 安装依赖包：
   ```
   pip install -r requirements.txt
   ```
2. 启动服务器：
   ```
   python APP.py
   ```
3. 在浏览器中访问：http://localhost:5000

## 在线部署（获取分享链接）
推荐使用Heroku平台部署，步骤如下：
1. 创建Heroku账号：https://signup.heroku.com
2. 安装Heroku CLI：https://devcenter.heroku.com/articles/heroku-cli
3. 登录Heroku：
   ```
   heroku login
   ```
4. 创建Heroku应用：
   ```
   heroku create
   ```
5. 部署代码：
   ```
   git init
   git add .
   git commit -m "Initial commit"
   git push heroku main
   ```
6. 打开在线应用：
   ```
   heroku open
   ```

部署成功后，您将获得一个类似 https://your-app-name.herokuapp.com 的可分享网址。

### 注意事项
- 免费账户可能有休眠时间限制
- WebSocket功能需要确保服务器支持异步worker
- 如遇部署问题，可查看日志：`heroku logs --tail`

## 使用说明
- 创建新基金：在顶部输入框填写基金名称并点击"创建"
- 切换基金：通过下拉菜单选择不同基金
- 录入数据：填写日期、净值和加额/加份数据并提交
- 查看结果：表格自动显示计算结果，图表展示近一个月净值趋势

## 注意事项
- 数据实时更新：提交新数据后所有打开页面会自动刷新
- 加额和加份只需填写一项，系统会自动计算另一项
- 负数加额表示赎回操作