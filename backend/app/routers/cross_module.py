"""跨模块业务路由：传承链追溯、批量关联、引用设置。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import pipeline

router = APIRouter(prefix="/api/cross", tags=["跨模块业务"])


class SetRefPayload(BaseModel):
    module: str
    entry_id: int
    artisan_id: int | None = None
    craft_category_id: int | None = None
    skill_card_id: int | None = None
    creation_work_id: int | None = None
    creation_work_ids: list[int] | None = None
    artisan_ids: list[int] | None = None
    workshop_id: int | None = None

    class Config:
        extra = "allow"


# ── 批量引导 ──

@router.post("/bootstrap")
def bootstrap_cross_references() -> dict[str, Any]:
    """为现有种子数据批量建立跨模块引用关系。"""
    return pipeline.bootstrap_cross_references()


# ── 单独设置引用 ──

@router.post("/artisan/category")
def set_artisan_category(artisan_id: int, craft_category_id: int) -> dict[str, Any]:
    """传承人关联技艺分类。"""
    result = pipeline.set_artisan_craft_category(artisan_id, craft_category_id)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/apprentice/artisan")
def set_apprentice_artisan(apprentice_id: int, artisan_id: int) -> dict[str, Any]:
    """学徒关联传承人。"""
    result = pipeline.set_apprentice_artisan(apprentice_id, artisan_id)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/skill_card/category")
def set_skill_card_category(skill_card_id: int, craft_category_id: int) -> dict[str, Any]:
    """技艺图谱关联技艺分类。"""
    result = pipeline.set_skill_card_category(skill_card_id, craft_category_id)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/raw_material/skill")
def set_raw_material_skill(raw_material_id: int, skill_card_id: int) -> dict[str, Any]:
    """原材料关联技艺图谱。"""
    result = pipeline.set_raw_material_skill(raw_material_id, skill_card_id)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/tooling/skill")
def set_tooling_skill(tooling_id: int, skill_card_id: int) -> dict[str, Any]:
    """工具器械关联技艺图谱。"""
    result = pipeline.set_tooling_skill(tooling_id, skill_card_id)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/creation_work/relations")
def set_creation_work_relations(creation_work_id: int, skill_card_id: int, artisan_id: int) -> dict[str, Any]:
    """作品创作关联技艺图谱和传承人。"""
    result = pipeline.set_creation_work_relations(creation_work_id, skill_card_id, artisan_id)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/authentication/work")
def set_authentication_work(authentication_id: int, creation_work_id: int) -> dict[str, Any]:
    """作品认证关联作品。"""
    result = pipeline.set_authentication_work(authentication_id, creation_work_id)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/exhibition/relations")
def set_exhibition_relations(
    exhibition_id: int,
    creation_work_ids: str = "",
    artisan_ids: str = "",
) -> dict[str, Any]:
    """展览策划关联作品和传承人。参数用逗号分隔。"""
    cw_ids = [int(x.strip()) for x in creation_work_ids.split(",") if x.strip()]
    a_ids = [int(x.strip()) for x in artisan_ids.split(",") if x.strip()]
    result = pipeline.set_exhibition_relations(exhibition_id, cw_ids, a_ids)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/training_plan/relations")
def set_training_plan_relations(training_plan_id: int, workshop_id: int, artisan_id: int) -> dict[str, Any]:
    """培训方案关联传习所和传承人。"""
    result = pipeline.set_training_plan_relations(training_plan_id, workshop_id, artisan_id)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/field_survey/category")
def set_field_survey_category(field_survey_id: int, craft_category_id: int) -> dict[str, Any]:
    """田野调查关联技艺分类。"""
    result = pipeline.set_field_survey_category(field_survey_id, craft_category_id)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/digitization/skill")
def set_digitization_skill(digitization_id: int, skill_card_id: int) -> dict[str, Any]:
    """数字化采集关联技艺图谱。"""
    result = pipeline.set_digitization_skill(digitization_id, skill_card_id)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/ip_right/relations")
def set_ip_right_relations(ip_right_id: int, creation_work_id: int | None = None, skill_card_id: int | None = None) -> dict[str, Any]:
    """知识产权关联作品或技艺。"""
    result = pipeline.set_ip_right_relations(ip_right_id, creation_work_id, skill_card_id)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/evaluation/relations")
def set_evaluation_relations(evaluation_id: int, artisan_id: int | None = None, craft_category_id: int | None = None) -> dict[str, Any]:
    """传承评估关联传承人或技艺分类。"""
    result = pipeline.set_evaluation_relations(evaluation_id, artisan_id, craft_category_id)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/emer_rescue/category")
def set_emer_rescue_category(emer_rescue_id: int, craft_category_id: int) -> dict[str, Any]:
    """濒危抢救关联技艺分类。"""
    result = pipeline.set_emer_rescue_category(emer_rescue_id, craft_category_id)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


# ── 跨模块读操作 ──

@router.get("/heritage-chain")
def get_heritage_chain(skill_card_id: int | None = None, artisan_id: int | None = None) -> dict[str, Any]:
    """技艺传承链追溯。"""
    result = pipeline.heritage_chain(skill_card_id=skill_card_id, artisan_id=artisan_id)
    if not result.get("ok", True):
        raise HTTPException(status_code=400, detail=result.get("message", "查询失败"))
    return result


@router.get("/overview-refs")
def get_overview_with_refs() -> dict[str, Any]:
    """返回带跨模块引用信息的总览。"""
    return pipeline.module_overview_with_refs()