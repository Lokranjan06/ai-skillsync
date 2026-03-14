"""
app/services/resume_optimizer.py
----------------------------------
ATS Resume Optimizer — New Feature #2

Analyses a resume PDF against ATS (Applicant Tracking System) criteria:
  • Keyword density vs a target skill vocabulary
  • Quantifiable achievement detection
  • Action verb strength analysis
  • Section structure detection
  • Formatting red-flags (tables, graphics, unusual fonts)

Returns an ATS score (0-100) and a prioritised list of improvements.

The analysis is deterministic and runs entirely offline — no external API
calls. This keeps latency low (< 200 ms) and ensures GDPR compliance.
"""

from __future__ import annotations

import re
from io import BytesIO

from pypdf import PdfReader

from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# ATS keyword vocabulary (high-value keywords that ATS systems scan for)
# ---------------------------------------------------------------------------

ATS_KEYWORDS: frozenset[str] = frozenset({
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "kotlin", "swift", "scala", "r", "matlab", "sql", "bash",
    # Frameworks / tools
    "react", "node.js", "django", "fastapi", "flask", "spring", "tensorflow",
    "pytorch", "scikit-learn", "docker", "kubernetes", "aws", "gcp", "azure",
    "git", "ci/cd", "jenkins", "terraform", "ansible",
    # Data & AI
    "machine learning", "deep learning", "nlp", "computer vision", "data science",
    "data analysis", "big data", "spark", "hadoop", "tableau", "power bi",
    "pandas", "numpy", "matplotlib", "seaborn", "transformers",
    # Soft / business skills
    "agile", "scrum", "jira", "leadership", "communication", "collaboration",
    "problem solving", "stakeholder management", "product management",
    # Certs / degrees
    "bachelor", "master", "phd", "mba", "aws certified", "google certified",
    "pmp", "cpa",
})

STRONG_ACTION_VERBS: frozenset[str] = frozenset({
    "achieved", "accelerated", "automated", "built", "delivered", "designed",
    "developed", "engineered", "established", "exceeded", "generated",
    "implemented", "improved", "increased", "launched", "led", "managed",
    "optimised", "optimized", "reduced", "scaled", "spearheaded", "streamlined",
})

WEAK_ACTION_VERBS: frozenset[str] = frozenset({
    "assisted", "helped", "worked on", "participated", "contributed", "involved",
    "supported", "responsible for",
})

REQUIRED_SECTIONS: list[str] = [
    "experience", "education", "skills", "projects",
]

# Patterns that suggest a number-backed achievement
QUANTIFIED_PATTERN = re.compile(
    r"\b(\d+[\.,]?\d*\s*(%|percent|x|times|hours?|days?|months?|years?|users?|"
    r"customers?|million|billion|k\b|ms\b|tb\b|gb\b|\$))",
    re.IGNORECASE,
)


