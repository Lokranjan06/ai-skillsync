"""
app/services/planner_engine.py
--------------------------------
Adaptive Study Planner — Feature #4

Priority formula:
    priority = (1 - skill_level) × weight × (1 / exam_days_left)

Higher priority = skill is weak, heavily weighted, and the exam is soon.
The engine returns the top-N skills to study, sorted by descending priority.
"""

from sqlalchemy.orm import Session

from app.models.orm import CareerSkill, UserSkillProgress
from app.schemas.schemas import PlannerRequest, PlannerResponse, StudyTask


class PlannerEngine:
    """Generates a ranked, personalised study plan."""

    def generate_plan(self, db: Session, request: PlannerRequest) -> PlannerResponse:
        """
        Steps:
        1. Load all skills required for the target career.
        2. Look up the user's current level for each skill.
        3. Score each skill with the priority formula.
        4. Return the top-N skills with plain-English reasoning.
        """
        career_skills: list[CareerSkill] = (
            db.query(CareerSkill)
            .filter(CareerSkill.career_id == request.career_id)
            .all()
        )
        if not career_skills:
            raise ValueError(f"No skills found for career {request.career_id}")

        # Build look-up: skill_id → level
        progress_records: list[UserSkillProgress] = (
            db.query(UserSkillProgress)
            .filter(UserSkillProgress.user_id == request.user_id)
            .all()
        )
        progress_map: dict[int, float] = {
            p.skill_id: p.skill_level for p in progress_records
        }

        scored: list[tuple[float, CareerSkill, float]] = []

        for cs in career_skills:
            level    = progress_map.get(cs.skill_id, 0.0)
            # Prevent division by zero - use minimum of 1 day
            days_factor = max(1, request.exam_days_left)
            priority = (1 - level) * cs.weight * (1 / days_factor)
            scored.append((priority, cs, level))

        # Sort descending by priority
        scored.sort(key=lambda x: x[0], reverse=True)

        tasks = []
        for priority, cs, level in scored[: request.top_n]:
            tasks.append(
                StudyTask(
                    skill_id=cs.skill_id,
                    skill_name=cs.skill.name,
                    priority=round(priority, 6),
                    skill_level=round(level, 4),
                    weight=cs.weight,
                    reason=self._build_reason(level, cs.weight, request.exam_days_left),
                )
            )

        return PlannerResponse(
            user_id=request.user_id,
            career_id=request.career_id,
            exam_days_left=request.exam_days_left,
            tasks=tasks,
        )

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _build_reason(level: float, weight: float, days: int) -> str:
        parts = []

        if level < 0.2:
            parts.append("skill is largely unpractised")
        elif level < 0.4:
            parts.append("skill is below beginner threshold")
        elif level < 0.75:
            parts.append("skill needs reinforcement")
        else:
            parts.append("skill is near mastery but still weighted highly")

        if weight >= 0.8:
            parts.append("it is critical for the target career")
        elif weight >= 0.5:
            parts.append("it carries significant career weight")

        if days <= 7:
            parts.append("exam is very close — high urgency")
        elif days <= 21:
            parts.append("exam is approaching — moderate urgency")

        return "; ".join(parts).capitalize() + "."
