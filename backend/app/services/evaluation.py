"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class EvaluationService(BaseModuleService):
    MODULE = "evaluation"
    ENTITY = "评估报告"
    OPERATION_TERM = "发布评估"
    LIST_FIELDS = ["评估对象", "评估周期", "评分结果", "评估机构", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["评估对象", "评估周期", "评分结果"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"发布评估": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
