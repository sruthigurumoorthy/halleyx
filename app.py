from flask import Flask, request, jsonify, send_from_directory, abort
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from contextlib import contextmanager
import traceback

import models
from database import SessionLocal, init_db
from engine import evaluate_rule_condition

# Initialize DB
init_db()

ERROR_LOG = "error.log"

def log_error(e):
    with open(ERROR_LOG, "a") as f:
        f.write(f"\n--- {datetime.now()} ---\n")
        traceback.print_exc(file=f)
    traceback.print_exc()

app = Flask(__name__, static_folder="static")

def gen_uuid():
    return str(uuid.uuid4())

@contextmanager
def yield_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# Helper to serialize models
def to_dict(obj, nested=False):
    if not obj: return None
    if isinstance(obj, dict): return obj
    
    from sqlalchemy import inspect
    d = {}
    try:
        # Use ORM Mapper to get attribute keys (handles renamed columns like metadata_)
        mapper = inspect(obj).mapper
        for attr in mapper.column_attrs:
            val = getattr(obj, attr.key)
            if isinstance(val, datetime):
                val = val.isoformat()
            if hasattr(models, 'StepType') and isinstance(val, models.StepType):
                val = val.value
            if hasattr(models, 'ExecutionStatus') and isinstance(val, models.ExecutionStatus):
                val = val.value
            
            # Map back to public name if internal _ suffix exists
            key = attr.key
            if key.endswith('_') and not key.startswith('_'):
                key = key[:-1]
            d[key] = val
        
        # Handle specific relationships if requested (shallow)
        if nested:
            if hasattr(obj, 'rules') and obj.rules:
                d['rules'] = [to_dict(r, nested=False) for r in obj.rules]
            if hasattr(obj, 'logs') and obj.logs:
                d['logs'] = [to_dict(l, nested=False) for l in obj.logs]
            if hasattr(obj, 'steps') and obj.steps:
                d['steps'] = [to_dict(s, nested=False) for s in obj.steps]
    except Exception as e:
        print(f"Serialization error: {e}")
    return d

# --- Workflows ---
@app.route("/workflows", methods=["POST"])
def create_workflow():
    try:
        data = request.json
        with yield_db() as db:
            wf_id = gen_uuid()
            db_wf = models.Workflow(
                id=wf_id,
                name=data["name"],
                is_active=data.get("is_active", True),
                input_schema=data.get("input_schema", {}),
                start_step_id=data.get("start_step_id")
            )
            db.add(db_wf)
            db.commit()
            db.refresh(db_wf)
            return jsonify(to_dict(db_wf))
    except Exception as e:
        log_error(e)
        return jsonify({"error": str(e)}), 500

@app.route("/workflows", methods=["GET"])
def list_workflows():
    try:
        with yield_db() as db:
            wfs = db.query(models.Workflow).order_by(models.Workflow.updated_at.desc()).all()
            return jsonify([to_dict(w) for w in wfs])
    except Exception as e:
        log_error(e)
        return jsonify({"error": str(e)}), 500

@app.route("/workflows/<id>", methods=["GET"])
def get_workflow(id):
    try:
        with yield_db() as db:
            wf = db.query(models.Workflow).filter_by(id=id).first()
            if not wf: abort(404)
            return jsonify(to_dict(wf))
    except Exception as e:
        log_error(e)
        return jsonify({"error": str(e)}), 500

@app.route("/workflows/<id>", methods=["PUT"])
def update_workflow(id):
    try:
        data = request.json
        with yield_db() as db:
            wf = db.query(models.Workflow).filter_by(id=id).first()
            if not wf: abort(404)
            
            wf.version += 1
            if "name" in data: wf.name = data["name"]
            if "is_active" in data: wf.is_active = data["is_active"]
            if "input_schema" in data: wf.input_schema = data["input_schema"]
            if "start_step_id" in data: wf.start_step_id = data["start_step_id"]
            
            db.commit()
            db.refresh(wf)
            return jsonify(to_dict(wf))
    except Exception as e:
        log_error(e)
        return jsonify({"error": str(e)}), 500

@app.route("/workflows/<id>", methods=["DELETE"])
def delete_workflow(id):
    try:
        with yield_db() as db:
            wf = db.query(models.Workflow).filter_by(id=id).first()
            if wf:
                db.delete(wf)
                db.commit()
            return jsonify({"status": "ok"})
    except Exception as e:
        log_error(e)
        return jsonify({"error": str(e)}), 500

# --- Steps ---
@app.route("/workflows/<workflow_id>/steps", methods=["POST"])
def create_step(workflow_id):
    try:
        data = request.json
        with yield_db() as db:
            step_id = gen_uuid()
            # SA Enum fix: Use the constructor correctly or string value
            db_step = models.Step(
                id=step_id,
                workflow_id=workflow_id,
                name=data["name"],
                step_type=data["step_type"], # models.py Enum(StepType) handles string or enum
                order=data.get("order", 1),
                metadata_=data.get("metadata", data.get("metadata_", {}))
            )
            db.add(db_step)
            
            wf = db.query(models.Workflow).filter_by(id=workflow_id).first()
            if wf and not wf.start_step_id:
                wf.start_step_id = step_id
                
            db.commit()
            db.refresh(db_step)
            return jsonify(to_dict(db_step))
    except Exception as e:
        log_error(e)
        return jsonify({"error": str(e)}), 500

