"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class WorkshopService(BaseModuleService):
    MODULE = "workshop"
    ENTITY = "传习所"
    OPERATION_TERM = "登记传习所"
    LIST_FIELDS = ["场所名称", "所在地区", "容纳人数", "开放周期", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["场所名称", "所在地区", "容纳人数"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"登记传习所": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
