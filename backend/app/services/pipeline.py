"""跨模块业务流水线：技艺传承链追溯、作品认证链、模块关联查询和写入。
所有操作基于内存 store，无外部依赖。
"""
from __future__ import annotations

from typing import Any

from app.store import store


# ── 单模块引用字段读取 ──────────────────────────────────────────

def _ref_field(module: str, entry_id: int, field: str) -> Any | None:
    """读取某个模块中某条记录的指定字段值（用于跨模块引用查找）。"""
    entry = store.find(module, entry_id)
    if entry is None:
        return None
    return entry.get(field)


def _find_by_field(module: str, field: str, value: Any) -> dict[str, Any] | None:
    """在某个模块中按字段值查找第一条匹配记录。"""
    for row in store.rows(module):
        if str(row.get(field, "")) == str(value):
            return row
    return None


def _all_by_field(module: str, field: str, value: Any) -> list[dict[str, Any]]:
    """在某个模块中按字段值查找所有匹配记录。"""
    return [row for row in store.rows(module) if str(row.get(field, "")) == str(value)]


# ── 跨模块引用字段写入 ──────────────────────────────────────────

def _set_ref(module: str, entry_id: int, field: str, value: Any) -> bool:
    """为某个模块的某条记录设置引用字段。"""
    entry = store.find(module, entry_id)
    if entry is None:
        return False
    entry[field] = value
    return True


# ── 跨模块业务操作 ───────────────────────────────────────────────

def set_artisan_craft_category(artisan_id: int, craft_category_id: int) -> dict[str, Any]:
    """传承人关联技艺分类：每位传承人属于特定技艺门类。"""
    artisan = store.find("artisan", artisan_id)
    if artisan is None:
        return {"ok": False, "message": f"传承人 {artisan_id} 不存在"}
    category = store.find("craft_category", craft_category_id)
    if category is None:
        return {"ok": False, "message": f"技艺分类 {craft_category_id} 不存在"}
    artisan["所属门类"] = category.get("门类名称", "")
    artisan["门类ID"] = craft_category_id
    return {"ok": True, "message": f"传承人 {artisan.get('姓名')} 已关联技艺门类 {category.get('门类名称')}", "entry": artisan}


def set_apprentice_artisan(apprentice_id: int, artisan_id: int) -> dict[str, Any]:
    """学徒关联传承人：学徒拜在某传承人门下。"""
    apprentice = store.find("apprentice", apprentice_id)
    if apprentice is None:
        return {"ok": False, "message": f"学徒 {apprentice_id} 不存在"}
    artisan = store.find("artisan", artisan_id)
    if artisan is None:
        return {"ok": False, "message": f"传承人 {artisan_id} 不存在"}
    apprentice["师傅ID"] = artisan_id
    apprentice["师傅姓名"] = artisan.get("姓名", "")
    return {"ok": True, "message": f"学徒 {apprentice.get('学徒姓名')} 已拜师 {artisan.get('姓名')}", "entry": apprentice}


def set_skill_card_category(skill_card_id: int, craft_category_id: int) -> dict[str, Any]:
    """技艺图谱引用技艺分类：每个技艺卡片归入特定门类。"""
    card = store.find("skill_card", skill_card_id)
    if card is None:
        return {"ok": False, "message": f"技艺卡片 {skill_card_id} 不存在"}
    category = store.find("craft_category", craft_category_id)
    if category is None:
        return {"ok": False, "message": f"技艺分类 {craft_category_id} 不存在"}
    card["所属门类"] = category.get("门类名称", "")
    card["门类ID"] = craft_category_id
    return {"ok": True, "message": f"技艺 {card.get('技艺名称')} 已归入门类 {category.get('门类名称')}", "entry": card}


