"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class CraftCategoryService(BaseModuleService):
    MODULE = "craft_category"
    ENTITY = "技艺门类"
    OPERATION_TERM = "核定门类"
    LIST_FIELDS = ["门类名称", "所属级别", "申报批次", "保护单位", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["门类名称", "所属级别", "申报批次"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"核定门类": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
