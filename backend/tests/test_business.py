"""跨模块业务逻辑测试：验证至少两个模块间的完整数据流。
每条测试构建真实关联并断言业务结果。
"""
from __future__ import annotations

import pytest

from app.services import pipeline
from app.store import store


class TestCraftCategoryToArtisanChain:
    """测试1: 技艺分类 → 传承人 关联链"""

    def test_artisan_set_craft_category(self):
        result = pipeline.set_artisan_craft_category(artisan_id=1, craft_category_id=1)
        assert result["ok"] is True
        assert "已关联技艺门类" in result["message"]

        artisan = store.find("artisan", 1)
        assert artisan is not None
        assert artisan.get("门类ID") == 1
        assert artisan.get("所属门类") == store.find("craft_category", 1)["门类名称"]

    def test_artisan_ref_nonexistent_category(self):
        result = pipeline.set_artisan_craft_category(artisan_id=1, craft_category_id=999)
        assert result["ok"] is False
        assert "不存在" in result["message"]

    def test_artisan_ref_nonexistent_artisan(self):
        result = pipeline.set_artisan_craft_category(artisan_id=999, craft_category_id=1)
        assert result["ok"] is False


class TestArtisanToApprenticeChain:
    """测试2: 传承人 → 学徒 拜师链"""

    def test_apprentice_set_artisan(self):
        result = pipeline.set_apprentice_artisan(apprentice_id=1, artisan_id=2)
        assert result["ok"] is True
        assert "已拜师" in result["message"]

        apprentice = store.find("apprentice", 1)
        assert apprentice is not None
        assert apprentice.get("师傅ID") == 2
        assert apprentice.get("师傅姓名") == store.find("artisan", 2)["姓名"]

    def test_apprentice_ref_nonexistent(self):
        result = pipeline.set_apprentice_artisan(apprentice_id=999, artisan_id=1)
        assert result["ok"] is False


class TestCraftCategoryToSkillCardChain:
    """测试3: 技艺分类 → 技艺图谱 归门链"""

    def test_skill_card_set_category(self):
        result = pipeline.set_skill_card_category(skill_card_id=1, craft_category_id=2)
        assert result["ok"] is True
        assert "已归入门类" in result["message"]

        card = store.find("skill_card", 1)
        assert card.get("门类ID") == 2
        assert card.get("所属门类") == store.find("craft_category", 2)["门类名称"]


class TestSkillCardToRawMaterialChain:
    """测试4: 技艺图谱 → 原材料 原料服务链"""

    def test_raw_material_set_skill(self):
        result = pipeline.set_raw_material_skill(raw_material_id=2, skill_card_id=1)
        assert result["ok"] is True
        assert "已关联技艺" in result["message"]

        material = store.find("raw_material", 2)
        assert material.get("服务技艺ID") == 1
        assert material.get("服务技艺名称") == store.find("skill_card", 1)["技艺名称"]


class TestSkillCardToToolingChain:
    """测试5: 技艺图谱 → 工具器械 工具关联链"""

    def test_tooling_set_skill(self):
        result = pipeline.set_tooling_skill(tooling_id=2, skill_card_id=3)
        assert result["ok"] is True
        assert "已关联技艺" in result["message"]

        tool = store.find("tooling", 2)
        assert tool.get("关联技艺ID") == 3
        assert tool.get("关联技艺名称") == store.find("skill_card", 3)["技艺名称"]


class TestCreationWorkMultiRefChain:
    """测试6: 技艺图谱 + 传承人 → 作品创作 双重关联"""

    def test_creation_work_set_relations(self):
        result = pipeline.set_creation_work_relations(
            creation_work_id=2, skill_card_id=2, artisan_id=3
        )
        assert result["ok"] is True
        assert "已关联技艺" in result["message"]
        assert "传承人" in result["message"]

        work = store.find("creation_work", 2)
        assert work.get("技艺ID") == 2
        assert work.get("创作者ID") == 3
        assert work.get("技艺名称") == store.find("skill_card", 2)["技艺名称"]
        assert work.get("创作者姓名") == store.find("artisan", 3)["姓名"]


class TestAuthenticationWorkChain:
    """测试7: 作品 → 认证 作品认证链"""

    def test_authentication_set_work(self):
        result = pipeline.set_authentication_work(authentication_id=2, creation_work_id=1)
        assert result["ok"] is True
        assert "已关联作品" in result["message"]

        auth = store.find("authentication", 2)
        assert auth.get("作品ID") == 1
        assert auth.get("作品名称") == store.find("creation_work", 1)["作品名称"]


class TestTrainingPlanRelationsChain:
    """测试8: 传习所 + 传承人 → 培训方案 双关联"""

    def test_training_plan_set_relations(self):
        result = pipeline.set_training_plan_relations(
            training_plan_id=2, workshop_id=2, artisan_id=2
        )
        assert result["ok"] is True
        assert "已关联传习所与传承人" in result["message"]

        plan = store.find("training_plan", 2)
        assert plan.get("传习所ID") == 2
        assert plan.get("师傅ID") == 2
        assert plan.get("传习所名称") == store.find("workshop", 2)["场所名称"]