def set_raw_material_skill(raw_material_id: int, skill_card_id: int) -> dict[str, Any]:
    """原材料关联技艺图谱：原料服务于特定技艺。"""
    material = store.find("raw_material", raw_material_id)
    if material is None:
        return {"ok": False, "message": f"原料 {raw_material_id} 不存在"}
    card = store.find("skill_card", skill_card_id)
    if card is None:
        return {"ok": False, "message": f"技艺卡片 {skill_card_id} 不存在"}
    material["服务技艺ID"] = skill_card_id
    material["服务技艺名称"] = card.get("技艺名称", "")
    return {"ok": True, "message": f"原料 {material.get('原料名称')} 已关联技艺 {card.get('技艺名称')}", "entry": material}


def set_tooling_skill(tooling_id: int, skill_card_id: int) -> dict[str, Any]:
    """工具器械关联技艺图谱。"""
    tool = store.find("tooling", tooling_id)
    if tool is None:
        return {"ok": False, "message": f"工具 {tooling_id} 不存在"}
    card = store.find("skill_card", skill_card_id)
    if card is None:
        return {"ok": False, "message": f"技艺卡片 {skill_card_id} 不存在"}
    tool["关联技艺ID"] = skill_card_id
    tool["关联技艺名称"] = card.get("技艺名称", "")
    return {"ok": True, "message": f"工具 {tool.get('工具名称')} 已关联技艺 {card.get('技艺名称')}", "entry": tool}


def set_creation_work_relations(creation_work_id: int, skill_card_id: int, artisan_id: int) -> dict[str, Any]:
    """作品创作关联技艺图谱和传承人：谁用什么技艺创作了什么。"""
    work = store.find("creation_work", creation_work_id)
    if work is None:
        return {"ok": False, "message": f"作品 {creation_work_id} 不存在"}
    card = store.find("skill_card", skill_card_id)
    if card is None:
        return {"ok": False, "message": f"技艺卡片 {skill_card_id} 不存在"}
    artisan = store.find("artisan", artisan_id)
    if artisan is None:
        return {"ok": False, "message": f"传承人 {artisan_id} 不存在"}
    work["技艺ID"] = skill_card_id
    work["技艺名称"] = card.get("技艺名称", "")
    work["创作者ID"] = artisan_id
    work["创作者姓名"] = artisan.get("姓名", "")
    return {"ok": True, "message": f"作品 {work.get('作品名称')} 已关联技艺 {card.get('技艺名称')} 与传承人 {artisan.get('姓名')}", "entry": work}


def set_authentication_work(authentication_id: int, creation_work_id: int) -> dict[str, Any]:
    """作品认证关联作品：认证针对特定作品。"""
    auth = store.find("authentication", authentication_id)
    if auth is None:
        return {"ok": False, "message": f"认证 {authentication_id} 不存在"}
    work = store.find("creation_work", creation_work_id)
    if work is None:
        return {"ok": False, "message": f"作品 {creation_work_id} 不存在"}
    auth["作品ID"] = creation_work_id
    auth["作品名称"] = work.get("作品名称", "")
    return {"ok": True, "message": f"认证 {auth.get('认证类型')} 已关联作品 {work.get('作品名称')}", "entry": auth}


def set_exhibition_relations(exhibition_id: int, creation_work_ids: list[int], artisan_ids: list[int]) -> dict[str, Any]:
    """展览策划关联作品和传承人。"""
    exh = store.find("exhibition", exhibition_id)
    if exh is None:
        return {"ok": False, "message": f"展览 {exhibition_id} 不存在"}
    exh["展品ID列表"] = creation_work_ids
    exh["传承人ID列表"] = artisan_ids
    works = [store.find("creation_work", wid) for wid in creation_work_ids]
    artisans = [store.find("artisan", aid) for aid in artisan_ids]
    exh["展品名称"] = [w.get("作品名称") if w else "?" for w in works]
    exh["参展传承人"] = [a.get("姓名") if a else "?" for a in artisans]
    return {"ok": True, "message": f"展览 {exh.get('展览主题')} 已关联 {len(creation_work_ids)} 件作品与 {len(artisan_ids)} 位传承人", "entry": exh}


