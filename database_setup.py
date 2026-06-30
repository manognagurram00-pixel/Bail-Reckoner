from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, Date, Float
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:12345678@localhost:5432/bail_reckoner_langchain"

# Initialize SQLAlchemy
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Define Table Schema
bail_cases = Table(
    "bail_cases", metadata,
    Column("id", Integer, primary_key=True),
    Column("prisoner_name", String),
    Column("case_number", String, unique=True),
    Column("charges", String),
    Column("arrest_date", Date),
    Column("offense_type", String),
    Column("served_duration", String),
    Column("risk_evaluation", String),
    Column("bailable", Boolean),
    Column("bail_eligibility", String),
    Column("section", String),
    Column("offense", String),
    Column("punishment", String),
    Column("embedding", String)
)

# Create the table if it doesn't exist
metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
