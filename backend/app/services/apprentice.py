"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ApprenticeService(BaseModuleService):
    MODULE = "apprentice"
    ENTITY = "学徒"
    OPERATION_TERM = "招收学徒"
    LIST_FIELDS = ["学徒姓名", "拜师日期", "学习阶段", "考核成绩", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["学徒姓名", "拜师日期", "学习阶段"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"招收学徒": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
