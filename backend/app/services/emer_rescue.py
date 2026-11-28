"""濒危抢救领域服务：在通用骨架上扩展临时停工、续办与关闭项目。

临时停工会把抢录交付进度持久保存；关闭项目后原编号不得再发新片，
关停前已交付的片段仍可查核。续办通过签发续采证据委托单完成，
见 app.services.rescue_handover。
"""
from __future__ import annotations

from typing import Any

from app.services import rescue_handover
from app.services.base import BaseModuleService
from app.store import store


class EmerRescueService(BaseModuleService):
    MODULE = "emer_rescue"
    ENTITY = "抢救项目"
    OPERATION_TERM = "启动抢救"
    LIST_FIELDS = ["濒危等级", "抢救方案", "实施团队", "抢救周期", "登记编号", "负责人", "生效版本", "备注说明"]
    REQUIRED_FIELDS = ["濒危等级", "抢救方案", "实施团队"]
    STATUS_ORDER = ["草稿", "待确认", "已确认", "已停工", "已关闭", "已撤回"]
    ACTION_RULES = {
        "启动抢救": "已确认",
        "提交确认": "待确认",
        "临时停工": "已停工",
        "关闭项目": "已关闭",
        "撤回记录": "已撤回",
    }
    NEGATIVE_ACTIONS = []
    TERMINAL_STATUSES = ("已关闭", "已撤回")

    def run_action(self, entry_id: int, action: str) -> tuple[dict[str, Any] | None, str]:
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return None, f"{self.ENTITY} {entry_id} 不存在或已归档"
        target = self.ACTION_RULES.get(action)
        if target is None:
            return None, f"动作「{action}」不属于{self.MODULE}可执行范围"
        current = str(entry.get("status", ""))
        if current == "已关闭":
            return None, f"{self.ENTITY} {entry_id} 已关闭，不得在原编号下再执行任何操作"
        if action == "临时停工" and current != "已确认":
            return None, "只有已启动的抢救项目才能临时停工"
        if action == "关闭项目" and current not in ("已确认", "已停工"):
            return None, "只有已启动或已停工的抢救项目才能关闭"
        if action == "临时停工":
            result = rescue_handover.suspend_by_rescue(entry_id)
            if not result["ok"]:
                return None, result["message"]
        elif action == "关闭项目":
            result = rescue_handover.close_by_rescue(entry_id)
            if not result["ok"]:
                return None, result["message"]
        entry["status"] = target
        entry["pending"] = target not in self.TERMINAL_STATUSES
        entry["abnormal"] = action in self.NEGATIVE_ACTIONS
        return entry, f"{self.ENTITY}已{action}"
