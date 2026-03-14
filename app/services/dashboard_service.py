"""
app/services/dashboard_service.py
-----------------------------------
Performance Dashboard — Feature #8

Aggregates study_logs for a given user and returns:
  - weekly_hours        : total study hours per ISO calendar week
  - skill_progress      : current mastery level per skill
  - focus_distribution  : histogram of focus scores in four 25-point bands
  - summary stats       : total hours, average focus, total log count
"""

from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.orm import StudyLog, UserSkillProgress, Skill
from app.schemas.schemas import (
    DashboardResponse,
    FocusDistributionEntry,
    SkillProgressEntry,
    WeeklyHourEntry,
)


class DashboardService:
    """Aggregates raw study logs into dashboard metrics."""

    # Focus histogram bucket boundaries (inclusive lower, exclusive upper)
    FOCUS_BANDS = [
        ("0-25",   0,   25),
        ("26-50",  26,  50),
        ("51-75",  51,  75),
        ("76-100", 76, 100),
    ]

    def get_dashboard(self, db: Session, user_id: int) -> DashboardResponse:
        logs: list[StudyLog] = (
            db.query(StudyLog)
            .filter(StudyLog.user_id == user_id)
            .order_by(StudyLog.logged_at)
            .all()
        )

        return DashboardResponse(
            user_id=user_id,
            weekly_hours=self._weekly_hours(logs),
            skill_progress=self._skill_progress(db, user_id),
            focus_distribution=self._focus_distribution(logs),
            total_study_hours=round(sum(l.study_hours for l in logs), 2),
            avg_focus_score=self._avg_focus(logs),
            log_count=len(logs),
        )

    # -----------------------------------------------------------------------
    # Aggregation helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _weekly_hours(logs: list[StudyLog]) -> list[WeeklyHourEntry]:
        """Group study hours by ISO year-week string (e.g. '2024-W12')."""
        week_map: dict[str, float] = defaultdict(float)

        for log in logs:
            dt: datetime = log.logged_at or datetime.utcnow()
            iso_year, iso_week, _ = dt.isocalendar()
            key = f"{iso_year}-W{iso_week:02d}"
            week_map[key] += log.study_hours

        return [
            WeeklyHourEntry(week=week, hours=round(hours, 2))
            for week, hours in sorted(week_map.items())
        ]

    @staticmethod
    def _skill_progress(db: Session, user_id: int) -> list[SkillProgressEntry]:
        """Current skill levels from user_skill_progress joined with skills."""
        records: list[UserSkillProgress] = (
            db.query(UserSkillProgress)
            .filter(UserSkillProgress.user_id == user_id)
            .all()
        )
        return [
            SkillProgressEntry(
                skill_name=r.skill.name,
                skill_level=round(r.skill_level, 4),
            )
            for r in records
        ]

    def _focus_distribution(self, logs: list[StudyLog]) -> list[FocusDistributionEntry]:
        """Count logs falling into each 25-point focus band."""
        counts: dict[str, int] = {band[0]: 0 for band in self.FOCUS_BANDS}

        for log in logs:
            score = log.focus_score or 0
            for label, lo, hi in self.FOCUS_BANDS:
                if lo <= score <= hi:
                    counts[label] += 1
                    break

        return [
            FocusDistributionEntry(range=label, count=counts[label])
            for label, _, __ in self.FOCUS_BANDS
        ]

    @staticmethod
    def _avg_focus(logs: list[StudyLog]) -> float:
        if not logs:
            return 0.0
        return round(sum(l.focus_score for l in logs) / len(logs), 2)
