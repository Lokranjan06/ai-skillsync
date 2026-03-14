"""
app/services/resume_extractor.py
----------------------------------
Resume Skill Extractor — Feature #5

Pipeline:
1. Accept an uploaded PDF file (bytes).
2. Extract raw text using pypdf.
3. Normalise text: lowercase, remove punctuation.
4. For every skill in the database, check whether any of its keywords
   appear in the normalised resume text.
5. Return matched skills with the specific keywords that triggered the match.
"""

import re

from pypdf import PdfReader
from io import BytesIO

from sqlalchemy.orm import Session

from app.models.orm import Skill
from app.schemas.schemas import ResumeExtractResponse, ResumeSkillMatch


class ResumeExtractor:
    """Extracts and matches skills from a PDF résumé."""

    def extract(
        self,
        db: Session,
        file_bytes: bytes,
        filename: str,
    ) -> ResumeExtractResponse:
        # --- Step 1: PDF → text -------------------------------------------
        raw_text   = self._pdf_to_text(file_bytes)
        clean_text = self._normalise(raw_text)

        # --- Step 2: Load all skills from DB --------------------------------
        skills: list[Skill] = db.query(Skill).all()

        # --- Step 3: Match skills against resume text -----------------------
        matched: list[ResumeSkillMatch] = []

        for skill in skills:
            keywords = self._parse_keywords(skill)
            hits = [kw for kw in keywords if kw in clean_text]
            if hits:
                matched.append(
                    ResumeSkillMatch(
                        skill_id=skill.id,
                        skill_name=skill.name,
                        matched_keywords=hits,
                    )
                )

        coverage = round(len(matched) / len(skills) * 100, 2) if skills else 0.0

        return ResumeExtractResponse(
            filename=filename,
            total_skills_in_db=len(skills),
            matched_skills=matched,
            match_count=len(matched),
            coverage_pct=coverage,
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _pdf_to_text(file_bytes: bytes) -> str:
        """Extract all text from all pages of a PDF."""
        try:
            reader = PdfReader(BytesIO(file_bytes))
            pages  = [page.extract_text() or "" for page in reader.pages]
            return " ".join(pages)
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")

    @staticmethod
    def _normalise(text: str) -> str:
        """Lowercase and strip punctuation for robust keyword matching."""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s\+#]", " ", text)  # keep + and # (C++, C#)
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def _parse_keywords(skill: Skill) -> list[str]:
        """
        Build keyword list from:
        - The skill name itself (lowercased)
        - The comma-separated keywords column
        """
        base = [skill.name.lower()]
        extras = [
            kw.strip().lower()
            for kw in (skill.keywords or "").split(",")
            if kw.strip()
        ]
        return list(set(base + extras))
