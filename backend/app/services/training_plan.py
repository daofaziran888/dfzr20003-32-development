"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class TrainingPlanService(BaseModuleService):
    MODULE = "training_plan"
    ENTITY = "培训计划"
    OPERATION_TERM = "排定课程"
    LIST_FIELDS = ["课程名称", "授课师傅", "培训周期", "学员规模", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["课程名称", "授课师傅", "培训周期"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"排定课程": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
