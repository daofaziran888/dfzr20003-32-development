"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class EmerRescueService(BaseModuleService):
    MODULE = "emer_rescue"
    ENTITY = "抢救项目"
    OPERATION_TERM = "启动抢救"
    LIST_FIELDS = ["濒危等级", "抢救方案", "实施团队", "抢救周期", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["濒危等级", "抢救方案", "实施团队"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"启动抢救": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
