"""
Pydantic v2 schemas for UserProfile, UserSkill, Education, WorkExperience.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    field_validator,
    model_validator,
)

from app.schemas.skill import SkillSummary

HTTP_URL = TypeAdapter(AnyHttpUrl)


# ── UserSkill ─────────────────────────────────────────────────────────────────

class UserSkillBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_id: str = Field(min_length=1, max_length=36)
    proficiency_level: int = Field(default=3, ge=1, le=5)
    months_of_experience: int | None = Field(default=None, ge=0)


class UserSkillCreate(UserSkillBase):
    pass


class UserSkillRead(UserSkillBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_id: str
    skill: SkillSummary | None = None
    is_self_assessed: bool
    created_at: datetime
    updated_at: datetime


# ── Education ─────────────────────────────────────────────────────────────────

class EducationBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    institution: str = Field(..., min_length=1, max_length=300)
    degree: str = Field(..., min_length=1, max_length=200)
    field_of_study: str | None = Field(default=None, max_length=200)
    start_year: int | None = Field(default=None, ge=1950, le=2100)
    end_year: int | None = Field(default=None, ge=1950, le=2100)
    is_current: bool = False

    @field_validator("institution", "degree", "field_of_study")
    @classmethod
    def strip_education_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Education text fields cannot be blank.")
        return value

    @model_validator(mode="after")
    def validate_year_range(self) -> EducationBase:
        if (
            self.start_year is not None
            and self.end_year is not None
            and self.end_year < self.start_year
        ):
            raise ValueError("Education end_year must not precede start_year.")
        if self.is_current and self.end_year is not None:
            raise ValueError("Current education cannot have an end_year.")
        return self


class EducationCreate(EducationBase):
    pass


class EducationRead(EducationBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_id: str
    created_at: datetime
    updated_at: datetime


# ── WorkExperience ────────────────────────────────────────────────────────────

class WorkExperienceBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: str | None = Field(default=None, max_length=300)
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    start_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")  # YYYY-MM
    end_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    is_current: bool = False

    @field_validator("company", "title")
    @classmethod
    def strip_work_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Work title and company cannot be blank.")
        return value

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_month_date(cls, value: str | None) -> str | None:
        if value is not None:
            datetime.strptime(value, "%Y-%m")
        return value

    @model_validator(mode="after")
    def validate_date_range(self) -> WorkExperienceBase:
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Work end_date must not precede start_date.")
        if self.is_current and self.end_date is not None:
            raise ValueError("Current work cannot have an end_date.")
        return self


class WorkExperienceCreate(WorkExperienceBase):
    pass


class WorkExperienceRead(WorkExperienceBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_id: str
    is_project: bool
    created_at: datetime
    updated_at: datetime


class ProjectBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=200)
    company: str | None = Field(default=None, max_length=300)
    description: str | None = None
    start_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    end_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    is_current: bool = False

    @field_validator("title", "company")
    @classmethod
    def strip_project_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Project title and company cannot be blank.")
        return value

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_month_date(cls, value: str | None) -> str | None:
        if value is not None:
            datetime.strptime(value, "%Y-%m")
        return value

    @model_validator(mode="after")
    def validate_date_range(self) -> ProjectBase:
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Project end_date must not precede start_date.")
        if self.is_current and self.end_date is not None:
            raise ValueError("Current projects cannot have an end_date.")
        return self


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_id: str
    is_project: bool = True
    created_at: datetime
    updated_at: datetime


# ── UserProfile ───────────────────────────────────────────────────────────────

class UserProfileBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_role_id: str | None = None
    years_of_experience: float = Field(default=0.0, ge=0.0, le=60.0)
    bio: str | None = None
    location: str | None = Field(default=None, max_length=200)
    linkedin_url: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=500)

    @field_validator("bio", "location")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("linkedin_url", "github_url")
    @classmethod
    def validate_profile_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        parsed_url = HTTP_URL.validate_python(value.strip())
        if parsed_url.scheme not in {"http", "https"}:
            raise ValueError("Profile links must use HTTP or HTTPS.")
        return str(parsed_url)


class UserProfileCreate(UserProfileBase):
    """Fields accepted when creating the authenticated user's profile."""

    skills: list[UserSkillCreate] = Field(default_factory=list, max_length=100)
    educations: list[EducationCreate] = Field(default_factory=list, max_length=50)
    experiences: list[WorkExperienceCreate] = Field(default_factory=list, max_length=100)
    projects: list[ProjectCreate] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_unique_skill_ids(self) -> UserProfileCreate:
        skill_ids = [skill.skill_id for skill in self.skills]
        if len(skill_ids) != len(set(skill_ids)):
            raise ValueError("A skill may only appear once in the profile.")
        return self


class UserProfileRead(UserProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    user_skills: list[UserSkillRead] = []
    educations: list[EducationRead] = []
    experiences: list[WorkExperienceRead] = []
    projects: list[ProjectRead] = []
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_role_id: str | None = Field(default=None, min_length=1, max_length=36)
    years_of_experience: float | None = Field(default=None, ge=0.0, le=60.0)
    bio: str | None = None
    location: str | None = Field(default=None, max_length=200)
    linkedin_url: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=500)
    skills: list[UserSkillCreate] | None = Field(default=None, max_length=100)
    educations: list[EducationCreate] | None = Field(default=None, max_length=50)
    experiences: list[WorkExperienceCreate] | None = Field(default=None, max_length=100)
    projects: list[ProjectCreate] | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validate_unique_skill_ids(self) -> UserProfileUpdate:
        if self.skills is not None:
            skill_ids = [skill.skill_id for skill in self.skills]
            if len(skill_ids) != len(set(skill_ids)):
                raise ValueError("A skill may only appear once in the profile.")
        return self
