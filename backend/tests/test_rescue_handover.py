"""抢录交接续采机制测试：临时停工续办、幂等回执、关闭项目与重投冲突。

覆盖需求：
1. 临时停工后凭交接号续办剩余采集任务；
2. 抢录交付进度持久保存，续办时签发续采证据委托单；
3. 已签收原片在续采重新初始化时不丢保管记录；
4. 凭委托单重新进入原交接任务，同步待办片段与签收回执；
5. 同一拍摄段断网重提最多收到一次已签收回执；
6. 关闭项目后不得在原编号下发布新片，已交付片段仍可查核；
7. 关闭与重投交错时，末段签收归属关停前的原传输；
8. 重进采集页确认证据编号、核对已获准后续使用范围、按旧号重发已签收段。
"""
from __future__ import annotations

import pytest

from app.services import rescue_handover, service_for
from app.store import store


@pytest.fixture(autouse=True)
def clean_handover_repo():
    rescue_handover.reset_handover_repo()
    yield
    rescue_handover.reset_handover_repo()


def _new_rescue() -> dict:
    service = service_for("emer_rescue")
    entry, missing = service.create_entry({
        "濒危等级": "极高",
        "抢救方案": "抢救性抢录，成果仅限学术研究与档案保存使用",
        "实施团队": "抢救一组",
        "抢救周期": "2026-12",
    })
    assert not missing
    entry["登记编号"] = f"EMER-T{int(entry['id']):04d}"
    return entry


def _new_digitization() -> dict:
    service = service_for("digitization")
    entry, missing = service.create_entry({
        "资源类型": "视频",
        "采集设备": "4K摄像机",
        "分辨率规格": "3840x2160",
    })
    assert not missing
    return entry


def _running_project(segment_count: int = 2, usage_scope: str | None = None):
    """登记并启动一个抢救项目，开通交接任务，返回 (rescue, handover_no)。"""
    rescue = _new_rescue()
    digitization = _new_digitization()
    service = service_for("emer_rescue")
    entry, message = service.run_action(int(rescue["id"]), "启动抢救")
    assert entry is not None, message
    opened = rescue_handover.open_handover(
        rescue_id=int(rescue["id"]),
        digitization_id=int(digitization["id"]),
        segment_count=segment_count,
        usage_scope=usage_scope,
    )
    assert opened["ok"], opened["message"]
    return entry, opened["task"]["交接号"]


class TestOpenHandover:
    """开通交接任务：交接号沿用项目登记编号。"""

    def test_open_requires_started_rescue(self):
        rescue = _new_rescue()
        digitization = _new_digitization()
        result = rescue_handover.open_handover(int(rescue["id"]), int(digitization["id"]), 2)
        assert result["ok"] is False
        assert "尚未启动" in result["message"]

    def test_open_creates_segments_and_progress(self):
        rescue, handover_no = _running_project(segment_count=2)
        assert handover_no == rescue["登记编号"]
        view = rescue_handover.get_handover(handover_no)
        assert view["ok"] is True
        task = view["task"]
        assert task["状态"] == "在办"
        assert task["待办片段"] == [f"{handover_no}-S1", f"{handover_no}-S2"]
        assert task["交付进度"]["持久保存"] is True
        assert task["后续使用范围"] == rescue["抢救方案"]

    def test_open_duplicate_rejected(self):
        rescue, handover_no = _running_project(segment_count=1)
        again = rescue_handover.open_handover(int(rescue["id"]), 1, 1)
        assert again["ok"] is False
        assert "已存在" in again["message"]

    def test_open_with_missing_digitization(self):
        rescue = _new_rescue()
        service_for("emer_rescue").run_action(int(rescue["id"]), "启动抢救")
        result = rescue_handover.open_handover(int(rescue["id"]), 999, 1)
        assert result["ok"] is False
        assert "不存在" in result["message"]


