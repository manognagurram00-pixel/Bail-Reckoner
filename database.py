from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, Date, JSON
from sqlalchemy.orm import sessionmaker
import pandas as pd
from sqlalchemy.sql import text
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_postgres import PGVector
import json

# Database and API configurations
DATABASE_URL = "postgresql://postgres:213021181@localhost/_langchain1"
openai_api_key = ""

# Initialize SQLAlchemy
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Define Table Schema
bail_cases = Table(
    "bail_cases", metadata,
    Column("id", Integer, primary_key=True),
    Column("prisoner_name", String),
    Column("case_number", Integer, unique=True),  # Ensure it's Integer
    Column("charges", String),
    Column("arrest_date", Date),
    Column("offense_type", String),
    Column("served_duration", Integer),  # Assuming it's numeric
    Column("risk_evaluation", String),
    Column("bailable", Boolean),
    Column("bail_eligibility", String),
    Column("section", String),
    Column("offense", String),
    Column("punishment", String),
    Column("embedding", JSON),  # JSON column for embeddings
    Column("bns_section", String)  # New column for BNS Section
)

# Create the table if it doesn't exist
metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# Initialize OpenAI Embeddings
embeddings = OpenAIEmbeddings(api_key=openai_api_key, request_timeout=30)

# Initialize PGVector with Correct Arguments
vectorstore = PGVector(
    connection=engine,
    embeddings=embeddings,
    collection_name="bail_cases",
    embedding_length=1536,
    use_jsonb=True
)



import pandas as pd

def clean_and_load_csv(file_path):
    try:
        # Step 1: Load CSV with the correct delimiter
        data = pd.read_csv(
            file_path,
            delimiter=",",  # Adjusted to match the CSV screenshot
            skip_blank_lines=True,
            on_bad_lines="skip",
            encoding="utf-8"
        )

        # Step 2: Rename columns
        column_rename_map = {
            "prisonerName": "prisoner_name",
            "caseNumber": "case_number",
            "arrestDate": "arrest_date",
            "bns_section": "bns_section",
            "sectionName": "section",
            "offenseType": "offense_type",
            "Served Duration": "served_duration",
            "riskEvaluation": "risk_evaluation",
            "bailable": "bailable",
            "bailEligibility": "bail_eligibility"
        }
        data.rename(columns=column_rename_map, inplace=True)

        # Debug: Print renamed columns
        print("Columns after renaming:", data.columns.tolist())

        # Step 3: Ensure all required columns are present
        required_columns = [
            "case_number", "section", "offense_type", "served_duration",
            "risk_evaluation", "bailable", "bail_eligibility", "bns_section"
        ]
        
        # Add missing columns with default values
        for col in required_columns:
            if col not in data.columns:
                print(f"Warning: Missing column '{col}', adding default values.")
                data[col] = "Not Specified" if col not in ["bailable", "served_duration"] else False

        # Debug: Print columns after ensuring all required columns
        print("Columns after filling missing data:", data.columns.tolist())

        # Step 4: Filter DataFrame to include only required columns
        data = data[required_columns]

        # Step 5: Fill NaN values with "Not Specified"
        data.fillna("Not Specified", inplace=True)

        # Step 6: Ensure column types are correct
        if "case_number" in data.columns:
            # Replace invalid values with NaN, fill with -1, and convert to integers
            data["case_number"] = pd.to_numeric(data["case_number"], errors="coerce")
            data["case_number"].fillna(-1, inplace=True)
            data["case_number"] = data["case_number"].astype(int)
        if "served_duration" in data.columns:
            # Extract numeric values from served_duration (e.g., "120 months" -> 120)
            data["served_duration"] = data["served_duration"].str.extract(r"(\d+)").fillna(0).astype(int)

        if "bailable" in data.columns:
            # Map "Yes"/"No" to True/False
            data["bailable"] = data["bailable"].map({"Yes": True, "No": False}).fillna(False)

        # Return the cleaned data
        return data

    except Exception as e:
        print(f"Error loading data: {e}")
        return None
# Function to add texts with embeddings to the database
def add_texts_with_embeddings(data):
    texts = data["offense_type"].astype(str).tolist()
    metadatas = data.to_dict(orient="records")

    embeddings_list = embeddings.embed_documents(texts)  # This returns a list of lists (embeddings)
    for doc_text, metadata, embedding in zip(texts, metadatas, embeddings_list):
        try:
            case_number = int(metadata.get("case_number", -1))  # Ensure it's an Integer

            # Debugging: Print case_number and metadata being processed
            print(f"Processing case_number: {case_number}, Metadata: {metadata}")

            # Check if the entry already exists
            existing_entry = session.execute(
                text("SELECT 1 FROM bail_cases WHERE case_number = :case_number"),
                {"case_number": case_number},
            ).fetchone()

            if existing_entry:
                print(f"Skipping duplicate case_number: {case_number}")
                continue

            # Prepare JSON serialization of the embedding
            json_embedding = json.dumps(embedding)  # Directly serialize the list

            # Insert new entry with all data including embedding
            session.execute(
                bail_cases.insert(),
                {
                    "prisoner_name": metadata.get("prisoner_name"),
                    "case_number": case_number,
                    "charges": metadata.get("charges"),
                    "arrest_date": metadata.get("arrest_date"),
                    "offense_type": metadata.get("offense_type"),
                    "served_duration": metadata.get("served_duration"),
                    "risk_evaluation": metadata.get("risk_evaluation"),
                    "bailable": metadata.get("bailable"),
                    "bail_eligibility": metadata.get("bail_eligibility"),
                    "section": metadata.get("section"),
                    "offense": metadata.get("offense"),
                    "punishment": metadata.get("punishment"),
                    "embedding": json_embedding,
                    "bns_section": metadata.get("bns_section")  # Include BNS Section
                },
            )
            print("Committing session...")
            session.commit()
            print(f"Successfully added case_number: {case_number}")

        except Exception as e:
            session.rollback()
            print(f"Database commit error for case_number {case_number}: {e}")

    # Verify the data after insertion
    print("Verifying data in bail_cases table...")
    rows = session.execute(text("SELECT * FROM bail_cases")).fetchall()
    print(f"Total rows in bail_cases: {len(rows)}")
    print(rows)
    
if __name__ == "__main__":
    print("Starting main execution...")

    file_path = "/home/prathvik/Downloads/WhatSie/Bns.csv"  # Update path as necessary
    data = clean_and_load_csv(file_path)

    if data is None:
        print("Error: Data not loaded.")
        exit()

    print("Data loaded successfully.")
    print(f"Data Preview: {data.head()}")

    print("Adding data with embeddings to the database...")
    add_texts_with_embeddings(data)
    print("Database population completed.")