"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class GrantFundService(BaseModuleService):
    MODULE = "grant_fund"
    ENTITY = "经费申请"
    OPERATION_TERM = "拨付经费"
    LIST_FIELDS = ["申请项目", "资助来源", "获批金额", "使用期限", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["申请项目", "资助来源", "获批金额"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"拨付经费": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
