"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class AuthenticationService(BaseModuleService):
    MODULE = "authentication"
    ENTITY = "认证"
    OPERATION_TERM = "签发认证"
    LIST_FIELDS = ["认证类型", "评审专家", "认证日期", "有效期限", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["认证类型", "评审专家", "认证日期"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"签发认证": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