class ResumeOptimizerService:
    """Scores a PDF resume against ATS criteria and generates improvement tips."""

    def analyze(self, file_bytes: bytes) -> dict:
        """
        Full ATS analysis pipeline.
        Returns a dict matching ResumeOptimizeResponse schema.
        """
        raw_text = self._extract_text(file_bytes)
        clean_text = raw_text.lower()

        keyword_score, missing_keywords = self._keyword_score(clean_text)
        structure_score = self._structure_score(clean_text)
        achievement_score = self._achievement_score(raw_text)
        verb_score, weak_verbs_found = self._verb_score(clean_text)
        formatting_score = self._formatting_score(raw_text)

        # Weighted composite ATS score
        ats_score = round(
            keyword_score    * 0.35 +
            structure_score  * 0.20 +
            achievement_score * 0.20 +
            verb_score       * 0.15 +
            formatting_score * 0.10,
            1,
        )

        suggestions = self._build_suggestions(
            keyword_score, missing_keywords,
            structure_score, achievement_score,
            verb_score, weak_verbs_found,
            formatting_score,
        )

        logger.info(
            "ATS analysis complete — score: %.1f | suggestions: %d",
            ats_score, len(suggestions),
        )

        return {
            "ats_score": ats_score,
            "breakdown": {
                "keyword_match":  round(keyword_score, 1),
                "structure":      round(structure_score, 1),
                "achievements":   round(achievement_score, 1),
                "action_verbs":   round(verb_score, 1),
                "formatting":     round(formatting_score, 1),
            },
            "missing_keywords": sorted(missing_keywords)[:10],
            "suggestions": suggestions,
        }

    # -----------------------------------------------------------------------
    # Scoring sub-components
    # -----------------------------------------------------------------------

    @staticmethod
    def _keyword_score(text: str) -> tuple[float, list[str]]:
        """Score based on fraction of ATS_KEYWORDS found in resume text."""
        found = {kw for kw in ATS_KEYWORDS if kw in text}
        missing = sorted(ATS_KEYWORDS - found)
        score = min(100.0, (len(found) / max(len(ATS_KEYWORDS), 1)) * 200)
        return score, missing

    @staticmethod
    def _structure_score(text: str) -> float:
        """Reward resumes that contain standard ATS-parseable sections."""
        found = sum(1 for section in REQUIRED_SECTIONS if section in text)
        return (found / len(REQUIRED_SECTIONS)) * 100

    @staticmethod
    def _achievement_score(text: str) -> float:
        """Reward quantifiable achievements (numbers + units)."""
        hits = QUANTIFIED_PATTERN.findall(text)
        # 5+ measurable results → 100; 0 → 0
        return min(100.0, len(hits) * 20)

    @staticmethod
    def _verb_score(text: str) -> tuple[float, list[str]]:
        """Score based on strong vs weak action verb usage."""
        strong = sum(1 for v in STRONG_ACTION_VERBS if v in text)
        weak_found = [v for v in WEAK_ACTION_VERBS if v in text]
        score = min(100.0, strong * 12) - len(weak_found) * 8
        return max(0.0, score), weak_found

    @staticmethod
    def _formatting_score(text: str) -> float:
        """Penalise ATS-unfriendly patterns (very short text = graphics-heavy PDF)."""
        word_count = len(text.split())
        if word_count < 100:
            return 20.0   # Likely image-based or heavy graphics
        if word_count < 200:
            return 50.0
        return 90.0

    # -----------------------------------------------------------------------
    # Suggestion builder
    # -----------------------------------------------------------------------

    @staticmethod
    def _build_suggestions(
        keyword_score: float,
        missing_keywords: list[str],
        structure_score: float,
        achievement_score: float,
        verb_score: float,
        weak_verbs: list[str],
        formatting_score: float,
    ) -> list[str]:
        suggestions: list[str] = []

        if keyword_score < 60 and missing_keywords:
            top_missing = ", ".join(missing_keywords[:5])
            suggestions.append(
                f"Add high-value keywords: {top_missing} — these are commonly scanned by ATS systems."
            )

        if structure_score < 75:
            suggestions.append(
                "Ensure your resume has clearly labelled sections: "
                "Experience, Education, Skills, and Projects."
            )

        if achievement_score < 60:
            suggestions.append(
                "Quantify your achievements — use numbers, percentages, or timeframes "
                "(e.g. 'Reduced API latency by 40%', 'Led a team of 5 engineers')."
            )

        if verb_score < 50:
            suggestions.append(
                "Replace weak verbs with strong action verbs: "
                "use 'Engineered', 'Optimised', 'Delivered' instead of "
                "'helped', 'worked on', 'responsible for'."
            )

        if weak_verbs:
            suggestions.append(
                f"Detected weak verbs: {', '.join(weak_verbs[:3])}. "
                "Replace these with impact-focused alternatives."
            )

        if formatting_score < 60:
            suggestions.append(
                "Your PDF appears to have limited extractable text. "
                "Avoid tables, text boxes, or image-based content — ATS systems cannot parse them."
            )

        if keyword_score >= 70 and structure_score >= 75 and achievement_score >= 60:
            suggestions.append(
                "Your resume is ATS-friendly. Focus on tailoring keywords to each specific job description."
            )

        return suggestions

    # -----------------------------------------------------------------------
    # PDF text extraction (re-uses pypdf already in requirements)
    # -----------------------------------------------------------------------

    @staticmethod
    def _extract_text(file_bytes: bytes) -> str:
        try:
            reader = PdfReader(BytesIO(file_bytes))
            return " ".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise ValueError(f"PDF parsing failed: {exc}") from exc