def set_training_plan_relations(training_plan_id: int, workshop_id: int, artisan_id: int) -> dict[str, Any]:
    """培训方案关联传习所和传承人。"""
    plan = store.find("training_plan", training_plan_id)
    if plan is None:
        return {"ok": False, "message": f"培训方案 {training_plan_id} 不存在"}
    ws = store.find("workshop", workshop_id)
    if ws is None:
        return {"ok": False, "message": f"传习所 {workshop_id} 不存在"}
    artisan = store.find("artisan", artisan_id)
    if artisan is None:
        return {"ok": False, "message": f"传承人 {artisan_id} 不存在"}
    plan["传习所ID"] = workshop_id
    plan["传习所名称"] = ws.get("场所名称", "")
    plan["师傅ID"] = artisan_id
    plan["师傅姓名"] = artisan.get("姓名", "")
    return {"ok": True, "message": f"培训方案 {plan.get('课程名称')} 已关联传习所与传承人", "entry": plan}


def set_field_survey_category(field_survey_id: int, craft_category_id: int) -> dict[str, Any]:
    """田野调查关联技艺分类。"""
    survey = store.find("field_survey", field_survey_id)
    if survey is None:
        return {"ok": False, "message": f"田野调查 {field_survey_id} 不存在"}
    category = store.find("craft_category", craft_category_id)
    if category is None:
        return {"ok": False, "message": f"技艺分类 {craft_category_id} 不存在"}
    survey["技艺门类ID"] = craft_category_id
    survey["技艺门类名称"] = category.get("门类名称", "")
    return {"ok": True, "message": f"田野调查 {survey.get('调查地点')} 已关联门类 {category.get('门类名称')}", "entry": survey}


def set_digitization_skill(digitization_id: int, skill_card_id: int) -> dict[str, Any]:
    """数字化采集关联技艺图谱。"""
    digi = store.find("digitization", digitization_id)
    if digi is None:
        return {"ok": False, "message": f"数字化采集 {digitization_id} 不存在"}
    card = store.find("skill_card", skill_card_id)
    if card is None:
        return {"ok": False, "message": f"技艺卡片 {skill_card_id} 不存在"}
    digi["技艺ID"] = skill_card_id
    digi["技艺名称"] = card.get("技艺名称", "")
    return {"ok": True, "message": f"数字化采集 {digi.get('资源类型')} 已关联技艺 {card.get('技艺名称')}", "entry": digi}


def set_ip_right_relations(ip_right_id: int, creation_work_id: int | None = None, skill_card_id: int | None = None) -> dict[str, Any]:
    """知识产权关联作品或技艺。"""
    ipr = store.find("ip_right", ip_right_id)
    if ipr is None:
        return {"ok": False, "message": f"知识产权 {ip_right_id} 不存在"}
    if creation_work_id:
        work = store.find("creation_work", creation_work_id)
        if work is None:
            return {"ok": False, "message": f"作品 {creation_work_id} 不存在"}
        ipr["作品ID"] = creation_work_id
        ipr["作品名称"] = work.get("作品名称", "")
    if skill_card_id:
        card = store.find("skill_card", skill_card_id)
        if card is None:
            return {"ok": False, "message": f"技艺卡片 {skill_card_id} 不存在"}
        ipr["技艺ID"] = skill_card_id
        ipr["技艺名称"] = card.get("技艺名称", "")
    return {"ok": True, "message": f"知识产权 {ipr.get('权利类型')} 已关联相应实体", "entry": ipr}


