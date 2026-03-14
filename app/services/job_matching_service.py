"""
app/services/job_matching_service.py
--------------------------------------
AI Job Matching Engine — New Feature #1

Compares user's extracted skills against a curated job role registry.
Returns match percentage per role and recommends the best-fit careers.

Algorithm:
  match% = (skills_user_has ∩ skills_role_needs) / skills_role_needs × 100

In a production system the job registry would be fetched from a jobs DB
or a third-party API (LinkedIn, Adzuna, etc.). Here we use a rich static
registry that covers the most common tech careers so the feature works
end-to-end without external dependencies.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.cache import job_match_cache
from app.core.logging import get_logger
from app.models.orm import UserSkillProgress, Skill

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Internal job registry
# Each entry: role title → frozenset of required skill keywords (lowercase)
# ---------------------------------------------------------------------------

JOB_REGISTRY: dict[str, frozenset[str]] = {
    "AI / ML Engineer": frozenset({
        "python", "machine learning", "deep learning", "tensorflow", "pytorch",
        "nlp", "computer vision", "scikit-learn", "numpy", "pandas",
        "neural networks", "transformers", "mlops", "docker",
    }),
    "Data Scientist": frozenset({
        "python", "statistics", "machine learning", "pandas", "numpy",
        "data visualization", "sql", "r", "tableau", "hypothesis testing",
        "scikit-learn", "jupyter",
    }),
    "Data Analyst": frozenset({
        "sql", "excel", "tableau", "power bi", "python", "data visualization",
        "statistics", "business intelligence", "data cleaning", "reporting",
    }),
    "Backend Engineer": frozenset({
        "python", "fastapi", "django", "flask", "sql", "rest api",
        "postgresql", "redis", "docker", "kubernetes", "microservices", "git",
    }),
    "Frontend Engineer": frozenset({
        "javascript", "typescript", "react", "vue", "css", "html",
        "webpack", "rest api", "git", "responsive design", "testing",
    }),
    "Full Stack Engineer": frozenset({
        "javascript", "python", "react", "node.js", "sql", "rest api",
        "docker", "git", "html", "css", "postgresql",
    }),
    "DevOps / SRE Engineer": frozenset({
        "docker", "kubernetes", "ci/cd", "linux", "terraform", "ansible",
        "aws", "gcp", "azure", "monitoring", "bash", "git", "networking",
    }),
    "Cloud Architect": frozenset({
        "aws", "gcp", "azure", "terraform", "kubernetes", "networking",
        "security", "docker", "microservices", "ci/cd", "cost optimisation",
    }),
    "Cybersecurity Analyst": frozenset({
        "networking", "security", "linux", "penetration testing", "siem",
        "incident response", "cryptography", "firewall", "python", "sql",
    }),
    "NLP Engineer": frozenset({
        "python", "nlp", "transformers", "pytorch", "tensorflow", "bert",
        "text classification", "named entity recognition", "hugging face",
        "machine learning", "deep learning",
    }),
    "Product Manager (Tech)": frozenset({
        "product roadmap", "agile", "scrum", "user research", "sql",
        "data analysis", "stakeholder management", "a/b testing", "jira",
    }),
    "Research Scientist (AI)": frozenset({
        "python", "pytorch", "tensorflow", "mathematics", "statistics",
        "deep learning", "reinforcement learning", "paper writing",
        "numerical methods", "linear algebra",
    }),
}


class JobMatchingService:
    """Matches user skill profile to job roles and returns scored recommendations."""

    TOP_N_JOBS = 5          # Maximum jobs returned
    MIN_MATCH_PCT = 10.0    # Filter out near-zero matches

    def get_job_matches(self, db: Session, user_id: int) -> dict:
        """
        1. Load user's skill names from DB (skills with any progress).
        2. Normalise to lowercase set.
        3. Compute intersection ratio against each role in the registry.
        4. Sort, filter, and return top matches.
        """
        cache_key = f"job_matches:{user_id}"
        cached = job_match_cache.get(cache_key)
        if cached is not None:
            logger.debug("Job matches cache HIT for user %d", user_id)
            return cached

        user_skills = self._load_user_skills(db, user_id)
        logger.info("Computing job matches for user %d with %d skills", user_id, len(user_skills))

        matches = []
        for role, required_skills in JOB_REGISTRY.items():
            match_pct = self._compute_match(user_skills, required_skills)
            if match_pct >= self.MIN_MATCH_PCT:
                matched_skills = sorted(user_skills & required_skills)
                missing_skills = sorted(required_skills - user_skills)
                matches.append({
                    "role": role,
                    "match": round(match_pct, 1),
                    "matched_skills": matched_skills[:8],    # top 8 to keep response lean
                    "missing_skills": missing_skills[:6],    # top 6 gaps
                })

        matches.sort(key=lambda x: x["match"], reverse=True)
        top_matches = matches[: self.TOP_N_JOBS]

        result = {
            "user_id": user_id,
            "user_skill_count": len(user_skills),
            "recommended_jobs": top_matches,
            "total_roles_evaluated": len(JOB_REGISTRY),
        }

        job_match_cache.set(cache_key, result)
        return result

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _load_user_skills(db: Session, user_id: int) -> frozenset[str]:
        """Load skill names (lowercased) for a user from user_skill_progress."""
        records = (
            db.query(UserSkillProgress, Skill)
            .join(Skill, UserSkillProgress.skill_id == Skill.id)
            .filter(UserSkillProgress.user_id == user_id)
            .all()
        )
        return frozenset(
            skill.name.lower()
            for _, skill in records
        )

    @staticmethod
    def _compute_match(user_skills: frozenset[str], required_skills: frozenset[str]) -> float:
        if not required_skills:
            return 0.0
        intersection = len(user_skills & required_skills)
        return (intersection / len(required_skills)) * 100
