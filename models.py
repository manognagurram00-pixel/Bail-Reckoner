from extensions import db

class LegalAidProvider(db.Model):
    __tablename__ = 'legal_aid_providers'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    aadhar_number = db.Column(db.String(12), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), nullable=False)
    address = db.Column(db.Text, nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    contact_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    working_location = db.Column(db.Text, nullable=False)  # Changed to Text field
    legal_fee = db.Column(db.Float, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    languages_known = db.Column(db.Text, nullable=True)  # New Column
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())



class JudicialAuthority(db.Model):
    __tablename__ = 'judicial_authorities'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    address = db.Column(db.Text, nullable=False)
    aadhar_number = db.Column(db.String(12), nullable=False)
    contact_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Prisoner(db.Model):
    __tablename__ = 'prisoners'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    aadhar_number = db.Column(db.String(12), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    occupation = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    father_name = db.Column(db.String(100), nullable=False)
    father_aadhar = db.Column(db.String(12), nullable=False)
    mother_name = db.Column(db.String(100), nullable=False)
    mother_aadhar = db.Column(db.String(12), nullable=False)
    siblings_name = db.Column(db.String(100), nullable=True)
    siblings_aadhar = db.Column(db.String(12), nullable=True)
    family_member_designation = db.Column(db.String(100), nullable=True)
    case_history = db.Column(db.Text, nullable=True)
    password_hash = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class OngoingCase(db.Model):
    __tablename__ = 'ongoing_cases'
    id = db.Column(db.Integer, primary_key=True)
    prisoner_id = db.Column(db.Integer, nullable=False)
    aadhar_number = db.Column(db.String(12), nullable=False)
    case_number = db.Column(db.String(50), nullable=False)
    arrest_conditions = db.Column(db.Text, nullable=False)
    charges = db.Column(db.Text, nullable=False)
    offense_date = db.Column(db.Date, nullable=False)
    arrest_date = db.Column(db.Date, nullable=False)
    bail_status = db.Column(db.String(20), nullable=False)
    case_status = db.Column(db.String(20), nullable=False)
    court_hearing_date = db.Column(db.Date, nullable=False)
    legal_aid_provider_id = db.Column(db.Integer, nullable=True)
    case_summary = db.Column(db.Text, nullable=True)
    evidence_details = db.Column(db.Text, nullable=True)
    prisoner_lawyer = db.Column(db.String(100), nullable=True) 
    suggestions = db.Column(db.Text, nullable=True)
    Opinion = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class CompletedCase(db.Model):
    __tablename__ = 'completed_cases'
    id = db.Column(db.Integer, primary_key=True)
    prisoner_id = db.Column(db.Integer, nullable=False)
    aadhar_number = db.Column(db.String(12), nullable=False)
    case_number = db.Column(db.String(50), nullable=False)
    arrest_conditions = db.Column(db.Text, nullable=False)
    charges = db.Column(db.Text, nullable=False)
    offense_date = db.Column(db.Date, nullable=False)
    arrest_date = db.Column(db.Date, nullable=False)
    bail_status = db.Column(db.String(20), nullable=False)
    case_status = db.Column(db.String(20), nullable=False)
    court_hearing_date = db.Column(db.Date, nullable=False)
    judgement = db.Column(db.Text, nullable=False)  # Judgement Details
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # Automatically sets creation timestamp

