"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class RawMaterialService(BaseModuleService):
    MODULE = "raw_material"
    ENTITY = "原料批次"
    OPERATION_TERM = "验收原料"
    LIST_FIELDS = ["原料名称", "产地来源", "采购日期", "质检等级", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["原料名称", "产地来源", "采购日期"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"验收原料": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
