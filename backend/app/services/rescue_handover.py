"""抢录交接域服务：濒危抢救与数字化采集之间的续采机制。

解决的问题：濒危抢救项目临时停工后，剩余采集任务无法凭交接号续办。

本模块提供：
- 交接任务：以抢救项目登记编号为交接号，绑定数字化采集任务与拍摄片段；
- 抢录交付进度的持久保存：每次交付事件都写入进度仓，停工/重新初始化不丢；
- 续采证据委托单：停工续办时签发，数字化采集凭单重新进入原交接任务；
- 原片保管记录：片段签收时登记，重新初始化只重建会话，不动保管记录；
- 幂等签收回执：同一拍摄段断网重提，最多收到一次已签收回执；
- 关停语义：项目关闭后不得在原编号下发布新片，关停前已交付片段仍可查核；
- 关闭与重投交错：片段在关停前已传输完成的，签收归属原传输，回执仍只发一次。

进度仓是进程内单例（与 app.store 同级的持久层，真实部署时替换为数据库）。
"""
from __future__ import annotations

from typing import Any

from app.store import store

# 交接任务状态
TASK_ACTIVE = "在办"
TASK_SUSPENDED = "已停工"
TASK_AWAIT_REENTRY = "待续采"
TASK_CLOSED = "已关闭"

# 片段状态
SEG_PENDING = "待采集"
SEG_TRANSMITTED = "传输完成"
SEG_SIGNED = "已签收"

# 委托单状态
SLIP_VALID = "有效"
SLIP_USED = "已用"
SLIP_VOID = "作废"


class _HandoverRepo:
    """抢录交付进度仓：交接任务、片段、回执、保管记录、委托单、进度快照。

    所有记录按交接号长期保存；重新初始化（凭单续采）只重建工作视图，
    已签收片段的回执与保管记录留在仓内不动。
    """

    def __init__(self) -> None:
        self.tasks: dict[str, dict[str, Any]] = {}
        self.segments: dict[str, dict[str, Any]] = {}
        self.receipts: dict[str, dict[str, Any]] = {}
        self.custody: dict[str, dict[str, Any]] = {}
        self.commissions: dict[str, dict[str, Any]] = {}
        self.progress: dict[str, dict[str, Any]] = {}
        self.tick = 0
        self.commission_seq = 0

    def next_tick(self) -> int:
        self.tick += 1
        return self.tick


_repo = _HandoverRepo()


def reset_handover_repo() -> None:
    """清空进度仓（测试隔离用）。"""
    global _repo
    _repo = _HandoverRepo()


# ── 内部工具 ─────────────────────────────────────────────────────

def _fail(message: str) -> dict[str, Any]:
    return {"ok": False, "message": message}


def _rescue_entry(rescue_id: int) -> dict[str, Any] | None:
    return store.find("emer_rescue", rescue_id)


def _handover_no_of(rescue: dict[str, Any]) -> str:
    """交接号沿用抢救项目登记编号，保证续办时按原编号找回任务。"""
    no = str(rescue.get("登记编号") or "").strip()
    return no or f"HD-{int(rescue.get('id', 0)):04d}"


def _segment_nos(task: dict[str, Any]) -> list[str]:
    return list(task.get("片段号列表", []))


def _segments_of(task: dict[str, Any]) -> list[dict[str, Any]]:
    return [_repo.segments[no] for no in _segment_nos(task) if no in _repo.segments]


def _persist_progress(task: dict[str, Any]) -> dict[str, Any]:
    """把当前交付进度写入进度仓（持久保存），停工与重进都以此为准。"""
    handover_no = task["交接号"]
    segments = _segments_of(task)
    delivered = [s["片段号"] for s in segments if s["状态"] == SEG_SIGNED]
    todo = [s["片段号"] for s in segments if s["状态"] != SEG_SIGNED]
    record = {
        "交接号": handover_no,
        "抢救项目ID": task["抢救项目ID"],
        "已交付片段": delivered,
        "待办片段": todo,
        "签收回执": {
            no: _repo.receipts[no]["回执号"] for no in delivered if no in _repo.receipts
        },
        "更新次序": _repo.next_tick(),
        "持久保存": True,
    }
    _repo.progress[handover_no] = record
    return record


