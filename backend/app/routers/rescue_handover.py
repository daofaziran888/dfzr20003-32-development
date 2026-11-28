"""抢录交接路由：交接任务开通、续采证据委托单、片段传输签收与查核。

路径固定前缀 /api/rescue-handover，必须注册在 /api/{module} 动态路由之前。
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import rescue_handover

router = APIRouter(prefix="/api/rescue-handover", tags=["抢录交接"])


class OpenPayload(BaseModel):
    rescue_id: int
    digitization_id: int
    segment_count: int = Field(default=1, ge=1)
    usage_scope: str | None = None


class CommissionPayload(BaseModel):
    rescue_id: int


class ReenterPayload(BaseModel):
    commission_no: str


class SegmentPayload(BaseModel):
    segment_no: str


def _result(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("ok"):
        raise HTTPException(status_code=400, detail=payload.get("message", "操作失败"))
    return payload


@router.get("/tasks")
def list_tasks() -> dict[str, Any]:
    """列出全部交接任务。"""
    return rescue_handover.list_tasks()


@router.post("/open")
def open_handover(payload: OpenPayload) -> dict[str, Any]:
    """为已启动的抢救项目开通交接任务（交接号=项目登记编号）。"""
    return _result(rescue_handover.open_handover(
        rescue_id=payload.rescue_id,
        digitization_id=payload.digitization_id,
        segment_count=payload.segment_count,
        usage_scope=payload.usage_scope,
    ))


@router.get("/{handover_no}")
def get_handover(handover_no: str) -> dict[str, Any]:
    """查看交接任务全貌；关停后仍可查核关停前已交付的片段。"""
    result = rescue_handover.get_handover(handover_no)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("message", "交接任务不存在"))
    return result


@router.get("/{handover_no}/progress")
def get_progress(handover_no: str) -> dict[str, Any]:
    """读取持久保存的抢录交付进度。"""
    result = rescue_handover.get_progress(handover_no)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("message", "暂无交付进度"))
    return result


@router.get("/{handover_no}/usage-scope")
def get_usage_scope(handover_no: str) -> dict[str, Any]:
    """核对抢救计划已获准的后续使用范围。"""
    return _result(rescue_handover.get_usage_scope(handover_no))


@router.post("/{handover_no}/commission")
def issue_commission(handover_no: str, payload: CommissionPayload) -> dict[str, Any]:
    """停工续办：签发续采证据委托单。"""
    result = rescue_handover.issue_commission(payload.rescue_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("message", "签发失败"))
    return result


@router.post("/{handover_no}/reenter")
def reenter_handover(handover_no: str, payload: ReenterPayload) -> dict[str, Any]:
    """凭续采证据委托单重新进入原交接任务，按委托续采。"""
    return _result(rescue_handover.reenter_handover(handover_no, payload.commission_no.strip()))


@router.post("/{handover_no}/segments/transmit")
def transmit_segment(handover_no: str, payload: SegmentPayload) -> dict[str, Any]:
    """登记片段传输完成。"""
    return _result(rescue_handover.transmit_segment(handover_no, payload.segment_no.strip()))


@router.post("/{handover_no}/segments/sign")
def sign_segment(handover_no: str, payload: SegmentPayload) -> dict[str, Any]:
    """签发签收回执（幂等，同段最多一次）。"""
    return _result(rescue_handover.sign_segment(handover_no, payload.segment_no.strip()))


@router.post("/{handover_no}/segments/submit")
def submit_segment(handover_no: str, payload: SegmentPayload) -> dict[str, Any]:
    """采集员提交片段；断网重提、按旧号重发均幂等。"""
    return _result(rescue_handover.submit_segment(handover_no, payload.segment_no.strip()))