class TestSegmentReceiptIdempotency:
    """同一拍摄段断网重提，最多收到一次已签收回执。"""

    def test_submit_issues_receipt_and_custody(self):
        _, handover_no = _running_project(segment_count=2)
        segment_no = f"{handover_no}-S1"
        result = rescue_handover.submit_segment(handover_no, segment_no)
        assert result["ok"] is True
        assert result["receipt"]["回执号"] == f"RC-{segment_no}"
        view = rescue_handover.get_handover(handover_no)["task"]
        assert view["已交付片段"] == [segment_no]
        assert view["保管记录"][0]["保管记录号"] == f"CU-{segment_no}"

    def test_resubmit_after_network_drop_single_receipt(self):
        _, handover_no = _running_project(segment_count=1)
        segment_no = f"{handover_no}-S1"
        first = rescue_handover.submit_segment(handover_no, segment_no)
        # 断网重提同一拍摄段
        second = rescue_handover.submit_segment(handover_no, segment_no)
        assert second["ok"] is True
        assert second["receipt"]["回执号"] == first["receipt"]["回执号"]
        view = rescue_handover.get_handover(handover_no)["task"]
        assert len(view["签收回执"]) == 1
        assert len(view["保管记录"]) == 1

    def test_transmit_then_sign_then_resign(self):
        _, handover_no = _running_project(segment_count=1)
        segment_no = f"{handover_no}-S1"
        transmitted = rescue_handover.transmit_segment(handover_no, segment_no)
        assert transmitted["ok"] is True
        signed = rescue_handover.sign_segment(handover_no, segment_no)
        assert signed["ok"] is True
        resigned = rescue_handover.sign_segment(handover_no, segment_no)
        assert resigned["receipt"]["回执号"] == signed["receipt"]["回执号"]
        view = rescue_handover.get_handover(handover_no)["task"]
        assert len(view["签收回执"]) == 1

    def test_sign_before_transmit_rejected(self):
        _, handover_no = _running_project(segment_count=1)
        result = rescue_handover.sign_segment(handover_no, f"{handover_no}-S1")
        assert result["ok"] is False
        assert "尚未传输完成" in result["message"]


class TestSuspendAndResume:
    """临时停工 → 进度持久保存 → 签发委托单 → 凭单重进续采。"""

    def test_suspend_persists_progress(self):
        rescue, handover_no = _running_project(segment_count=2)
        rescue_handover.submit_segment(handover_no, f"{handover_no}-S1")
        entry, message = service_for("emer_rescue").run_action(int(rescue["id"]), "临时停工")
        assert entry is not None, message
        assert entry["status"] == "已停工"
        task = rescue_handover.get_handover(handover_no)["task"]
        assert task["状态"] == "已停工"
        progress = rescue_handover.get_progress(handover_no)["progress"]
        assert progress["已交付片段"] == [f"{handover_no}-S1"]
        assert progress["待办片段"] == [f"{handover_no}-S2"]
        assert progress["持久保存"] is True

    def test_submit_rejected_while_suspended(self):
        rescue, handover_no = _running_project(segment_count=1)
        service_for("emer_rescue").run_action(int(rescue["id"]), "临时停工")
        result = rescue_handover.submit_segment(handover_no, f"{handover_no}-S1")
        assert result["ok"] is False
        assert "停工" in result["message"]

    def test_suspend_requires_started_project(self):
        rescue = _new_rescue()
        entry, message = service_for("emer_rescue").run_action(int(rescue["id"]), "临时停工")
        assert entry is None
        assert "已启动" in message

    def test_commission_and_reentry_resume_collection(self):
        rescue, handover_no = _running_project(segment_count=2)
        first = rescue_handover.submit_segment(handover_no, f"{handover_no}-S1")
        custody_before = dict(rescue_handover.get_handover(handover_no)["task"]["保管记录"][0])
        service_for("emer_rescue").run_action(int(rescue["id"]), "临时停工")

        # 续办：签发续采证据委托单
        issued = rescue_handover.issue_commission(int(rescue["id"]))
        assert issued["ok"] is True
        slip = issued["commission"]
        assert slip["状态"] == "有效"
        assert slip["待办片段"] == [f"{handover_no}-S2"]
        assert slip["证据编号"].startswith("EV-")
        assert store.find("emer_rescue", int(rescue["id"]))["status"] == "已确认"

        # 委托单不匹配 / 缺失时不能重进
        wrong = rescue_handover.reenter_handover(handover_no, "CM-UNKNOWN-1")
        assert wrong["ok"] is False

        # 凭单重新进入原交接任务，同步待办片段与签收回执
        reentered = rescue_handover.reenter_handover(handover_no, slip["委托单号"])
        assert reentered["ok"] is True
        assert reentered["待办片段"] == [f"{handover_no}-S2"]
        assert [r["回执号"] for r in reentered["签收回执"]] == [first["receipt"]["回执号"]]
        assert reentered["证据编号"] == slip["证据编号"]
        task = reentered["task"]
        assert task["状态"] == "在办"
        assert task["当前证据编号"] == slip["证据编号"]

        # 重新初始化不丢已签收原片的保管记录
        custody_after = task["保管记录"]
        assert len(custody_after) == 1
        assert custody_after[0] == custody_before

        # 委托单一次性，不能重复进入
        again = rescue_handover.reenter_handover(handover_no, slip["委托单号"])
        assert again["ok"] is False

        # 按委托续采剩余片段
        resumed = rescue_handover.submit_segment(handover_no, f"{handover_no}-S2")
        assert resumed["ok"] is True
        progress = rescue_handover.get_progress(handover_no)["progress"]
        assert progress["待办片段"] == []
        assert len(progress["已交付片段"]) == 2

    def test_commission_requires_suspension(self):
        rescue, _ = _running_project(segment_count=1)
        result = rescue_handover.issue_commission(int(rescue["id"]))
        assert result["ok"] is False
        assert "临时停工" in result["message"]

    def test_transmit_rejected_before_reentry(self):
        rescue, handover_no = _running_project(segment_count=1)
        service_for("emer_rescue").run_action(int(rescue["id"]), "临时停工")
        rescue_handover.issue_commission(int(rescue["id"]))
        result = rescue_handover.transmit_segment(handover_no, f"{handover_no}-S1")
        assert result["ok"] is False
        assert "凭单" in result["message"] or "重新进入" in result["message"]


