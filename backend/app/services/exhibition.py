"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ExhibitionService(BaseModuleService):
    MODULE = "exhibition"
    ENTITY = "展览活动"
    OPERATION_TERM = "审批展览"
    LIST_FIELDS = ["展览主题", "展出地点", "展期起止", "参展作品数", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["展览主题", "展出地点", "展期起止"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"审批展览": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
