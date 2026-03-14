"""
app/schemas/schemas.py
----------------------
Pydantic v2 request/response models for every API endpoint.

Separating schemas from ORM models keeps the API contract independent
from database implementation details.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ---------------------------------------------------------------------------
# Shared config — enables ORM mode across all response schemas
# ---------------------------------------------------------------------------

class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# 1. Skill Graph
# ===========================================================================

class GraphNode(BaseModel):
    id:    str
    label: str
    type:  str  # "subject" | "skill" | "career"

class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float = 1.0

class SkillGraphResponse(BaseModel):
    career_id: int
    nodes:     list[GraphNode]
    links:     list[GraphEdge]


# ===========================================================================
# 2. Career Readiness Score
# ===========================================================================

class ReadinessResponse(BaseModel):
    user_id:        int
    career_id:      int
    career_title:   str
    readiness_score: float = Field(..., ge=0.0, le=1.0, description="Weighted readiness 0–1")
    percentage:     float  = Field(..., description="readiness_score × 100")
    skills_assessed: int


# ===========================================================================
# 3. Skill Gap Detection
# ===========================================================================

class SkillGapItem(BaseModel):
    skill_id:    int
    skill_name:  str
    skill_level: float
    weight:      float
    category:    str   # "strong" | "weak" | "missing"

class SkillGapResponse(BaseModel):
    user_id:   int
    career_id: int
    strong:    list[SkillGapItem]
    weak:      list[SkillGapItem]
    missing:   list[SkillGapItem]
    summary:   dict[str, int]   # {"strong": N, "weak": N, "missing": N}


# ===========================================================================
# 4. Adaptive Study Planner
# ===========================================================================

class PlannerRequest(BaseModel):
    user_id:       int
    career_id:     int
    exam_days_left: int = Field(..., ge=1, description="Days until the exam / deadline")
    top_n:         int  = Field(default=3, ge=1, le=10)

class StudyTask(BaseModel):
    skill_id:   int
    skill_name: str
    priority:   float
    skill_level: float
    weight:     float
    reason:     str

class PlannerResponse(BaseModel):
    user_id:       int
    career_id:     int
    exam_days_left: int
    tasks:         list[StudyTask]


# ===========================================================================
# 5. Resume Skill Extractor
# ===========================================================================

class ResumeSkillMatch(BaseModel):
    skill_id:   int
    skill_name: str
    matched_keywords: list[str]

class ResumeExtractResponse(BaseModel):
    filename:        str
    total_skills_in_db: int
    matched_skills:  list[ResumeSkillMatch]
    match_count:     int
    coverage_pct:    float


# ===========================================================================
# 6. Burnout Risk
# ===========================================================================

class BurnoutRequest(BaseModel):
    user_id:     int
    sleep_hours: float = Field(..., ge=0, le=24)
    study_hours: float = Field(..., ge=0, le=24)
    focus_score: float = Field(..., ge=0, le=100)

class BurnoutResponse(BaseModel):
    user_id:     int
    risk_score:  float
    risk_level:  str    # "Low" | "Medium" | "High"
    advice:      str


# ===========================================================================
# 7. Digital Twin / Score Simulation
# ===========================================================================

class SimulationRequest(BaseModel):
    study_hours:        float = Field(..., ge=0)
    focus_score:        float = Field(..., ge=0, le=100)
    revision_frequency: int   = Field(..., ge=0)

class SimulationResponse(BaseModel):
    predicted_score:    float
    confidence_note:    str
    input_summary:      dict[str, Any]


# ===========================================================================
# 8. Performance Dashboard
# ===========================================================================

class WeeklyHourEntry(BaseModel):
    week:  str
    hours: float

class SkillProgressEntry(BaseModel):
    skill_name:  str
    skill_level: float

class FocusDistributionEntry(BaseModel):
    range: str   # e.g. "0-25", "26-50", "51-75", "76-100"
    count: int

class DashboardResponse(BaseModel):
    user_id:            int
    weekly_hours:       list[WeeklyHourEntry]
    skill_progress:     list[SkillProgressEntry]
    focus_distribution: list[FocusDistributionEntry]
    total_study_hours:  float
    avg_focus_score:    float
    log_count:          int


# ===========================================================================
# Utility — User & Career CRUD (used in seed script / future admin routes)
# ===========================================================================

class UserCreate(BaseModel):
    name:  str
    email: str

class CareerCreate(BaseModel):
    title:       str
    description: str = ""

class SkillCreate(BaseModel):
    name:       str
    subject_id: int | None = None
    keywords:   str = ""
