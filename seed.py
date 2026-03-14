"""
scripts/seed.py
----------------
Populates the database with realistic seed data for development and demos.

Run with:
    python scripts/seed.py

Creates:
  - 3 subjects
  - 10 skills (with resume keywords)
  - 3 careers
  - career_skills junction rows with weights
  - 2 users
  - user_skill_progress records
  - study_logs for the past 4 weeks
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Make sure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database.session import engine, Base, SessionLocal
from app.models.orm import (
    User, Subject, Skill, Career, CareerSkill,
    UserSkillProgress, StudyLog,
)


def seed():
    # -----------------------------------------------------------------------
    # Ensure all tables exist
    # -----------------------------------------------------------------------
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        _seed_all(db)
        db.commit()
        print("[OK]  Database seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"[X]  Seeding failed: {e}")
        raise
    finally:
        db.close()


def _seed_all(db):
    # ------------------------------------------------------------------
    # Subjects
    # ------------------------------------------------------------------
    subjects = {
        "CS":   Subject(name="Computer Science"),
        "Math": Subject(name="Mathematics"),
        "Data": Subject(name="Data Science"),
    }
    for s in subjects.values():
        db.add(s)
    db.flush()

    # ------------------------------------------------------------------
    # Skills  (name + comma-separated resume keywords)
    # ------------------------------------------------------------------
    skills_data = [
        ("Python",           subjects["CS"],   "python,py,django,flask,fastapi"),
        ("SQL",              subjects["CS"],   "sql,mysql,postgresql,postgres,sqlite,database"),
        ("Machine Learning", subjects["Data"], "ml,machine learning,sklearn,scikit,xgboost,model"),
        ("Statistics",       subjects["Math"], "statistics,stats,probability,hypothesis,regression"),
        ("Data Wrangling",   subjects["Data"], "pandas,numpy,data cleaning,etl,wrangling"),
        ("Linear Algebra",   subjects["Math"], "linear algebra,matrix,vectors,eigenvalue"),
        ("System Design",    subjects["CS"],   "system design,architecture,microservices,api design"),
        ("Deep Learning",    subjects["Data"], "deep learning,neural network,tensorflow,pytorch,keras"),
        ("Cloud & DevOps",   subjects["CS"],   "aws,gcp,azure,docker,kubernetes,ci/cd,devops"),
        ("Data Visualisation", subjects["Data"], "matplotlib,seaborn,tableau,power bi,plotly,visualization"),
    ]

    skills = {}
    for name, subject, keywords in skills_data:
        skill = Skill(name=name, subject_id=subject.id, keywords=keywords)
        db.add(skill)
        skills[name] = skill
    db.flush()

    # ------------------------------------------------------------------
    # Careers
    # ------------------------------------------------------------------
    careers = {
        "DS":  Career(title="Data Scientist",       description="Builds ML models and derives insights from data."),
        "BE":  Career(title="Backend Engineer",      description="Designs and implements server-side systems and APIs."),
        "MLE": Career(title="ML Engineer",           description="Deploys and scales machine learning models in production."),
    }
    for c in careers.values():
        db.add(c)
    db.flush()

    # ------------------------------------------------------------------
    # CareerSkills  (weight reflects how critical each skill is)
    # ------------------------------------------------------------------
    career_skills_map = [
        # Data Scientist
        (careers["DS"],  skills["Python"],           0.9),
        (careers["DS"],  skills["Machine Learning"],  1.0),
        (careers["DS"],  skills["Statistics"],        0.9),
        (careers["DS"],  skills["Data Wrangling"],    0.8),
        (careers["DS"],  skills["SQL"],               0.7),
        (careers["DS"],  skills["Data Visualisation"],0.6),
        (careers["DS"],  skills["Linear Algebra"],    0.6),
        # Backend Engineer
        (careers["BE"],  skills["Python"],            1.0),
        (careers["BE"],  skills["SQL"],               0.9),
        (careers["BE"],  skills["System Design"],     1.0),
        (careers["BE"],  skills["Cloud & DevOps"],    0.8),
        # ML Engineer
        (careers["MLE"], skills["Python"],            1.0),
        (careers["MLE"], skills["Machine Learning"],  1.0),
        (careers["MLE"], skills["Deep Learning"],     0.9),
        (careers["MLE"], skills["Cloud & DevOps"],    0.9),
        (careers["MLE"], skills["System Design"],     0.7),
        (careers["MLE"], skills["Linear Algebra"],    0.7),
    ]
    for career, skill, weight in career_skills_map:
        db.add(CareerSkill(career_id=career.id, skill_id=skill.id, weight=weight))
    db.flush()

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    users = [
        User(name="Alex Rivera",  email="alex@skillsync.dev"),
        User(name="Priya Sharma", email="priya@skillsync.dev"),
    ]
    for u in users:
        db.add(u)
    db.flush()

    # ------------------------------------------------------------------
    # UserSkillProgress  — Alex is mid-level Data Scientist candidate
    # ------------------------------------------------------------------
    alex_progress = [
        (skills["Python"],           0.80),
        (skills["Machine Learning"],  0.55),
        (skills["Statistics"],        0.60),
        (skills["Data Wrangling"],    0.70),
        (skills["SQL"],               0.50),
        (skills["Data Visualisation"],0.45),
        (skills["Linear Algebra"],    0.30),
    ]
    for skill, level in alex_progress:
        db.add(UserSkillProgress(user_id=users[0].id, skill_id=skill.id, skill_level=level))

    # Priya is an early-stage Backend Engineer candidate
    priya_progress = [
        (skills["Python"],      0.40),
        (skills["SQL"],         0.35),
        (skills["System Design"], 0.20),
        (skills["Cloud & DevOps"], 0.15),
    ]
    for skill, level in priya_progress:
        db.add(UserSkillProgress(user_id=users[1].id, skill_id=skill.id, skill_level=level))
    db.flush()

    # ------------------------------------------------------------------
    # StudyLogs  — 28 days of logs for Alex
    # ------------------------------------------------------------------
    rng = random.Random(99)
    base_date = datetime.utcnow() - timedelta(days=28)

    for day in range(28):
        log_date = base_date + timedelta(days=day)
        db.add(StudyLog(
            user_id=users[0].id,
            skill_id=rng.choice(list(skills.values())).id,
            study_hours=rng.uniform(1.0, 5.0),
            focus_score=rng.uniform(40, 95),
            sleep_hours=rng.uniform(5.5, 8.5),
            revision_frequency=rng.randint(1, 5),
            logged_at=log_date,
        ))

    # A few logs for Priya
    for day in range(10):
        log_date = base_date + timedelta(days=day * 2)
        db.add(StudyLog(
            user_id=users[1].id,
            skill_id=rng.choice(list(skills.values())).id,
            study_hours=rng.uniform(0.5, 3.0),
            focus_score=rng.uniform(30, 80),
            sleep_hours=rng.uniform(6.0, 9.0),
            revision_frequency=rng.randint(1, 3),
            logged_at=log_date,
        ))

    print("   • Subjects:         ", len(subjects))
    print("   • Skills:           ", len(skills))
    print("   • Careers:          ", len(careers))
    print("   • CareerSkills:     ", len(career_skills_map))
    print("   • Users:            ", len(users))
    print("   • StudyLogs:        ", 38)


if __name__ == "__main__":
    seed()
