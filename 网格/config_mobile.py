# 移动端基金分析系统配置
# 数据库配置
DATABASE_PATH = 'fund_analysis_mobile.db'  # 移动端数据库

# Flask应用配置
FLASK_HOST = '0.0.0.0'  # 允许外部访问，方便手机连接
FLASK_PORT = 5001  # 使用不同端口避免冲突
FLASK_DEBUG = True

# 计算常量
DECIMAL_PRECISION = 4  # 数值精度（小数点后位数）

# 移动端特定配置
MOBILE_OPTIMIZED = True
TOUCH_FRIENDLY = True
RESPONSIVE_DESIGN = True