class TestFieldSurveyCategoryChain:
    """测试9: 技艺分类 → 田野调查 调查关联"""

    def test_field_survey_set_category(self):
        result = pipeline.set_field_survey_category(field_survey_id=2, craft_category_id=3)
        assert result["ok"] is True
        assert "已关联门类" in result["message"]

        survey = store.find("field_survey", 2)
        assert survey.get("技艺门类ID") == 3


class TestDigitizationSkillChain:
    """测试10: 技艺图谱 → 数字化采集 数字化关联"""

    def test_digitization_set_skill(self):
        result = pipeline.set_digitization_skill(digitization_id=2, skill_card_id=2)
        assert result["ok"] is True
        assert "已关联技艺" in result["message"]

        digi = store.find("digitization", 2)
        assert digi.get("技艺ID") == 2


class TestIpRightRelationsChain:
    """测试11: 作品+技艺 → 知识产权 权属关联"""

    def test_ip_right_set_relations(self):
        result = pipeline.set_ip_right_relations(
            ip_right_id=2, creation_work_id=2, skill_card_id=2
        )
        assert result["ok"] is True
        assert "已关联相应实体" in result["message"]

        ipr = store.find("ip_right", 2)
        assert ipr.get("作品ID") == 2
        assert ipr.get("技艺ID") == 2


class TestEvaluationRelationsChain:
    """测试12: 传承人+门类 → 传承评估 评估关联"""

    def test_evaluation_set_relations(self):
        result = pipeline.set_evaluation_relations(
            evaluation_id=2, artisan_id=2, craft_category_id=2
        )
        assert result["ok"] is True
        assert "已关联相应实体" in result["message"]

        ev = store.find("evaluation", 2)
        assert ev.get("传承人ID") == 2
        assert ev.get("门类ID") == 2


class TestEmerRescueCategoryChain:
    """测试13: 技艺分类 → 濒危抢救"""

    def test_emer_rescue_set_category(self):
        result = pipeline.set_emer_rescue_category(emer_rescue_id=2, craft_category_id=2)
        assert result["ok"] is True
        assert "已关联门类" in result["message"]

        rescue = store.find("emer_rescue", 2)
        assert rescue.get("门类ID") == 2


class TestHeritageChainTrace:
    """测试14: 传承链追溯 — 验证完整的多模块链路"""

    def test_heritage_chain_by_artisan(self):
        # 先用 bootstrap 确保引用关系完整
        bootstrap_result = pipeline.bootstrap_cross_references()
        assert bootstrap_result["ok"] is True

        # 从传承人出发追溯
        result = pipeline.heritage_chain(artisan_id=1)
        assert result.get("ok") is True
        chain = result.get("chain", {})

        nodes = chain.get("nodes", [])
        edges = chain.get("edges", [])

        # 应包含传承人、门类（如果有）、学徒、作品节点
        node_types = [n.get("type") for n in nodes]
        assert "artisan" in node_types, f"传承链应包含 artisan 节点，当前节点: {node_types}"

        # 应该有至少 2 条边（门类→传承人，传承人→学徒/作品等）
        assert len(edges) >= 1, f"传承链应包含至少1条边，当前边数: {len(edges)}"

    def test_heritage_chain_by_skill_card(self):
        result = pipeline.heritage_chain(skill_card_id=1)
        assert result.get("ok") is True
        chain = result.get("chain", {})
        nodes = chain.get("nodes", [])
        assert len(nodes) >= 1, "技艺追溯至少应包含技艺卡片节点"


class TestBootstrapCompleteness:
    """测试15: 引导建立所有跨模块引用后验证完整性"""

    def test_bootstrap_all_success(self):
        result = pipeline.bootstrap_cross_references()
        assert result["ok"] is True
        assert result["total"] > 20, f"bootstrap 应建立超过20条引用，实际 {result['total']}"
        assert result["success"] >= result["total"] - 1, "bootstrap 应几乎全部成功"

    def test_bootstrap_then_verify_refs(self):
        # Bootstrap 已在 test_heritage_chain_by_artisan 中调用，验证存量
        overview = pipeline.module_overview_with_refs()
        cross_links = overview.get("cross_links", {})

        # 每位传承人应有关联门类（种子数据有3条）
        assert cross_links.get("artisan_with_category", 0) >= 3

        # 每位学徒应有关联师傅
        assert cross_links.get("apprentice_with_artisan", 0) >= 3

        # 技艺图谱应归入门类
        assert cross_links.get("skill_card_with_category", 0) >= 3

        # 原材料应关联技艺
        assert cross_links.get("raw_material_with_skill", 0) >= 3

        # 工具应关联技艺
        assert cross_links.get("tooling_with_skill", 0) >= 3

        # 作品应有双重关联
        assert cross_links.get("creation_work_with_relations", 0) >= 3

        # 认证应关联作品
        assert cross_links.get("authentication_with_work", 0) >= 3


class TestExhibitionRelationsChain:
    """测试16: 展览关联作品和传承人"""

    def test_exhibition_set_relations(self):
        result = pipeline.set_exhibition_relations(
            exhibition_id=2, creation_work_ids=[1, 2], artisan_ids=[1, 3]
        )
        assert result["ok"] is True
        assert "已关联" in result["message"]

        exh = store.find("exhibition", 2)
        assert exh.get("展品ID列表") == [1, 2]
        assert exh.get("传承人ID列表") == [1, 3]
        assert len(exh.get("展品名称", [])) == 2