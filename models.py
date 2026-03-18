from datetime import datetime, timezone
import enum
from typing import Any, Dict
from sqlalchemy import Column, String, Integer, Boolean, Enum as SAEnum, ForeignKey, DateTime, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

class StepType(str, enum.Enum):
    task = "task"
    approval = "approval"
    notification = "notification"

class ExecutionStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    canceled = "canceled"

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    input_schema = Column(JSON, nullable=False)
    start_step_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    steps = relationship("Step", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="workflow", cascade="all, delete-orphan")


class Step(Base):
    __tablename__ = "steps"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    name = Column(String, nullable=False)
    step_type = Column(SAEnum(StepType), nullable=False)
    order = Column(Integer, default=1)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    workflow = relationship("Workflow", back_populates="steps")
    rules = relationship("Rule", back_populates="step", cascade="all, delete-orphan")


class Rule(Base):
    __tablename__ = "rules"

    id = Column(String, primary_key=True)
    step_id = Column(String, ForeignKey("steps.id"), nullable=False)
    condition = Column(String, nullable=False)
    next_step_id = Column(String, nullable=True)
    priority = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    step = relationship("Step", back_populates="rules")


class Execution(Base):
    __tablename__ = "executions"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    workflow_version = Column(Integer, nullable=False)
    status = Column(SAEnum(ExecutionStatus), default=ExecutionStatus.pending)
    data = Column(JSON, nullable=False)
    current_step_id = Column(String, nullable=True)
    retries = Column(Integer, default=0)
    triggered_by = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), default=get_utc_now)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    workflow = relationship("Workflow", back_populates="executions")
    logs = relationship("ExecutionLog", back_populates="execution", cascade="all, delete-orphan")


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(String, primary_key=True)
    execution_id = Column(String, ForeignKey("executions.id"), nullable=False)
    step_id = Column(String, nullable=True)
    step_name = Column(String, nullable=False)
    step_type = Column(SAEnum(StepType), nullable=False)
    evaluated_rules = Column(JSON, nullable=False)
    selected_next_step = Column(String, nullable=True)
    status = Column(SAEnum(ExecutionStatus), nullable=False)
    error_message = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), default=get_utc_now)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    execution = relationship("Execution", back_populates="logs")
