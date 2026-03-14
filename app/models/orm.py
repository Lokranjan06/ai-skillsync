"""
app/models/orm.py
-----------------
SQLAlchemy ORM models — one class per database table.

Table relationships:
  users ──< user_skill_progress >── skills
  users ──< study_logs
  careers ──< career_skills >── skills
  subjects ──< skills
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey,
    DateTime, Text, func,
)
from sqlalchemy.orm import relationship

from app.database.session import Base


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(120), nullable=False)
    email      = Column(String(200), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    skill_progress = relationship("UserSkillProgress", back_populates="user", cascade="all, delete-orphan")
    study_logs     = relationship("StudyLog",          back_populates="user", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# subjects  (e.g. "Mathematics", "Computer Science")
# ---------------------------------------------------------------------------

class Subject(Base):
    __tablename__ = "subjects"

    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False)

    skills = relationship("Skill", back_populates="subject")


# ---------------------------------------------------------------------------
# skills  (e.g. "Linear Algebra", "Python", "SQL")
# ---------------------------------------------------------------------------

class Skill(Base):
    __tablename__ = "skills"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(120), unique=True, nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    keywords   = Column(Text, default="")  # comma-separated resume-matching terms

    subject        = relationship("Subject",           back_populates="skills")
    career_skills  = relationship("CareerSkill",       back_populates="skill")
    user_progress  = relationship("UserSkillProgress", back_populates="skill")


# ---------------------------------------------------------------------------
# careers  (e.g. "Data Scientist", "Backend Engineer")
# ---------------------------------------------------------------------------

class Career(Base):
    __tablename__ = "careers"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), unique=True, nullable=False)
    description = Column(Text, default="")

    career_skills = relationship("CareerSkill", back_populates="career")


# ---------------------------------------------------------------------------
# career_skills  — junction table with skill weight per career
# ---------------------------------------------------------------------------

class CareerSkill(Base):
    __tablename__ = "career_skills"

    id        = Column(Integer, primary_key=True, index=True)
    career_id = Column(Integer, ForeignKey("careers.id"),  nullable=False)
    skill_id  = Column(Integer, ForeignKey("skills.id"),   nullable=False)
    weight    = Column(Float,   nullable=False, default=1.0)  # 0.0 – 1.0

    career = relationship("Career", back_populates="career_skills")
    skill  = relationship("Skill",  back_populates="career_skills")


# ---------------------------------------------------------------------------
# user_skill_progress  — a user's current mastery level for a skill
# ---------------------------------------------------------------------------

class UserSkillProgress(Base):
    __tablename__ = "user_skill_progress"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"),  nullable=False)
    skill_id     = Column(Integer, ForeignKey("skills.id"), nullable=False)
    skill_level  = Column(Float, default=0.0)   # 0.0 (none) – 1.0 (mastered)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user  = relationship("User",  back_populates="skill_progress")
    skill = relationship("Skill", back_populates="user_progress")


# ---------------------------------------------------------------------------
# study_logs  — raw learning session records
# ---------------------------------------------------------------------------

class StudyLog(Base):
    __tablename__ = "study_logs"

    id                 = Column(Integer, primary_key=True, index=True)
    user_id            = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id           = Column(Integer, ForeignKey("skills.id"), nullable=True)
    study_hours        = Column(Float,   default=0.0)
    focus_score        = Column(Float,   default=0.0)   # 0–100
    sleep_hours        = Column(Float,   default=7.0)
    revision_frequency = Column(Integer, default=1)     # sessions per week
    logged_at          = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="study_logs")