def _issue_receipt(task: dict[str, Any], segment: dict[str, Any], attribution: str) -> dict[str, Any]:
    """签发回执并登记原片保管记录。每段最多一次，调用方需先判重。"""
    tick = _repo.next_tick()
    receipt_no = f"RC-{segment['片段号']}"
    receipt = {
        "回执号": receipt_no,
        "片段号": segment["片段号"],
        "交接号": task["交接号"],
        "签收次序": tick,
        "签收归属": attribution,
    }
    _repo.receipts[segment["片段号"]] = receipt
    segment["状态"] = SEG_SIGNED
    segment["签收次序"] = tick
    segment["回执号"] = receipt_no
    # 原片保管记录：签收即入账，之后任何重新初始化都不动这条记录
    _repo.custody[segment["片段号"]] = {
        "保管记录号": f"CU-{segment['片段号']}",
        "片段号": segment["片段号"],
        "交接号": task["交接号"],
        "登记次序": tick,
        "保管人": task.get("负责人", ""),
        "备注": "原片已签收，保管记录长期有效",
    }
    _persist_progress(task)
    return receipt


def _task_view(task: dict[str, Any]) -> dict[str, Any]:
    handover_no = task["交接号"]
    segments = _segments_of(task)
    progress = _repo.progress.get(handover_no, {})
    return {
        "交接号": handover_no,
        "抢救项目ID": task["抢救项目ID"],
        "采集任务ID": task["采集任务ID"],
        "状态": task["状态"],
        "当前证据编号": task.get("当前证据编号"),
        "后续使用范围": task.get("后续使用范围", ""),
        "片段列表": [dict(s) for s in segments],
        "待办片段": [s["片段号"] for s in segments if s["状态"] != SEG_SIGNED],
        "已交付片段": [s["片段号"] for s in segments if s["状态"] == SEG_SIGNED],
        "签收回执": [dict(_repo.receipts[no]) for no in _segment_nos(task) if no in _repo.receipts],
        "保管记录": [dict(_repo.custody[no]) for no in _segment_nos(task) if no in _repo.custody],
        "交付进度": dict(progress) if progress else None,
    }


# ── 开通交接任务 ──────────────────────────────────────────────────

def open_handover(
    rescue_id: int,
    digitization_id: int,
    segment_count: int = 1,
    usage_scope: str | None = None,
) -> dict[str, Any]:
    """为已启动的抢救项目开通交接任务，交接号即项目登记编号。"""
    rescue = _rescue_entry(rescue_id)
    if rescue is None:
        return _fail(f"抢救项目 {rescue_id} 不存在")
    if rescue.get("status") == "已关闭":
        return _fail(f"抢救项目 {rescue_id} 已关闭，不得在原编号下再开通交接任务")
    if rescue.get("status") != "已确认":
        return _fail("抢救项目尚未启动，不能开通交接任务")
    digitization = store.find("digitization", digitization_id)
    if digitization is None:
        return _fail(f"数字化采集任务 {digitization_id} 不存在")
    handover_no = _handover_no_of(rescue)
    existing = _repo.tasks.get(handover_no)
    if existing is not None:
        if existing["状态"] == TASK_CLOSED:
            return _fail(f"交接号 {handover_no} 已关停，不得在原编号下发布新片")
        return _fail(f"交接号 {handover_no} 的交接任务已存在")
    if segment_count < 1:
        return _fail("交接任务至少包含一段拍摄片段")
    task = {
        "交接号": handover_no,
        "抢救项目ID": rescue_id,
        "采集任务ID": digitization_id,
        "状态": TASK_ACTIVE,
        "负责人": rescue.get("负责人", ""),
        "后续使用范围": (usage_scope or "").strip() or str(rescue.get("抢救方案") or ""),
        "当前证据编号": None,
        "关闭次序": None,
        "片段号列表": [],
    }
    for index in range(1, segment_count + 1):
        segment_no = f"{handover_no}-S{index}"
        _repo.segments[segment_no] = {
            "片段号": segment_no,
            "交接号": handover_no,
            "序号": index,
            "状态": SEG_PENDING,
            "传完次序": None,
            "签收次序": None,
            "回执号": None,
        }
        task["片段号列表"].append(segment_no)
    _repo.tasks[handover_no] = task
    _persist_progress(task)
    return {
        "ok": True,
        "message": f"交接任务 {handover_no} 已开通，共 {segment_count} 段待采集",
        "task": _task_view(task),
    }