class TestCloseProject:
    """关闭项目：原编号不得再发新片，已交付片段仍可查核。"""

    def test_close_blocks_new_segment_but_keeps_delivered(self):
        rescue, handover_no = _running_project(segment_count=2)
        rescue_handover.submit_segment(handover_no, f"{handover_no}-S1")
        entry, message = service_for("emer_rescue").run_action(int(rescue["id"]), "关闭项目")
        assert entry is not None, message
        assert entry["status"] == "已关闭"
        assert entry["pending"] is False

        # 未传输的片段不得再发布
        blocked = rescue_handover.submit_segment(handover_no, f"{handover_no}-S2")
        assert blocked["ok"] is False
        assert "不得在原编号下发布新片" in blocked["message"]

        # 关停前已交付的片段仍可查核
        view = rescue_handover.get_handover(handover_no)
        assert view["ok"] is True
        assert view["task"]["状态"] == "已关闭"
        assert view["task"]["已交付片段"] == [f"{handover_no}-S1"]
        assert len(view["task"]["签收回执"]) == 1

    def test_closed_project_rejects_all_actions(self):
        rescue, _ = _running_project(segment_count=1)
        service = service_for("emer_rescue")
        service.run_action(int(rescue["id"]), "关闭项目")
        for action in ("启动抢救", "提交确认", "临时停工", "关闭项目", "撤回记录"):
            entry, message = service.run_action(int(rescue["id"]), action)
            assert entry is None
            assert "已关闭" in message

    def test_close_voids_valid_commission(self):
        rescue, handover_no = _running_project(segment_count=1)
        service = service_for("emer_rescue")
        service.run_action(int(rescue["id"]), "临时停工")
        issued = rescue_handover.issue_commission(int(rescue["id"]))
        service.run_action(int(rescue["id"]), "关闭项目")
        assert rescue_handover._repo.commissions[issued["commission"]["委托单号"]]["状态"] == "作废"
        reentered = rescue_handover.reenter_handover(handover_no, issued["commission"]["委托单号"])
        assert reentered["ok"] is False

    def test_reopen_closed_handover_rejected(self):
        rescue, handover_no = _running_project(segment_count=1)
        service_for("emer_rescue").run_action(int(rescue["id"]), "关闭项目")
        result = rescue_handover.open_handover(int(rescue["id"]), 1, 1)
        assert result["ok"] is False
        assert "已关停" in result["message"] or "已关闭" in result["message"]

    def test_close_requires_active_or_suspended(self):
        rescue = _new_rescue()
        entry, message = service_for("emer_rescue").run_action(int(rescue["id"]), "关闭项目")
        assert entry is None
        assert "才能关闭" in message