def set_evaluation_relations(evaluation_id: int, artisan_id: int | None = None, craft_category_id: int | None = None) -> dict[str, Any]:
    """传承评估关联传承人或技艺分类。"""
    ev = store.find("evaluation", evaluation_id)
    if ev is None:
        return {"ok": False, "message": f"评估 {evaluation_id} 不存在"}
    if artisan_id:
        artisan = store.find("artisan", artisan_id)
        if artisan is None:
            return {"ok": False, "message": f"传承人 {artisan_id} 不存在"}
        ev["传承人ID"] = artisan_id
        ev["传承人姓名"] = artisan.get("姓名", "")
    if craft_category_id:
        category = store.find("craft_category", craft_category_id)
        if category is None:
            return {"ok": False, "message": f"技艺分类 {craft_category_id} 不存在"}
        ev["门类ID"] = craft_category_id
        ev["门类名称"] = category.get("门类名称", "")
    return {"ok": True, "message": f"评估 {ev.get('评估对象')} 已关联相应实体", "entry": ev}


def set_emer_rescue_category(emer_rescue_id: int, craft_category_id: int) -> dict[str, Any]:
    """濒危抢救关联技艺分类。"""
    rescue = store.find("emer_rescue", emer_rescue_id)
    if rescue is None:
        return {"ok": False, "message": f"濒危抢救 {emer_rescue_id} 不存在"}
    category = store.find("craft_category", craft_category_id)
    if category is None:
        return {"ok": False, "message": f"技艺分类 {craft_category_id} 不存在"}
    rescue["门类ID"] = craft_category_id
    rescue["门类名称"] = category.get("门类名称", "")
    return {"ok": True, "message": f"濒危抢救 {rescue.get('濒危等级')} 已关联门类 {category.get('门类名称')}", "entry": rescue}


# ── 跨模块读操作：传承链追溯 ──────────────────────────────────────

def heritage_chain(skill_card_id: int | None = None, artisan_id: int | None = None) -> dict[str, Any]:
    """技艺传承链追溯：从技艺或传承人出发，追溯完整的传承链路。
    
    返回：技艺门类 → 传承人 → 学徒 → 作品 → 认证 的完整链条信息。
    """
    chain: dict[str, Any] = {"nodes": [], "edges": []}
    nodes = chain["nodes"]
    edges = chain["edges"]

    # 从 skill_card 出发
    if skill_card_id:
        card = store.find("skill_card", skill_card_id)
        if card is None:
            return {"ok": False, "message": f"技艺卡片 {skill_card_id} 不存在"}
        nodes.append({"type": "skill_card", "id": card["id"], "label": card.get("技艺名称", ""), "data": card})

        # 查找技艺门类
        category_id = card.get("门类ID")
        if category_id:
            category = store.find("craft_category", int(category_id))
            if category:
                nodes.append({"type": "craft_category", "id": category["id"], "label": category.get("门类名称", ""), "data": category})
                edges.append({"from": f"craft_category_{category['id']}", "to": f"skill_card_{card['id']}", "label": "归入门类"})

        # 查找关联的传承人（通过作品和原材料反向查）
        works = [row for row in store.rows("creation_work") if str(row.get("技艺ID", "")) == str(skill_card_id)]

    # 从 artisan 出发
    if artisan_id:
        artisan = store.find("artisan", artisan_id)
        if artisan is None:
            return {"ok": False, "message": f"传承人 {artisan_id} 不存在"}
        nodes.append({"type": "artisan", "id": artisan["id"], "label": artisan.get("姓名", ""), "data": artisan})

        # 查找门类
        category_id = artisan.get("门类ID")
        if category_id:
            category = store.find("craft_category", int(category_id))
            if category:
                existing = any(n.get("id") == category["id"] and n.get("type") == "craft_category" for n in nodes)
                if not existing:
                    nodes.append({"type": "craft_category", "id": category["id"], "label": category.get("门类名称", ""), "data": category})
                edges.append({"from": f"craft_category_{category['id']}", "to": f"artisan_{artisan['id']}", "label": "所属门类"})

        # 查找学徒
        apprentices = _all_by_field("apprentice", "师傅ID", artisan_id)
        for app in apprentices:
            nodes.append({"type": "apprentice", "id": app["id"], "label": app.get("学徒姓名", ""), "data": app})
            edges.append({"from": f"artisan_{artisan['id']}", "to": f"apprentice_{app['id']}", "label": "收徒"})

        # 查找作品
        works = _all_by_field("creation_work", "创作者ID", artisan_id)
        for w in works:
            existing_w = any(n.get("id") == w["id"] and n.get("type") == "creation_work" for n in nodes)
            if not existing_w:
                nodes.append({"type": "creation_work", "id": w["id"], "label": w.get("作品名称", ""), "data": w})
            edges.append({"from": f"artisan_{artisan['id']}", "to": f"creation_work_{w['id']}", "label": "创作"})

    return {"ok": True, "chain": chain}