# ── 片段传输与签收 ────────────────────────────────────────────────

def _load_task(handover_no: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    task = _repo.tasks.get(handover_no)
    if task is None:
        return None, _fail(f"交接号 {handover_no} 不存在或已归档")
    return task, None


def _load_segment(task: dict[str, Any], segment_no: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    segment = _repo.segments.get(segment_no)
    if segment is None or segment.get("交接号") != task["交接号"]:
        return None, _fail(f"片段 {segment_no} 不属于交接号 {task['交接号']}")
    return segment, None


def transmit_segment(handover_no: str, segment_no: str) -> dict[str, Any]:
    """登记片段传输完成。断网重传不覆盖首次传完时间。"""
    task, error = _load_task(handover_no)
    if error:
        return error
    segment, error = _load_segment(task, segment_no)
    if error:
        return error
    if task["状态"] == TASK_CLOSED:
        return _fail(f"交接号 {handover_no} 已关停，不得在原编号下发布新片")
    if task["状态"] == TASK_SUSPENDED:
        return _fail("抢救项目已临时停工，请先办理续办再传输片段")
    if task["状态"] == TASK_AWAIT_REENTRY:
        return _fail("续采证据委托单已签发，请凭单重新进入原交接任务后再传输")
    if segment["状态"] == SEG_PENDING:
        segment["状态"] = SEG_TRANSMITTED
        segment["传完次序"] = _repo.next_tick()
        _persist_progress(task)
        return {"ok": True, "message": f"片段 {segment_no} 传输完成", "segment": dict(segment)}
    return {"ok": True, "message": f"片段 {segment_no} 此前已传输，重传不覆盖原记录", "segment": dict(segment)}


def sign_segment(handover_no: str, segment_no: str) -> dict[str, Any]:
    """签发签收回执：同一拍摄段最多一次；关停前已传完的片段归属原传输。"""
    task, error = _load_task(handover_no)
    if error:
        return error
    segment, error = _load_segment(task, segment_no)
    if error:
        return error
    if segment["状态"] == SEG_SIGNED:
        receipt = _repo.receipts[segment_no]
        return {
            "ok": True,
            "message": f"片段 {segment_no} 已签收，重提不再重复发回执",
            "receipt": dict(receipt),
            "segment": dict(segment),
        }
    if segment["状态"] != SEG_TRANSMITTED:
        return _fail(f"片段 {segment_no} 尚未传输完成，不能签收")
    if task["状态"] == TASK_CLOSED:
        closed_tick = task.get("关闭次序") or 0
        transmitted_tick = segment.get("传完次序") or 0
        if transmitted_tick and transmitted_tick < closed_tick:
            receipt = _issue_receipt(task, segment, "关停前已传输，签收归属原传输")
            return {
                "ok": True,
                "message": f"片段 {segment_no} 在关停前已传输完成，签收归属原传输",
                "receipt": dict(receipt),
                "segment": dict(segment),
            }
        return _fail(f"交接号 {handover_no} 已关停，不得在原编号下发布新片")
    if task["状态"] == TASK_SUSPENDED:
        return _fail("抢救项目已临时停工，请先办理续办再签收")
    if task["状态"] == TASK_AWAIT_REENTRY:
        return _fail("请凭续采证据委托单重新进入原交接任务后再签收")
    receipt = _issue_receipt(task, segment, "在办签收")
    return {
        "ok": True,
        "message": f"片段 {segment_no} 已签收，回执 {receipt['回执号']}",
        "receipt": dict(receipt),
        "segment": dict(segment),
    }


def submit_segment(handover_no: str, segment_no: str) -> dict[str, Any]:
    """采集员提交片段（传输+签收）。断网重提、按旧号重发都幂等。"""
    task, error = _load_task(handover_no)
    if error:
        return error
    segment, error = _load_segment(task, segment_no)
    if error:
        return error
    if segment["状态"] == SEG_SIGNED:
        receipt = _repo.receipts[segment_no]
        return {
            "ok": True,
            "message": f"片段 {segment_no} 已签收，本次重提不重复发回执",
            "receipt": dict(receipt),
            "segment": dict(segment),
        }
    if segment["状态"] == SEG_TRANSMITTED:
        return sign_segment(handover_no, segment_no)
    transmitted = transmit_segment(handover_no, segment_no)
    if not transmitted["ok"]:
        return transmitted
    return sign_segment(handover_no, segment_no)


# ── 临时停工与续办 ────────────────────────────────────────────────

def suspend_by_rescue(rescue_id: int) -> dict[str, Any]:
    """临时停工：把交付进度持久保存，任务进入已停工。"""
    rescue = _rescue_entry(rescue_id)
    if rescue is None:
        return _fail(f"抢救项目 {rescue_id} 不存在")
    handover_no = _handover_no_of(rescue)
    task = _repo.tasks.get(handover_no)
    if task is None:
        return {"ok": True, "message": "抢救项目尚未开通交接任务，无需停工", "task": None}
    if task["状态"] == TASK_CLOSED:
        return _fail(f"交接号 {handover_no} 已关停，不能再停工")
    task["状态"] = TASK_SUSPENDED
    progress = _persist_progress(task)
    return {
        "ok": True,
        "message": f"交接任务 {handover_no} 已停工，交付进度已持久保存",
        "task": _task_view(task),
        "progress": progress,
    }


def issue_commission(rescue_id: int) -> dict[str, Any]:
    """停工续办：签发续采证据委托单，数字化采集凭单续采剩余任务。"""
    rescue = _rescue_entry(rescue_id)
    if rescue is None:
        return _fail(f"抢救项目 {rescue_id} 不存在")
    if rescue.get("status") != "已停工":
        return _fail("抢救项目未处于临时停工状态，不能签发续采证据委托单")
    handover_no = _handover_no_of(rescue)
    task = _repo.tasks.get(handover_no)
    if task is None:
        return _fail(f"交接号 {handover_no} 尚未开通交接任务")
    if task["状态"] != TASK_SUSPENDED:
        return _fail(f"交接任务 {handover_no} 当前状态为 {task['状态']}，不能续办")
    _repo.commission_seq += 1
    seq = _repo.commission_seq
    commission_no = f"CM-{handover_no}-{seq}"
    evidence_no = f"EV-{handover_no}-{seq:04d}"
    todo = [s["片段号"] for s in _segments_of(task) if s["状态"] != SEG_SIGNED]
    slip = {
        "委托单号": commission_no,
        "证据编号": evidence_no,
        "交接号": handover_no,
        "抢救项目ID": rescue_id,
        "采集任务ID": task["采集任务ID"],
        "状态": SLIP_VALID,
        "签发次序": _repo.next_tick(),
        "待办片段": todo,
    }
    _repo.commissions[commission_no] = slip
    task["状态"] = TASK_AWAIT_REENTRY
    rescue["status"] = "已确认"
    rescue["pending"] = True
    return {
        "ok": True,
        "message": f"已签发续采证据委托单 {commission_no}，证据编号 {evidence_no}",
        "commission": dict(slip),
        "task": _task_view(task),
    }


def reenter_handover(handover_no: str, commission_no: str) -> dict[str, Any]:
    """凭续采证据委托单重新进入原交接任务，按委托续采。

    重新初始化只恢复工作视图：待办片段与签收回执从持久进度同步，
    已签收原片的保管记录留在仓内不动。
    """
    task, error = _load_task(handover_no)
    if error:
        return error
    if task["状态"] == TASK_CLOSED:
        return _fail(f"交接号 {handover_no} 已关停，不能重新进入")
    if task["状态"] != TASK_AWAIT_REENTRY:
        return _fail(f"交接任务 {handover_no} 当前状态为 {task['状态']}，无需凭单重进")
    slip = _repo.commissions.get(commission_no)
    if slip is None or slip.get("交接号") != handover_no:
        return _fail(f"续采证据委托单 {commission_no} 与交接号 {handover_no} 不匹配")
    if slip["状态"] == SLIP_VOID:
        return _fail(f"续采证据委托单 {commission_no} 已作废")
    if slip["状态"] == SLIP_USED:
        return _fail(f"续采证据委托单 {commission_no} 已使用，不能重复进入")
    slip["状态"] = SLIP_USED
    task["状态"] = TASK_ACTIVE
    task["当前证据编号"] = slip["证据编号"]
    progress = _persist_progress(task)
    view = _task_view(task)
    return {
        "ok": True,
        "message": f"已凭委托单 {commission_no} 重新进入交接任务 {handover_no}，按委托续采",
        "task": view,
        "commission": dict(slip),
        "progress": progress,
        "待办片段": view["待办片段"],
        "签收回执": view["签收回执"],
        "证据编号": slip["证据编号"],
    }


# ── 关闭项目 ─────────────────────────────────────────────────────

def close_by_rescue(rescue_id: int) -> dict[str, Any]:
    """关闭项目：任务关停、有效委托单作废；已交付片段与回执保留可查。"""
    rescue = _rescue_entry(rescue_id)
    if rescue is None:
        return _fail(f"抢救项目 {rescue_id} 不存在")
    handover_no = _handover_no_of(rescue)
    task = _repo.tasks.get(handover_no)
    if task is None:
        return {"ok": True, "message": "抢救项目未开通交接任务，直接关闭", "task": None}
    if task["状态"] == TASK_CLOSED:
        return _fail(f"交接号 {handover_no} 已是关停状态")
    task["状态"] = TASK_CLOSED
    task["关闭次序"] = _repo.next_tick()
    for slip in _repo.commissions.values():
        if slip.get("交接号") == handover_no and slip["状态"] == SLIP_VALID:
            slip["状态"] = SLIP_VOID
    progress = _persist_progress(task)
    return {
        "ok": True,
        "message": f"交接任务 {handover_no} 已关停，已交付片段仍可查核",
        "task": _task_view(task),
        "progress": progress,
    }


# ── 查核 ─────────────────────────────────────────────────────────

def get_handover(handover_no: str) -> dict[str, Any]:
    """查看交接任务全貌；关停后仍可查核关停前已交付的片段。"""
    task, error = _load_task(handover_no)
    if error:
        return error
    return {"ok": True, "task": _task_view(task)}


def get_progress(handover_no: str) -> dict[str, Any]:
    """读取持久保存的抢录交付进度。"""
    task, error = _load_task(handover_no)
    if error:
        return error
    progress = _repo.progress.get(handover_no)
    if progress is None:
        return _fail(f"交接号 {handover_no} 暂无交付进度")
    return {"ok": True, "progress": dict(progress)}


def get_usage_scope(handover_no: str) -> dict[str, Any]:
    """核对抢救计划已获准的后续使用范围（关停后仍可核对）。"""
    task, error = _load_task(handover_no)
    if error:
        return error
    rescue = _rescue_entry(task["抢救项目ID"]) or {}
    return {
        "ok": True,
        "交接号": handover_no,
        "后续使用范围": task.get("后续使用范围", ""),
        "抢救方案": rescue.get("抢救方案", ""),
        "项目状态": rescue.get("status", ""),
    }


def list_tasks() -> dict[str, Any]:
    """列出全部交接任务（工作台面板用）。"""
    return {
        "ok": True,
        "tasks": [_task_view(task) for task in _repo.tasks.values()],
    }
