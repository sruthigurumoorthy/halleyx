from database import SessionLocal, init_db
import models
import schemas
from engine import evaluate_rule_condition

def seed_db():
    db = SessionLocal()
    
    # Check if we already seeded
    wf = db.query(models.Workflow).filter(models.Workflow.name == "Expense Approval").first()
    if wf:
        print("Database already seeded")
        return

    # 1. Create Workflow
    wf_id = schemas.gen_uuid()
    workflow = models.Workflow(
        id=wf_id,
        name="Expense Approval",
        version=1,
        is_active=True,
        input_schema={
            "amount": {"type": "number", "required": True},
            "country": {"type": "string", "required": True},
            "department": {"type": "string", "required": False},
            "priority": {"type": "string", "required": True, "allowed_values": ["High", "Medium", "Low"]}
        }
    )
    db.add(workflow)
    
    # 2. Create Steps
    step_mgr_id = schemas.gen_uuid()
    step_fin_id = schemas.gen_uuid()
    step_ceo_id = schemas.gen_uuid()
    step_rej_id = schemas.gen_uuid()
    
    workflow.start_step_id = step_mgr_id

    s1 = models.Step(id=step_mgr_id, workflow_id=wf_id, name="Manager Approval", step_type=models.StepType.approval, order=1, metadata_={"assignee": "manager@example.com"})
    s2 = models.Step(id=step_fin_id, workflow_id=wf_id, name="Finance Notification", step_type=models.StepType.notification, order=2)
    s3 = models.Step(id=step_ceo_id, workflow_id=wf_id, name="CEO Approval", step_type=models.StepType.approval, order=3)
    s4 = models.Step(id=step_rej_id, workflow_id=wf_id, name="Task Rejection", step_type=models.StepType.task, order=4)
    
    db.add_all([s1, s2, s3, s4])
    
    # 3. Create Rules for Manager Approval Step
    r1 = models.Rule(id=schemas.gen_uuid(), step_id=step_mgr_id, condition="amount > 100 && country == 'US' && priority == 'High'", next_step_id=step_fin_id, priority=1)
    r2 = models.Rule(id=schemas.gen_uuid(), step_id=step_mgr_id, condition="amount <= 100 || department == 'HR'", next_step_id=step_ceo_id, priority=2)
    r3 = models.Rule(id=schemas.gen_uuid(), step_id=step_mgr_id, condition="priority == 'Low' && country != 'US'", next_step_id=step_rej_id, priority=3)
    r4 = models.Rule(id=schemas.gen_uuid(), step_id=step_mgr_id, condition="DEFAULT", next_step_id=step_rej_id, priority=4)

    db.add_all([r1, r2, r3, r4])
    
    db.commit()
    print("Seeded database with sample 'Expense Approval' workflow!")
    db.close()

if __name__ == "__main__":
    init_db()
    seed_db()