class TestCloseResubmitConflict:
    """关闭与重投交错：两段视频，首段已签收，末段传输完成未收到回执。

    保护专员提交关闭项目的同时采集员重交末段，
    末段签收归属关停前的原传输，回执仍然只发一次。
    """

    def test_close_and_resubmit_interleaved(self):
        rescue, handover_no = _running_project(segment_count=2)
        first_no, last_no = f"{handover_no}-S1", f"{handover_no}-S2"

        # 首段已签收
        first = rescue_handover.submit_segment(handover_no, first_no)
        assert first["ok"] is True
        # 末段传输完成却没收到回执
        transmitted = rescue_handover.transmit_segment(handover_no, last_no)
        assert transmitted["ok"] is True

        # 保护专员提交关闭项目
        entry, message = service_for("emer_rescue").run_action(int(rescue["id"]), "关闭项目")
        assert entry is not None, message

        # 采集员重交末段：签收归属关停前的原传输
        resubmitted = rescue_handover.submit_segment(handover_no, last_no)
        assert resubmitted["ok"] is True
        assert resubmitted["receipt"]["签收归属"] == "关停前已传输，签收归属原传输"

        # 再次重提末段：仍是同一张回执
        again = rescue_handover.submit_segment(handover_no, last_no)
        assert again["receipt"]["回执号"] == resubmitted["receipt"]["回执号"]

        # 按旧号重发刚已签收的首段：不重复回执、不动保管记录
        resent = rescue_handover.submit_segment(handover_no, first_no)
        assert resent["receipt"]["回执号"] == first["receipt"]["回执号"]

        view = rescue_handover.get_handover(handover_no)["task"]
        assert view["状态"] == "已关闭"
        assert sorted(view["已交付片段"]) == sorted([first_no, last_no])
        assert len(view["签收回执"]) == 2
        assert len({r["回执号"] for r in view["签收回执"]}) == 2
        assert len(view["保管记录"]) == 2
        progress = rescue_handover.get_progress(handover_no)["progress"]
        assert progress["待办片段"] == []

    def test_never_transmitted_segment_loses_to_close(self):
        """关闭先落地时，从未传输的片段不得再发布。"""
        rescue, handover_no = _running_project(segment_count=2)
        rescue_handover.submit_segment(handover_no, f"{handover_no}-S1")
        service_for("emer_rescue").run_action(int(rescue["id"]), "关闭项目")
        result = rescue_handover.submit_segment(handover_no, f"{handover_no}-S2")
        assert result["ok"] is False
        assert "不得在原编号下发布新片" in result["message"]
        view = rescue_handover.get_handover(handover_no)["task"]
        assert view["已交付片段"] == [f"{handover_no}-S1"]


class TestEvidenceAndUsageScope:
    """重进采集页确认证据编号；核对抢救计划已获准的后续使用范围。"""

    def test_evidence_no_visible_after_reentry(self):
        rescue, handover_no = _running_project(segment_count=1)
        service_for("emer_rescue").run_action(int(rescue["id"]), "临时停工")
        issued = rescue_handover.issue_commission(int(rescue["id"]))
        slip = issued["commission"]
        reentered = rescue_handover.reenter_handover(handover_no, slip["委托单号"])
        assert reentered["task"]["当前证据编号"] == slip["证据编号"]
        view = rescue_handover.get_handover(handover_no)["task"]
        assert view["当前证据编号"] == slip["证据编号"]

    def test_usage_scope_survives_close(self):
        rescue, handover_no = _running_project(
            segment_count=1, usage_scope="仅限学术研究与档案保存"
        )
        rescue_handover.submit_segment(handover_no, f"{handover_no}-S1")
        service_for("emer_rescue").run_action(int(rescue["id"]), "关闭项目")
        scope = rescue_handover.get_usage_scope(handover_no)
        assert scope["ok"] is True
        assert scope["后续使用范围"] == "仅限学术研究与档案保存"
        assert scope["项目状态"] == "已关闭"
        # 已交付片段在关停后依旧可查核
        view = rescue_handover.get_handover(handover_no)["task"]
        assert view["已交付片段"] == [f"{handover_no}-S1"]
