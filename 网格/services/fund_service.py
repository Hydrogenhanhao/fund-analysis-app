from models.fund import Fund

class FundService:
    """基金管理服务"""
    @staticmethod
    def get_fund_list():
        """获取基金列表"""
        return Fund.get_all()

    @staticmethod
    def create_fund(fund_name):
        """创建基金（名称去重）"""
        if not fund_name or len(fund_name.strip()) == 0:
            return None, "基金名称不能为空"
        fund = Fund.create(fund_name.strip())
        if not fund:
            return None, "基金名称已存在"
        return fund, "创建成功"

    @staticmethod
    def update_fund_name(fund_id, new_name):
        """修改基金名称"""
        if not new_name or len(new_name.strip()) == 0:
            return False, "基金名称不能为空"
        fund = Fund.get_by_id(fund_id)
        if not fund:
            return False, "基金不存在"
        if fund.update_name(new_name.strip()):
            return True, "修改成功"
        return False, "名称已存在"

    @staticmethod
    def delete_fund(fund_id):
        """删除基金"""
        fund = Fund.get_by_id(fund_id)
        if not fund:
            return False, "基金不存在"
        if fund.delete():
            return True, "删除成功"
        return False, "删除失败"

    @staticmethod
    def get_fund_data(fund_id):
        """获取基金数据（含计算结果）"""
        fund = Fund.get_by_id(fund_id)
        if not fund:
            return None, "基金不存在"
        history_df = fund.get_history_data()
        return history_df, fund.fund_name