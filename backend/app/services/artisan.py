"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ArtisanService(BaseModuleService):
    MODULE = "artisan"
    ENTITY = "传承人"
    OPERATION_TERM = "认定传承人"
    LIST_FIELDS = ["姓名", "技艺方向", "传承谱系", "评定等级", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["姓名", "技艺方向", "传承谱系"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"认定传承人": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
