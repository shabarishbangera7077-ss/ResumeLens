from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, password: str) -> str:
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes for bcrypt")
        return password


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AnalysisSummary(BaseModel):
    id: int
    job_title: str
    score: float
    created_at: datetime


class ComparisonResult(BaseModel):
    previous_score: float
    score_change: float
    newly_matched_skills: list[str]


class AnalysisResult(AnalysisSummary):
    skill_match: float
    text_similarity: float
    matched_skills: list[str]
    missing_skills: list[str]
    suggestions: list[str]
    comparison: ComparisonResult | None = None


class AnalysisDetail(AnalysisResult):
    resume_text: str
    job_description: str
