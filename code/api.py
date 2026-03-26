from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from search_engine import SearchEngine, SearchMode
from llm_client import LLMClient
from session_manager import SessionManager

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI(
    title="Legal AI RAG API",
    description="REST API for Hybrid Legal Retrieval and Gemini-powered Synthesis",
    version="1.0.0"
)

# Initialize Core Services
engine = SearchEngine()
llm = LLMClient()
sessions = SessionManager(sessions_dir=str(Path(__file__).parent.parent / "sessions"))

# Pydantic Models
class SearchQuery(BaseModel):
    query: str
    limit: int = 5
    mode: str = "hybrid"

class ChatQuery(BaseModel):
    query: str
    session_id: Optional[str] = None
    limit: int = 5

class CaseResponse(BaseModel):
    case_id: str
    title: str
    year: int
    court: Optional[str]
    full_text: Optional[str]
    score: float

@app.get("/")
async def root():
    return {"message": "Legal AI Backend is online", "status": "active"}

@app.post("/search", response_model=List[Dict[str, Any]])
async def search_cases(query: SearchQuery):
    """Perform hybrid search for legal precedents."""
    try:
        mode_map = {
            "keyword": SearchMode.KEYWORD_ONLY,
            "semantic": SearchMode.SEMANTIC_ONLY,
            "graph": SearchMode.GRAPH_ONLY,
            "hybrid": SearchMode.HYBRID,
            "ultra": SearchMode.ULTRA
        }
        search_mode = mode_map.get(query.mode.lower(), SearchMode.HYBRID)
        
        results = engine.search(query.query, limit=query.limit, mode=search_mode)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_consultation(query: ChatQuery):
    """Get legal advice grounded in retrieved precedents."""
    try:
        # 1. Handle Session
        if query.session_id:
            sessions.load_session(query.session_id)
        else:
            sessions.start_new_session()
            
        # 2. Search
        results = engine.search(query.query, limit=query.limit, mode=SearchMode.HYBRID)
        if not results:
            return {"answer": "No relevant precedents found.", "session_id": sessions.current_session_id, "precedents": []}
            
        # 3. Prepare Context
        context_docs = [
            {'title': res['title'], 'text': res.get('text_content', '')}
            for res in results
        ]
        
        # 4. Generate Answer
        answer = llm.generate_answer(query.query, context_docs, history=sessions.history)
        
        # 5. Update Session
        sessions.add_message("user", query.query)
        sessions.add_message("assistant", answer, metadata={"precedents": [r['title'] for r in results]})
        
        return {
            "answer": answer,
            "session_id": sessions.current_session_id,
            "precedents": [
                {"id": r['case_id'], "title": r['title'], "year": r['year'], "score": r['score']}
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/brief/{case_id}")
async def generate_case_brief(case_id: str):
    """Generate a structured IRAC case brief for a specific judgment."""
    try:
        # 1. Fetch Case
        case = engine.storage.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
            
        # 2. Get body text
        case_text = case.get('full_text') or ""
        if not case_text and case.get('file_path'):
            # Fallback to file system if not in DB yet
            full_text_path = Path(__file__).parent.parent / "data" / "full_texts" / f"{case_id}.txt"
            if full_text_path.exists():
                case_text = full_text_path.read_text(encoding='utf-8', errors='ignore')

        if not case_text:
             raise HTTPException(status_code=400, detail="Judgment body not available for briefing")

        # 3. Generate Brief
        brief = llm.generate_case_brief(case, case_text)
        return {"case_id": case_id, "title": case['title'], "brief": brief}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
async def list_sessions():
    """List recent conversation sessions."""
    return sessions.list_sessions()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
