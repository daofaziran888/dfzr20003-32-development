"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class DigitizationService(BaseModuleService):
    MODULE = "digitization"
    ENTITY = "数字资源"
    OPERATION_TERM = "入库资源"
    LIST_FIELDS = ["资源类型", "采集设备", "分辨率规格", "存储路径", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["资源类型", "采集设备", "分辨率规格"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已撤回"]
    ACTION_RULES = {"入库资源": "已确认", "提交确认": "待确认", "撤回记录": "已撤回"}
    NEGATIVE_ACTIONS = []
