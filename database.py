from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from contextlib import asynccontextmanager

Base = declarative_base()

# SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Village model
class Village(Base):
    __tablename__ = "villages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    name_kh = Column(String)
    name_en = Column(String)
    age = Column(Integer)
    gender = Column(String)
    dob = Column(String)
    image_path = Column(String)

# Initialize DB
def init_db():
    Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield
