from fastapi import FastAPI, HTTPException, Depends,Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Date, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from contextlib import contextmanager
import bcrypt
from typing import List
from sqlalchemy import or_
from fastapi.responses import JSONResponse
from query3 import query_section
from math import radians, sin, cos, sqrt, atan2

# Database Configuration
DATABASE_URL = "postgresql://postgres:213021181@localhost/bail_reckoner"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI App
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Models
class LegalAidProvider(Base):
    __tablename__ = 'legal_aid_providers'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    dob = Column(Date, nullable=False)
    aadhar_number = Column(String(12), nullable=False)
    designation = Column(String(100), nullable=False)
    license_number = Column(String(50), nullable=False)
    address = Column(Text, nullable=False)
    experience = Column(Integer, nullable=False)
    contact_number = Column(String(15), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    gender = Column(String(10), nullable=False)
    password_hash = Column(Text, nullable=False)
    working_location = Column(String(50), nullable=False)  # Added working_location (Live_Location, Manual_Location, Predefined_Cities)
    legal_fee = Column(Float, nullable=False)  # Added legal_fee (in INR)
    languages_known=Column(String(250),nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class JudicialAuthority(Base):
    __tablename__ = 'judicial_authorities'
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    dob = Column(Date, nullable=False)
    address = Column(Text, nullable=False)
    aadhar_number = Column(String(12), nullable=False)
    contact_number = Column(String(15), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    gender = Column(String(10), nullable=False)
    password_hash = Column(Text, nullable=False)
    designation = Column(String(100), nullable=False)
    license_number = Column(String(50), nullable=False)
    experience = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Prisoner(Base):
    __tablename__ = 'prisoners'
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    dob = Column(Date, nullable=False)
    aadhar_number = Column(String(12), nullable=False)
    gender = Column(String(10), nullable=False)
    phone_number = Column(String(15), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    occupation = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    father_name = Column(String(100), nullable=False)
    father_aadhar = Column(String(12), nullable=False)
    mother_name = Column(String(100), nullable=False)
    mother_aadhar = Column(String(12), nullable=False)
    siblings_name = Column(String(100), nullable=True)
    siblings_aadhar = Column(String(12), nullable=True)
    family_member_designation = Column(String(100), nullable=True)
    case_history = Column(Text, nullable=True)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class OngoingCase(Base):
    __tablename__ = 'ongoing_cases'
    id = Column(Integer, primary_key=True)
    prisoner_id = Column(Integer, nullable=False)
    aadhar_number = Column(String(12), nullable=False)  # Aadhar Number Field Added
    case_number = Column(String(50), nullable=False)
    arrest_conditions = Column(Text, nullable=False)
    charges = Column(Text, nullable=False)
    offense_date = Column(Date, nullable=False)
    arrest_date = Column(Date, nullable=False)
    bail_status = Column(String(20), nullable=False)
    case_status = Column(String(20), nullable=False)
    court_hearing_date = Column(Date, nullable=False)
    legal_aid_provider_id = Column(Integer, nullable=True)
    case_summary = Column(Text, nullable=True)
    evidence_details = Column(Text, nullable=True)
    prisoner_lawyer = Column(String(100), nullable=True)
    suggestions = Column(Text, nullable=True)
    Opinion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
from typing import Optional

class AddOngoingCaseRequest(BaseModel):
    prisoner_id: int
    aadhar_number: str
    case_number: str
    arrest_conditions: str
    charges: str
    offense_date: str
    arrest_date: str
    bail_status: str
    case_status: str
    court_hearing_date: str
    legal_aid_provider_id: Optional[int] = None  # Optional field
    case_summary: Optional[str] = None          # Optional field
    evidence_details: Optional[str] = None      # Optional field


# Pydantic Model for Login Request
class LoginRequest(BaseModel):
    email: str
    password: str
    role: str


# Create Tables
Base.metadata.create_all(bind=engine)


# Utility: Verify Password
def verify_password(plain_password, hashed_password):
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password verification failed: {e}")


# Utility: Context manager for database session
@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()



# Login Endpoint
@app.post("/login")
async def login(data: LoginRequest):
    if not data.email or not data.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    role = data.role.lower()
    email = data.email
    password = data.password

    try:
        with get_session() as session:
            if role == "legal_aid":
                user = session.query(LegalAidProvider).filter_by(email=email).first()
            elif role == "judicial_authority":
                user = session.query(JudicialAuthority).filter_by(email=email).first()
            elif role == "prisoner":
                user = session.query(Prisoner).filter_by(email=email).first()
            else:
                raise HTTPException(status_code=400, detail="Invalid role selected")

            if user and verify_password(password, user.password_hash):
                return {
                    "message": "Login successful",
                    "name": user.full_name,
                    "role": role,
                }
            else:
                raise HTTPException(status_code=401, detail="Invalid email or password")
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

@app.post("/add-ongoing-case")
async def add_ongoing_case(data: AddOngoingCaseRequest):
    try:
        offense_date = datetime.strptime(data.offense_date, "%Y-%m-%d").date()
        arrest_date = datetime.strptime(data.arrest_date, "%Y-%m-%d").date()
        court_hearing_date = datetime.strptime(data.court_hearing_date, "%Y-%m-%d").date()

        with get_session() as session:
            new_case = OngoingCase(
                prisoner_id=data.prisoner_id,
                aadhar_number=data.aadhar_number,
                case_number=data.case_number,
                arrest_conditions=data.arrest_conditions,
                charges=data.charges,
                offense_date=offense_date,
                arrest_date=arrest_date,
                bail_status=data.bail_status,
                case_status=data.case_status,
                court_hearing_date=court_hearing_date,
                legal_aid_provider_id=data.legal_aid_provider_id,
                case_summary=data.case_summary,
                evidence_details=data.evidence_details,
            )
            session.add(new_case)
            session.commit()
            return {"message": "Ongoing case added successfully"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")



@app.get("/validate-aadhar/{aadhar_number}")
def validate_aadhar(aadhar_number: str, role: str):
    # Get the session using the context manager
    with get_session() as db:  # 'db' is the session object
        if role == "prisoner":
            # Check if the Aadhar number exists in the Prisoner table
            prisoner = db.query(Prisoner).filter(Prisoner.aadhar_number == aadhar_number).first()
            if not prisoner:
                raise HTTPException(status_code=400, detail="Aadhar number doesn't match the prisoner record.")
            
            # Fetch the case details for the prisoner
            case = db.query(OngoingCase).filter(OngoingCase.aadhar_number == aadhar_number).first()
            if case:
                
                return {
                    "case_number": case.case_number,
                    "charges": case.charges,
                    "bail_status": case.bail_status,
                    "court_hearing_date": case.court_hearing_date,
                    "case_summary": case.case_summary,
                    "suggestions": case.suggestions,
                    "opinion": case.Opinion,
                    "legal_aid_provider_id": case.legal_aid_provider_id,  # Include the LegalAidProviderID
                }
            
            # No cases found for the provided Aadhar number
            raise HTTPException(status_code=404, detail="No pending cases found for this Aadhar number.")
    
    # If the role is not "prisoner", raise an error
    raise HTTPException(status_code=400, detail="Invalid role for this operation.")




@app.get("/ongoing-cases")
def get_ongoing_cases():
    with get_session() as db:
        cases = db.query(OngoingCase).all()
        return cases



# Completed Case Model
class CompletedCase(Base):
    __tablename__ = 'completed_cases'
    id = Column(Integer, primary_key=True)
    prisoner_id = Column(Integer, nullable=False)
    aadhar_number = Column(String(12), nullable=False)  # Aadhar Number
    case_number = Column(String(50), nullable=False)
    arrest_conditions = Column(Text, nullable=False)
    charges = Column(Text, nullable=False)
    offense_date = Column(Date, nullable=False)
    arrest_date = Column(Date, nullable=False)
    bail_status = Column(String(20), nullable=False)
    case_status = Column(String(20), nullable=False)
    court_hearing_date = Column(Date, nullable=False)
    judgement = Column(Text, nullable=False)  # Judgement Details
    created_at = Column(DateTime, default=datetime.utcnow)


# Pydantic Model for Input Validation
class CompletedCaseRequest(BaseModel):
    prisoner_id: int
    aadhar_number: str
    case_number: str
    arrest_conditions: str
    charges: str
    offense_date: str
    arrest_date: str
    bail_status: str
    case_status: str
    court_hearing_date: str
    judgement: str


# API Endpoint to Add a Completed Case
@app.post("/add-completed-case")
async def add_completed_case(data: CompletedCaseRequest):
    try:
        # Convert date strings to date objects
        offense_date = datetime.strptime(data.offense_date, "%Y-%m-%d").date()
        arrest_date = datetime.strptime(data.arrest_date, "%Y-%m-%d").date()
        court_hearing_date = datetime.strptime(data.court_hearing_date, "%Y-%m-%d").date()

        with get_session() as session:
            completed_case = CompletedCase(
                prisoner_id=data.prisoner_id,
                aadhar_number=data.aadhar_number,
                case_number=data.case_number,
                arrest_conditions=data.arrest_conditions,
                charges=data.charges,
                offense_date=offense_date,
                arrest_date=arrest_date,
                bail_status=data.bail_status,
                case_status=data.case_status,
                court_hearing_date=court_hearing_date,
                judgement=data.judgement,
            )
            session.add(completed_case)
            session.commit()
            return {"message": "Completed case added successfully"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


# API Endpoint to Retrieve Completed Cases
@app.get("/completed-cases")
def get_completed_cases(db: Session = Depends(get_session)):
    try:
        cases = db.query(CompletedCase).all()
        return [
            {
                "id": case.id,
                "prisoner_id": case.prisoner_id,
                "aadhar_number": case.aadhar_number,
                "case_number": case.case_number,
                "arrest_conditions": case.arrest_conditions,
                "charges": case.charges,
                "offense_date": case.offense_date.strftime("%Y-%m-%d"),
                "arrest_date": case.arrest_date.strftime("%Y-%m-%d"),
                "bail_status": case.bail_status,
                "case_status": case.case_status,
                "court_hearing_date": case.court_hearing_date.strftime("%Y-%m-%d"),
                "judgement": case.judgement,
            }
            for case in cases
        ]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

# Endpoint to fetch cases requiring opinion
@app.get("/pending-cases")
async def get_pending_cases():
    # Manually create a database session
    with get_session() as db:
        try:
            # Query to get cases where the legal_aid_provider_id is None
            cases = db.query(OngoingCase).filter(OngoingCase.legal_aid_provider_id == None).all()
            if not cases:
                return []  # Return an empty list if no cases are found

            # Format the case data for the response
            return [
                {
                    "id": case.id,
                    "case_number": case.case_number,
                    "prisoner_id": case.prisoner_id,
                    "aadhar_number": case.aadhar_number,
                    "arrest_conditions": case.arrest_conditions,
                    "charges": case.charges,
                    "offense_date": case.offense_date.strftime('%Y-%m-%d') if case.offense_date else None,
                    "arrest_date": case.arrest_date.strftime('%Y-%m-%d') if case.arrest_date else None,
                    "bail_status": case.bail_status,
                    "case_status": case.case_status,
                    "court_hearing_date": case.court_hearing_date.strftime('%Y-%m-%d') if case.court_hearing_date else None,
                    "case_summary": case.case_summary,
                    "evidence_details": case.evidence_details,
                    "prisoner_lawyer": case.prisoner_lawyer,  # Directly return the value
                    "suggestions": case.suggestions,
                    "opinion": case.Opinion,
                }
                for case in cases
            ]
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/pending-opinions")
def get_pending_opinions():
    with get_session() as db:  # Use `db` directly from the context manager
        cases = db.query(OngoingCase).filter(OngoingCase.Opinion == None).all()
        if not cases:
            return []
        return [
            {
                "id": case.id,
                "prisoner_id": case.prisoner_id,
                "aadhar_number": case.aadhar_number,
                "case_number": case.case_number,
                "arrest_conditions": case.arrest_conditions,
                "charges": case.charges,
                "offense_date": case.offense_date.strftime('%Y-%m-%d') if case.offense_date else None,
                "arrest_date": case.arrest_date.strftime('%Y-%m-%d') if case.arrest_date else None,
                "bail_status": case.bail_status,
                "case_status": case.case_status,
                "court_hearing_date": case.court_hearing_date.strftime('%Y-%m-%d') if case.court_hearing_date else None,
                "legal_aid_provider_id": case.legal_aid_provider_id,
                "case_summary": case.case_summary,
                "evidence_details": case.evidence_details,
                "suggestions": case.suggestions,
                "opinion": case.Opinion,
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


@app.post("/take-up-case/{case_id}")
def take_up_case(case_id: int, payload: dict):
    # Manually create a database session
    with get_session() as db:
        prisoner_lawyer_name = payload.get("prisoner_lawyer")  # The name of the Legal Aid Provider
        license_number = payload.get("license_number")  # License number of the Legal Aid Provider

        # Validate the input data
        if not prisoner_lawyer_name or not license_number:
            raise HTTPException(status_code=422, detail="Both prisoner_lawyer name and license_number are required.")

        # Fetch the Legal Aid Provider by license number to validate existence
        legal_aid_provider = db.query(LegalAidProvider).filter(LegalAidProvider.license_number == license_number).first()

        if not legal_aid_provider:
            raise HTTPException(status_code=404, detail="Legal Aid Provider not found")

        # Retrieve the case by its ID
        case = db.query(OngoingCase).filter(OngoingCase.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Update the case with the Legal Aid Provider's license number and name
        case.legal_aid_provider_id = license_number  # Update with the Legal Aid Provider's license number
        case.prisoner_lawyer = prisoner_lawyer_name  # Update with the Legal Aid Provider's name
        db.commit()  # Commit the changes to the database

    return {"message": "Case taken up successfully by Legal Aid Provider"}

class HistoricalCaseRequest(BaseModel):
    ipcs: List[str]

@app.post("/historical-cases")
def get_historical_cases(request: HistoricalCaseRequest):
    ipcs = request.ipcs
    if not ipcs:
        raise HTTPException(status_code=400, detail="IPCs are required")

    with get_session() as db:  # Use the context manager for session
        # Query the CompletedCase table to find matches
        matching_cases = db.query(CompletedCase).filter(
            or_(
                *[CompletedCase.charges.ilike(f"%{ipc}%") for ipc in ipcs]
            )
        ).all()

        # If no cases match, return a friendly message
        if not matching_cases:
            return {"message": "No historical cases found for the provided IPCs."}

        # Format the results for output
        results = [
            {
                "case_number": case.case_number,
                "prisoner_id": case.prisoner_id,
                "aadhar_number": case.aadhar_number,
                "charges": case.charges,
                "judgement": case.judgement,
                "court_hearing_date": case.court_hearing_date,
            }
            for case in matching_cases
        ]

    return {"matching_cases": results}

@app.post("/get-bail-status")
async def get_bail_status(request: Request):
    try:
        # Extract section from request body
        data = await request.json()
        ipc_section = data.get("charges", "").strip().upper()

        if not ipc_section.startswith("IPC_"):
            return JSONResponse(content={"error": "Invalid IPC section format. Must be IPC_XXX."}, status_code=400)

        # Query the IPC section
        response = query_section(ipc_section)
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
# Create the Database Table
    

@app.get("/ongoing-cases/{aadhar_number}")
def get_ongoing_cases(aadhar_number: str):
    try:
        with get_session() as db:
            # Query the OngoingCase table for the given Aadhar number
            count = db.query(OngoingCase).filter(OngoingCase.aadhar_number == aadhar_number).count()
            return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ongoing cases: {str(e)}")

# Endpoint to fetch the number of completed cases for a given aadhar number
@app.get("/completed-cases/{aadhar_number}")
def get_completed_cases(aadhar_number: str):
    try:
        with get_session() as db:
            # Query the CompletedCase table for the given Aadhar number
            count = db.query(CompletedCase).filter(CompletedCase.aadhar_number == aadhar_number).count()
            return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching completed cases: {str(e)}")

def serialize_case(case):
    """Convert a SQLAlchemy object to a dictionary, excluding _sa_instance_state."""
    return {key: value for key, value in case.__dict__.items() if key != "_sa_instance_state"}

@app.get("/all-cases/{aadhar_number}")
def get_all_cases(aadhar_number: str):
    try:
        with get_session() as db:
            # Fetch ongoing cases
            ongoing_cases = db.query(OngoingCase).filter(OngoingCase.aadhar_number == aadhar_number).all()
            # Fetch completed cases
            completed_cases = db.query(CompletedCase).filter(CompletedCase.aadhar_number == aadhar_number).all()

            # Serialize cases
            result = {
                "ongoing_cases": [serialize_case(case) for case in ongoing_cases],
                "completed_cases": [serialize_case(case) for case in completed_cases]
            }
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cases: {str(e)}")

# Haversine formula to calculate distance between two points on Earth
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

@app.post("/get-nearest-providers")
async def get_nearest_providers(request: Request):
    data = await request.json()
    try:
        latitude = float(data.get("latitude"))
        longitude = float(data.get("longitude"))
        max_fee = float(data.get("maxAdvocateFee", float("inf")))
        min_experience = int(data.get("minExperience", 0))

        with get_session() as session:
            # Fetch providers matching criteria
            providers = (
                session.query(LegalAidProvider)
                .filter(
                    LegalAidProvider.legal_fee <= max_fee,
                    LegalAidProvider.experience >= min_experience
                )
                .all()
            )

            if not providers:
                return []

            provider_distances = []
            for provider in providers:
                try:
                    # Validate and parse working_location
                    if not provider.working_location or ',' not in provider.working_location:
                        print(f"Skipping provider {provider.full_name}: Invalid working_location format")
                        continue

                    provider_lat, provider_lon = map(float, provider.working_location.split(","))
                    distance = calculate_distance(latitude, longitude, provider_lat, provider_lon)
                    provider_distances.append({
                        "name": provider.full_name,
                        "designation": provider.designation,
                        "email": provider.email,
                        "contact_number": provider.contact_number,
                        "fee": provider.legal_fee,
                        "experience": provider.experience,
                        "languages_known": provider.languages_known,
                        "distance": round(distance, 2),
                    })
                except ValueError as e:
                    print(f"Error parsing provider location: {provider.working_location}. Error: {str(e)}")
                    continue

            # Sort by distance
            provider_distances.sort(key=lambda x: x["distance"])
            return provider_distances
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-provider-location/{provider_id}")
async def get_provider_location(provider_id: int):
    with get_session() as session:
        # Query the provider by ID
        provider = session.query(LegalAidProvider).get(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")

        # Parse the 'working_location' field
        try:
            working_location = provider.working_location  # Example: "12.9716,77.5946"
            latitude, longitude = map(float, working_location.split(','))
        except (ValueError, AttributeError):
            raise HTTPException(status_code=400, detail="Invalid working_location format")

        return {
            "latitude": latitude,
            "longitude": longitude
        }
      
# Create the Database Table
Base.metadata.create_all(bind=engine)






