"""
app/services/scoring_engine.py
--------------------------------
Scoring Engine — Features #2 & #3

Feature 2 — Career Readiness Score:
    readiness = Σ(skill_progress × skill_weight) / Σ(skill_weight)

Feature 3 — Skill Gap Detection:
    strong  : skill_level > 0.75
    weak    : 0.4 ≤ skill_level ≤ 0.75
    missing : skill_level < 0.4  (or no progress record at all)
"""

from sqlalchemy.orm import Session

from app.models.orm import Career, CareerSkill, UserSkillProgress
from app.schemas.schemas import (
    ReadinessResponse,
    SkillGapItem,
    SkillGapResponse,
)


class ScoringEngine:
    """Computes readiness scores and skill gap breakdowns."""

    # Thresholds for skill classification
    STRONG_THRESHOLD  = 0.75
    WEAK_LOWER_BOUND  = 0.40

    # -----------------------------------------------------------------------
    # Helper: fetch career skills + user progress in one pass
    # -----------------------------------------------------------------------

    def _get_career_skills_with_progress(
        self,
        db: Session,
        user_id: int,
        career_id: int,
    ) -> tuple[Career, list[tuple[CareerSkill, float]]]:
        """
        Returns (career, [(career_skill, user_level), ...]).
        user_level defaults to 0.0 when no progress record exists.
        """
        career: Career | None = db.query(Career).filter(Career.id == career_id).first()
        if career is None:
            raise ValueError(f"Career {career_id} not found")

        career_skills: list[CareerSkill] = (
            db.query(CareerSkill)
            .filter(CareerSkill.career_id == career_id)
            .all()
        )
        if not career_skills:
            raise ValueError(f"Career {career_id} has no associated skills")

        # Index user progress by skill_id for O(1) look-up
        progress_records: list[UserSkillProgress] = (
            db.query(UserSkillProgress)
            .filter(UserSkillProgress.user_id == user_id)
            .all()
        )
        progress_map: dict[int, float] = {
            p.skill_id: p.skill_level for p in progress_records
        }

        pairs = [
            (cs, progress_map.get(cs.skill_id, 0.0))
            for cs in career_skills
        ]
        return career, pairs

    # -----------------------------------------------------------------------
    # Feature 2: Readiness score
    # -----------------------------------------------------------------------

    def compute_readiness(
        self,
        db: Session,
        user_id: int,
        career_id: int,
    ) -> ReadinessResponse:
        """Weighted average of (skill_level × weight) across all career skills."""
        career, pairs = self._get_career_skills_with_progress(db, user_id, career_id)

        total_weight    = sum(cs.weight for cs, _ in pairs)
        weighted_sum    = sum(level * cs.weight for cs, level in pairs)

        readiness = weighted_sum / total_weight if total_weight > 0 else 0.0
        readiness = round(min(max(readiness, 0.0), 1.0), 4)

        return ReadinessResponse(
            user_id=user_id,
            career_id=career_id,
            career_title=career.title,
            readiness_score=readiness,
            percentage=round(readiness * 100, 2),
            skills_assessed=len(pairs),
        )

    # -----------------------------------------------------------------------
    # Feature 3: Skill gap detection
    # -----------------------------------------------------------------------

    def compute_skill_gap(
        self,
        db: Session,
        user_id: int,
        career_id: int,
    ) -> SkillGapResponse:
        """Classify each career skill into strong / weak / missing buckets."""
        _, pairs = self._get_career_skills_with_progress(db, user_id, career_id)

        strong, weak, missing = [], [], []

        for cs, level in pairs:
            item = SkillGapItem(
                skill_id=cs.skill_id,
                skill_name=cs.skill.name,
                skill_level=round(level, 4),
                weight=cs.weight,
                category=self._classify(level),
            )
            if item.category == "strong":
                strong.append(item)
            elif item.category == "weak":
                weak.append(item)
            else:
                missing.append(item)

        return SkillGapResponse(
            user_id=user_id,
            career_id=career_id,
            strong=strong,
            weak=weak,
            missing=missing,
            summary={"strong": len(strong), "weak": len(weak), "missing": len(missing)},
        )

    def _classify(self, level: float) -> str:
        if level > self.STRONG_THRESHOLD:
            return "strong"
        if level >= self.WEAK_LOWER_BOUND:
            return "weak"
        return "missing"
