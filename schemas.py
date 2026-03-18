from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from models import StepType, ExecutionStatus

# Generate UUID utility
def gen_uuid():
    return str(uuid.uuid4())

# Rules
class RuleBase(BaseModel):
    condition: str
    next_step_id: Optional[str] = None
    priority: int

class RuleCreate(RuleBase):
    pass

class RuleUpdate(RuleBase):
    condition: Optional[str] = None
    priority: Optional[int] = None

class RuleSchema(RuleBase):
    id: str
    step_id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Steps
class StepBase(BaseModel):
    name: str
    step_type: StepType
    order: int = 1
    metadata_: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")

class StepCreate(StepBase):
    pass

class StepUpdate(StepBase):
    name: Optional[str] = None
    step_type: Optional[StepType] = None
    order: Optional[int] = None
    metadata_: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")

class StepSchema(StepBase):
    id: str
    workflow_id: str
    created_at: datetime
    updated_at: datetime
    rules: List[RuleSchema] = []
    class Config:
        from_attributes = True
        populate_by_name = True

# Workflows
class WorkflowBase(BaseModel):
    name: str
    is_active: bool = True
    input_schema: Dict[str, Any]
    start_step_id: Optional[str] = None

class WorkflowCreate(WorkflowBase):
    pass

class WorkflowUpdate(WorkflowBase):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    input_schema: Optional[Dict[str, Any]] = None
    start_step_id: Optional[str] = None

class WorkflowSchema(WorkflowBase):
    id: str
    version: int
    created_at: datetime
    updated_at: datetime
    steps: List[StepSchema] = []
    class Config:
        from_attributes = True

# Execution Logs
class ExecutionLogSchema(BaseModel):
    id: str
    execution_id: str
    step_id: Optional[str]
    step_name: str
    step_type: StepType
    evaluated_rules: List[Dict[str, Any]]
    selected_next_step: Optional[str]
    status: ExecutionStatus
    error_message: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    class Config:
        from_attributes = True

# Executions
class ExecutionCreate(BaseModel):
    data: Dict[str, Any]

class ExecutionSchema(BaseModel):
    id: str
    workflow_id: str
    workflow_version: int
    status: ExecutionStatus
    data: Dict[str, Any]
    current_step_id: Optional[str]
    retries: int
    triggered_by: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    logs: List[ExecutionLogSchema] = []
    class Config:
        from_attributes = True
