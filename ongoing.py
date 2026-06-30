from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from extensions import db
from models import OngoingCase
from contextlib import contextmanager

# Create FastAPI instance
app = FastAPI()
#how to run the code
#uvicorn ongoing:app --reload
# Utility: Context manager for database session

@contextmanager
def get_session():
    session = db.session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


# Endpoint to fetch all ongoing cases
@app.get("/ongoing-cases")
async def get_ongoing_cases():
    try:
        with get_session() as session:
            cases = session.query(OngoingCase).all()
            return [
                {
                    "id": case.id,
                    "prisoner_id": case.prisoner_id,
                    "case_number": case.case_number,
                    "charges": case.charges,
                    "bail_status": case.bail_status,
                    "case_status": case.case_status,
                    "Opinion": case.Opinion,
                }
                for case in cases
            ]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


# Endpoint to edit an opinion for a specific case
@app.put("/edit-suggestion/{case_id}")
async def edit_suggestion(case_id: int, suggestion: str, db: Session = Depends(get_session)):
    try:
        with get_session() as session:
            case = session.query(OngoingCase).filter(OngoingCase.id == case_id).first()
            if not case:
                raise HTTPException(status_code=404, detail="Case not found")
            case.Opinion = suggestion
            session.commit()
            return {"message": "Opinion updated successfully"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

# Endpoint to fetch cases requiring opinion
@app.get("/pending-opinions")
async def get_pending_opinions():
    with get_session() as session:
        cases = session.query(OngoingCase).filter(OngoingCase.Opinion == None).all()
        return [
            {
                "id": case.id,
                "case_number": case.case_number,
                "prisoner_id": case.prisoner_id,
                "charges": case.charges,
                "arrest_date": case.arrest_date.isoformat(),
            }
            for case in cases
        ]

# Endpoint to submit opinion
@app.post("/submit-opinion/{case_id}")
async def submit_opinion(case_id: int, opinion: dict):
    with get_session() as session:
        case = session.query(OngoingCase).filter(OngoingCase.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        case.Opinion = opinion.get("opinion")
        session.commit()
        return {"message": "Opinion submitted successfully"}
    
@app.get("/pending-cases")
async def get_pending_cases():
    with get_session() as session:
        cases = session.query(OngoingCase).filter(OngoingCase.legal_aid_provider_id == None).all()
        return [
            {
                "id": case.id,
                "case_number": case.case_number,
                "prisoner_id": case.prisoner_id,
                "charges": case.charges,
                "arrest_date": case.arrest_date.isoformat(),
            }
            for case in cases
        ]

@app.post("/suggestion/{case_id}")
def upsert_suggestion(case_id: int, suggestion: str, db: Session = Depends(get_session)):
    case = db.query(OngoingCase).filter(OngoingCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    case.suggestions = suggestion  # Add or update the suggestion
    db.commit()
    return {"message": "Suggestion added or updated successfully"}