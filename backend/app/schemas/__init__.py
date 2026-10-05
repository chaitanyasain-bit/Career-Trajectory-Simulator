"""
Schemas package — re-exports all Pydantic schemas for convenient access.
"""

from app.schemas.auth import (  # noqa: F401
    TokenResponse,
    UserLogin,
    UserRead,
    UserRegister,
)
from app.schemas.profile import (  # noqa: F401
    EducationCreate,
    EducationRead,
    UserProfileCreate,
    UserProfileRead,
    UserProfileUpdate,
    UserSkillCreate,
    UserSkillRead,
    WorkExperienceCreate,
    WorkExperienceRead,
)
from app.schemas.role import (  # noqa: F401
    RoleBase,
    RoleCreate,
    RoleRead,
    RoleReadWithSkills,
    RoleSkillRequirementCreate,
    RoleSkillRequirementRead,
    RoleSummary,
    RoleTransitionCreate,
    RoleTransitionRead,
    RoleUpdate,
)
from app.schemas.simulation import (  # noqa: F401
    RoadmapStepRead,
    SimulationCreate,
    SimulationPathRead,
    SimulationRead,
    SimulationSummary,
    SkillGapRead,
    WhatIfRequest,
    WhatIfResponse,
)
from app.schemas.skill import (  # noqa: F401
    SkillBase,
    SkillCategoryBase,
    SkillCategoryCreate,
    SkillCategoryRead,
    SkillCategoryUpdate,
    SkillCreate,
    SkillRead,
    SkillSummary,
    SkillUpdate,
)
