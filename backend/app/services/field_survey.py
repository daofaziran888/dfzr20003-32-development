"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class FieldSurveyService(BaseModuleService):
    MODULE = "field_survey"
    ENTITY = "调查记录"
    OPERATION_TERM = "归档调查"
    LIST_FIELDS = ["调查地点", "调查日期", "访谈对象", "采集素材", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["调查地点", "调查日期", "访谈对象"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"归档调查": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
