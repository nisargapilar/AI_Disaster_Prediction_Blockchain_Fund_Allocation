from sqlalchemy import Column, String, Float, Text, Boolean, ForeignKey, func
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



class SubscriberModel(Base):
    __tablename__ = "subscribers"

    subscriber_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False, unique=True, index=True)
    region = Column(String, nullable=True)
    disaster_type = Column(String, nullable=True)
    is_confirmed = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    confirm_token = Column(String, nullable=False, unique=True)
    unsubscribe_token = Column(String, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class PredictionModel(Base):
    __tablename__ = "predictions"

    prediction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disaster_type = Column(String, nullable=False)
    region = Column(String, nullable=False)
    predicted_time = Column(TIMESTAMP(timezone=True), nullable=False)
    input_data = Column(JSONB, nullable=False)
    risk_score = Column(Float, nullable=False)
    severity_tier = Column(String, nullable=False)
    matched_event_id = Column(UUID(as_uuid=True), ForeignKey("events.event_id"), nullable=True)
    is_simulated = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())