@app.route("/workflows/<workflow_id>/steps", methods=["GET"])
def list_steps(workflow_id):
    try:
        with yield_db() as db:
            steps = db.query(models.Step).filter_by(workflow_id=workflow_id).order_by(models.Step.order).all()
            return jsonify([to_dict(s, nested=True) for s in steps])
    except Exception as e:
        log_error(e)
        return jsonify({"error": str(e)}), 500

@app.route("/steps/<id>", methods=["DELETE"])
def delete_step(id):
    try:
        with yield_db() as db:
            step = db.query(models.Step).filter_by(id=id).first()
            if step:
                db.delete(step)
                db.commit()
            return jsonify({"status": "ok"})
    except Exception as e:
        log_error(e)
        return jsonify({"error": str(e)}), 500

# --- Rules ---
@app.route("/steps/<step_id>/rules", methods=["POST"])
def create_rule(step_id):
    try:
        data = request.json
        with yield_db() as db:
            rule = models.Rule(
                id=gen_uuid(),
                step_id=step_id,
                condition=data["condition"],
                next_step_id=data.get("next_step_id"),
                priority=data["priority"]
            )
            db.add(rule)
            db.commit()
            db.refresh(rule)
            return jsonify(to_dict(rule))
    except Exception as e:
        log_error(e)
        return jsonify({"error": str(e)}), 500

@app.route("/steps/<step_id>/rules", methods=["GET"])
def list_rules(step_id):
    try:
        with yield_db() as db:
            rules = db.query(models.Rule).filter_by(step_id=step_id).order_by(models.Rule.priority).all()
            return jsonify([to_dict(r) for r in rules])
    except Exception as e:
        log_error(e)
        return jsonify({"error": str(e)}), 500

@app.route("/rules/<id>", methods=["DELETE"])
def delete_rule(id):
    try:
        with yield_db() as db:
            rule = db.query(models.Rule).filter_by(id=id).first()
            if rule:
                db.delete(rule)
                db.commit()
            return jsonify({"status": "ok"})
    except Exception as e:
        log_error(e)
        return jsonify({"error": str(e)}), 500

# --- Execution Engine ---
def process_step(execution_id, step_id, db):
    try:
        execution = db.query(models.Execution).filter_by(id=execution_id).first()
        if not execution or execution.status != models.ExecutionStatus.in_progress:
            return
            
        step = db.query(models.Step).filter_by(id=step_id).first()
        if not step:
            execution.status = models.ExecutionStatus.failed
            db.commit()
            return

        execution.current_step_id = step_id
        db.commit()

        # Fetch rules for this step
        rules = db.query(models.Rule).filter_by(step_id=step_id).order_by(models.Rule.priority).all()
        
        evaluated_logs = []
        selected_next_step = None
        step_failed = False
        
        for rule in rules:
            try:
                matched = evaluate_rule_condition(rule.condition, execution.data)
                evaluated_logs.append({"rule": rule.condition, "result": matched})
                if matched:
                    selected_next_step = rule.next_step_id
                    break
            except Exception as e:
                evaluated_logs.append({"rule": rule.condition, "result": "error", "error": str(e)})
                step_failed = True
                break
                
        status = models.ExecutionStatus.completed if not step_failed else models.ExecutionStatus.failed
        
        log = models.ExecutionLog(
            id=gen_uuid(),
            execution_id=execution.id,
            step_id=step.id,
            step_name=step.name,
            step_type=step.step_type,
            evaluated_rules=evaluated_logs,
            selected_next_step=selected_next_step,
            status=status,
            ended_at=models.get_utc_now()
        )
        db.add(log)
        
        if step_failed:
            execution.status = models.ExecutionStatus.failed
            execution.ended_at = models.get_utc_now()
            db.commit()
            return
            
        if not selected_next_step:
            execution.status = models.ExecutionStatus.completed
            execution.current_step_id = None
            execution.ended_at = models.get_utc_now()
            db.commit()
            return
            
        db.commit()
        # Execute next step recursively
        process_step(execution.id, selected_next_step, db)
    except Exception as e:
        log_error(e)

@app.route("/workflows/<workflow_id>/execute", methods=["POST"])
def execute_workflow(workflow_id):
    try:
        data = request.json.get("data", {})
        with yield_db() as db:
            wf = db.query(models.Workflow).filter_by(id=workflow_id).first()
            if not wf or not wf.start_step_id:
                return jsonify({"error": "Invalid workflow or no start step"}), 400
                
            exec_id = gen_uuid()
            execution = models.Execution(
                id=exec_id,
                workflow_id=wf.id,
                workflow_version=wf.version,
                status=models.ExecutionStatus.in_progress,
                data=data,
                current_step_id=wf.start_step_id
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            
            # Process synchronously for demo
            process_step(exec_id, wf.start_step_id, db)
            
            db.refresh(execution)
            return jsonify(to_dict(execution))
    except Exception as e:
        log_error(e)
        return jsonify({"error": str(e)}), 500

@app.route("/executions", methods=["GET"])
def list_executions():
    try:
        with yield_db() as db:
            executions = db.query(models.Execution).order_by(models.Execution.started_at.desc()).all()
            return jsonify([to_dict(e) for e in executions])
    except Exception as e:
        log_error(e)
        return jsonify({"error": str(e)}), 500

@app.route("/executions/<id>", methods=["GET"])
def get_execution(id):
    try:
        with yield_db() as db:
            ex = db.query(models.Execution).filter_by(id=id).first()
            if not ex: abort(404)
            return jsonify(to_dict(ex, nested=True))
    except Exception as e:
        log_error(e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
