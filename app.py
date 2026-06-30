from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from extensions import db, bcrypt
from models import LegalAidProvider, JudicialAuthority, Prisoner, OngoingCase, CompletedCase
import logging
from datetime import datetime


# Initialize logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:213021181@localhost/bail_reckoner'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/undertrial_prisoner', methods=['POST'])
def undertrial_prisoner():
    try:
        if not request.is_json:
            app.logger.error("Invalid JSON input")
            return jsonify({"error": "Invalid JSON input"}), 400

        data = request.get_json()
        app.logger.info(f"Received data: {data}")

        # Validate required fields
        required_fields = [
            "prisoner_id", "case_number", "arrest_conditions", "charges",
            "offense_date", "arrest_date", "bail_status", "case_status",
            "court_hearing_date"
        ]
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            app.logger.error(f"Missing fields: {missing_fields}")
            return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

        # Validate date format
        for date_field in ['offense_date', 'arrest_date', 'court_hearing_date']:
            try:
                datetime.strptime(data[date_field], '%Y-%m-%d')
            except ValueError:
                app.logger.error(f"Invalid date format for {date_field}: {data[date_field]}")
                return jsonify({"error": f"Invalid date format for {date_field}. Use YYYY-MM-DD"}), 400

        # Add ongoing case to database
        new_case = OngoingCase(
            prisoner_id=data['prisoner_id'],
            case_number=data['case_number'],
            arrest_conditions=data['arrest_conditions'],
            charges=data['charges'],
            offense_date=data['offense_date'],
            arrest_date=data['arrest_date'],
            bail_status=data['bail_status'],
            case_status=data['case_status'],
            court_hearing_date=data['court_hearing_date'],
            legal_aid_provider_id=data.get('legal_aid_provider_id'),
            case_summary=data.get('case_summary'),
            evidence_details=data.get('evidence_details'),
        )
        db.session.add(new_case)
        db.session.commit()

        app.logger.info("Ongoing case added successfully")
        return jsonify({"message": "Ongoing case added successfully!"}), 201

    except Exception as e:
        app.logger.error(f"Error adding ongoing case: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/bail_status/<prisoner_id>', methods=['GET'])
def get_bail_status(prisoner_id):
    try:
        # Validate prisoner_id as an integer
        if not prisoner_id.isdigit():
            return jsonify({"message": "Invalid Prisoner ID. It must be a number."}), 400

        case = OngoingCase.query.filter_by(prisoner_id=int(prisoner_id)).first()
        if not case:
            return jsonify({"message": f"No ongoing case found for Prisoner ID: {prisoner_id}"}), 404

        return jsonify({"bail_status": case.bail_status}), 200
    except Exception as e:
        app.logger.error(f"Error fetching bail status: {e}")
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        app.logger.info(f"Received registration data: {data}")

        role = data.get('role', '').lower()

        # Map role values to standard names
        role_mapping = {
            'legalaid': 'legal_aid',
            'legal_aid': 'legal_aid',
            'judicialauthority': 'judicial_authority',
            'judicial_authority': 'judicial_authority',
            'judicial': 'judicial_authority',
            'prisoner': 'prisoner'
        }

        # Validate and map role
        standardized_role = role_mapping.get(role)
        if not standardized_role:
            app.logger.error(f"Invalid role specified: {role}")
            return jsonify({"message": f"Invalid role: {role}. Must be 'legal_aid', 'judicial_authority', or 'prisoner'"}), 400


        # Hash the password
        password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')

        # Role-specific registration logic
        if standardized_role == 'legal_aid':
            if LegalAidProvider.query.filter_by(email=data['email']).first():
                return jsonify({"message": "Email already registered"}), 400
            if not data.get('aadhar_number'):
                return jsonify({"message": "Aadhar number is required for Legal Aid Providers"}), 400
            
            working_location = data.get("working_location")
            app.logger.info(f"Working location received: {working_location}")

            if not working_location:
                return jsonify({"message": "Working location is required for Legal Aid Providers."}), 400

            try:
            # Validate the latitude and longitude format
                latitude, longitude = map(float, working_location.split(","))
                if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                    raise ValueError("Invalid latitude or longitude range")
            except ValueError:
                return jsonify({"message": "Invalid working location format. Expected 'latitude,longitude'."}), 400
    
            languages_known = data.get('languages_known', '')
            new_legal_aid = LegalAidProvider(
                full_name=data['full_name'],
                dob=data['dob'],
                aadhar_number=data['aadhar_number'],
                designation=data['designation'],
                license_number=data['license_number'],
                address=data['address'],
                experience=data['experience'],
                contact_number=data['contact_number'],
                email=data['email'],
                gender=data['gender'],
                working_location=working_location,  # New field
                legal_fee=float(data.get('legal_fee', 0)),      # New field
                languages_known=languages_known,
                password_hash=password_hash
            )
            db.session.add(new_legal_aid)

        elif standardized_role == 'judicial_authority':
            if JudicialAuthority.query.filter_by(email=data['email']).first():
                return jsonify({"message": "Email already registered"}), 400

            new_judicial = JudicialAuthority(
                full_name=data['full_name'],
                dob=data['dob'],
                address=data['address'],
                aadhar_number=data['aadhar_number'],
                contact_number=data['contact_number'],
                email=data['email'],
                gender=data['gender'],
                password_hash=password_hash,
                designation=data['designation'],
                license_number=data['license_number'],
                experience=data['experience']
            )
            db.session.add(new_judicial)

        elif standardized_role == 'prisoner':
            if Prisoner.query.filter_by(email=data['email']).first():
                return jsonify({"message": "Email already registered"}), 400

            new_prisoner = Prisoner(
                full_name=data['full_name'],
                dob=data['dob'],
                aadhar_number=data['aadhar_number'],
                gender=data['gender'],
                phone_number=data['phone_number'],
                email=data['email'],
                occupation=data['occupation'],
                address=data['address'],
                father_name=data['father_name'],
                father_aadhar=data['father_aadhar'],
                mother_name=data['mother_name'],
                mother_aadhar=data['mother_aadhar'],
                siblings_name=data.get('siblings_name'),
                siblings_aadhar=data.get('siblings_aadhar'),
                family_member_designation=data.get('family_member_designation'),
                case_history=data.get('case_history'),
                password_hash=password_hash
            )
            db.session.add(new_prisoner)

        # Commit transaction
        db.session.commit()
        return jsonify({"message": "Registration successful"}), 201

    except Exception as e:
        app.logger.error(f"Error during registration: {e}")
        db.session.rollback()
        return jsonify({"message": f"Registration failed. Error: {str(e)}"}), 500

@app.cli.command("create-tables")
def create_tables():
    """Create all database tables."""
    with app.app_context():
        db.create_all()
        print("Tables created successfully!")

@app.route("/add-completed-case", methods=["POST"])
def add_completed_case():
    try:
        data = request.get_json()
        app.logger.info(f"Received data: {data}")

        # Validate required fields
        required_fields = [
            "prisoner_id", "aadhar_number", "case_number", "arrest_conditions",
            "charges", "offense_date", "arrest_date", "bail_status",
            "case_status", "court_hearing_date", "judgement"
        ]
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

        # Validate dates
        for date_field in ["offense_date", "arrest_date", "court_hearing_date"]:
            try:
                datetime.strptime(data[date_field], "%Y-%m-%d")
            except ValueError:
                return jsonify({"error": f"Invalid date format for {date_field}. Use YYYY-MM-DD"}), 400

        # Add to Completed Cases
        new_completed_case = CompletedCase(
            prisoner_id=data["prisoner_id"],
            aadhar_number=data["aadhar_number"],
            case_number=data["case_number"],
            arrest_conditions=data["arrest_conditions"],
            charges=data["charges"],
            offense_date=data["offense_date"],
            arrest_date=data["arrest_date"],
            bail_status=data["bail_status"],
            case_status=data["case_status"],
            court_hearing_date=data["court_hearing_date"],
            judgement=data["judgement"],
        )
        db.session.add(new_completed_case)
        db.session.commit()
        return jsonify({"message": "Completed case added successfully!"}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding completed case: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)