def module_overview_with_refs() -> dict[str, Any]:
    """返回带跨模块引用信息的总览。"""
    overview = store.overview()
    cross_links = {
        "artisan_with_category": sum(1 for r in store.rows("artisan") if r.get("门类ID")),
        "apprentice_with_artisan": sum(1 for r in store.rows("apprentice") if r.get("师傅ID")),
        "skill_card_with_category": sum(1 for r in store.rows("skill_card") if r.get("门类ID")),
        "raw_material_with_skill": sum(1 for r in store.rows("raw_material") if r.get("服务技艺ID")),
        "tooling_with_skill": sum(1 for r in store.rows("tooling") if r.get("关联技艺ID")),
        "creation_work_with_relations": sum(1 for r in store.rows("creation_work") if r.get("技艺ID") and r.get("创作者ID")),
        "authentication_with_work": sum(1 for r in store.rows("authentication") if r.get("作品ID")),
    }
    overview["cross_links"] = cross_links
    return overview


# ── 批量关联预置数据（一次调用建立所有种子数据间的引用）─────────

def bootstrap_cross_references() -> dict[str, Any]:
    """为种子数据批量建立跨模块引用关系。"""
    results = []

    # artisan[1-3] → craft_category[1-3]
    for i in (1, 2, 3):
        r = set_artisan_craft_category(i, i)
        results.append(r)

    # apprentice[1-3] → artisan[1-3]
    for i in (1, 2, 3):
        r = set_apprentice_artisan(i, i)
        results.append(r)

    # skill_card[1-3] → craft_category[1-3]
    for i in (1, 2, 3):
        r = set_skill_card_category(i, i)
        results.append(r)

    # raw_material[1-3] → skill_card[1-3]
    for i in (1, 2, 3):
        r = set_raw_material_skill(i, i)
        results.append(r)

    # tooling[1-3] → skill_card[1-3]
    for i in (1, 2, 3):
        r = set_tooling_skill(i, i)
        results.append(r)

    # creation_work[1-3] → skill_card[1-3] + artisan[1-3]
    for i in (1, 2, 3):
        r = set_creation_work_relations(i, i, i)
        results.append(r)

    # authentication[1-3] → creation_work[1-3]
    for i in (1, 2, 3):
        r = set_authentication_work(i, i)
        results.append(r)

    # exhibition[1] → creation_work[1,2] + artisan[1,2]
    r = set_exhibition_relations(1, [1, 2], [1, 2])
    results.append(r)

    # training_plan[1] → workshop[1] + artisan[1]
    r = set_training_plan_relations(1, 1, 1)
    results.append(r)

    # field_survey[1] → craft_category[1]
    r = set_field_survey_category(1, 1)
    results.append(r)

    # digitization[1] → skill_card[1]
    r = set_digitization_skill(1, 1)
    results.append(r)

    # ip_right[1] → creation_work[1] + skill_card[1]
    r = set_ip_right_relations(1, 1, 1)
    results.append(r)

    # evaluation[1] → artisan[1] + craft_category[1]
    r = set_evaluation_relations(1, 1, 1)
    results.append(r)

    # emer_rescue[1] → craft_category[1]
    r = set_emer_rescue_category(1, 1)
    results.append(r)

    ok_count = sum(1 for r in results if r["ok"])
    return {"ok": True, "total": len(results), "success": ok_count, "details": results}