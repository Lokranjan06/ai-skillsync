"""app/routes/skill_graph.py — GET /api/skill-graph/{career_id}"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.graph_engine import SkillGraphEngine
from app.schemas.schemas import SkillGraphResponse

router = APIRouter()
_engine = SkillGraphEngine()


@router.get("/skill-graph/{career_id}", response_model=SkillGraphResponse)
def get_skill_graph(career_id: int, db: Session = Depends(get_db)):
    """
    Returns a node-link JSON graph of Subject → Skill → Career relationships
    for the specified career. Compatible with D3.js force-directed layouts.
    """
    try:
        return _engine.build_graph(db, career_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph error: {str(e)}")
