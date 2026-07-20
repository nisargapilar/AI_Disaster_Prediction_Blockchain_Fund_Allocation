from sqlalchemy import Column, String, Float, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP 
from db import Base
import uuid

class EventModel(Base):
    __tablename__ = "events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disaster_type = Column(String, nullable=False)
    source = Column(String, nullable=False)
    external_id = Column(String, unique=True, nullable=True)
    event_time = Column(TIMESTAMP(timezone=True), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    region = Column(Text, nullable=False)
    input_data = Column(JSONB, nullable=False)
    risk_score = Column(Float, nullable=False)
    severity_tier = Column(String, nullable=False)
    fund_status = Column(String, nullable=False, default="not_applicable")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())