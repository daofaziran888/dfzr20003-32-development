"""领域服务注册表：通用资源路由按模块 key 分派到独立业务服务。"""
from __future__ import annotations

from app.services.base import BaseModuleService
from app.services.craft_category import CraftCategoryService
from app.services.artisan import ArtisanService
from app.services.apprentice import ApprenticeService
from app.services.skill_card import SkillCardService
from app.services.raw_material import RawMaterialService
from app.services.tooling import ToolingService
from app.services.workshop import WorkshopService
from app.services.training_plan import TrainingPlanService
from app.services.creation_work import CreationWorkService
from app.services.authentication import AuthenticationService
from app.services.exhibition import ExhibitionService
from app.services.grant_fund import GrantFundService
from app.services.field_survey import FieldSurveyService
from app.services.digitization import DigitizationService
from app.services.publication import PublicationService
from app.services.ip_right import IpRightService
from app.services.evaluation import EvaluationService
from app.services.emer_rescue import EmerRescueService

SERVICES: dict[str, BaseModuleService] = {
    "craft_category": CraftCategoryService(),
    "artisan": ArtisanService(),
    "apprentice": ApprenticeService(),
    "skill_card": SkillCardService(),
    "raw_material": RawMaterialService(),
    "tooling": ToolingService(),
    "workshop": WorkshopService(),
    "training_plan": TrainingPlanService(),
    "creation_work": CreationWorkService(),
    "authentication": AuthenticationService(),
    "exhibition": ExhibitionService(),
    "grant_fund": GrantFundService(),
    "field_survey": FieldSurveyService(),
    "digitization": DigitizationService(),
    "publication": PublicationService(),
    "ip_right": IpRightService(),
    "evaluation": EvaluationService(),
    "emer_rescue": EmerRescueService(),
}


def service_for(module: str) -> BaseModuleService | None:
    return SERVICES.get(module)
