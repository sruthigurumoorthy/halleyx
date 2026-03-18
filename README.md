# Halleyx Full Stack Engineer - Challenge I - 2026
## demo link
https://youtu.be/dSUOz54Wvog

## Overview

This is a comprehensive workflow engine system that lets users design workflows, define rules, execute processes, and track every step. The system is built to support automation, notifications, approvals, and dynamic decision-making based on input data.

**Tech Stack:**
- **Backend**: Python 3, Flask, SQLAlchemy (SQLite natively)
- **Frontend**: Vanilla HTML / CSS (Glassmorphism UI) / JS SPA
- **Rule Engine**: Custom dynamic expression evaluator built in Python

---

## 1. Setup Instructions & Running the App

1. **Ensure Python 3.10+ is installed** on your system.
2. **Open a terminal** in this directory.
3. **Set up the virtual environment & install dependencies**:
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1   # (On Windows)
   pip install -r requirements.txt
   ```
4. **Seed the Database** (This creates the sample "Expense Approval" workflow, steps, and rules):
   ```bash
   python seed.py
   ```
5. **Run the Server**:
   ```bash
   python app.py
   ```
6. **Open the Website**:
   Navigate to `http://127.0.0.1:8000` in your web browser.

---

## 2. Core Concepts & Database Models

### 2.1 Workflow
A workflow is a process composed of multiple steps.
- **Attributes**: `id`, `name`, `version`, `is_active`, `input_schema`, `start_step_id`, `created_at`, `updated_at`.

### 2.2 Step
A single action in a workflow (`task`, `approval`, `notification`).
- **Attributes**: `id`, `workflow_id`, `name`, `step_type`, `order`, `metadata`, `created_at`, `updated_at`.

### 2.3 Rule
Defines which step should execute next based on input data. Evaluated in **priority order**.
- **Supported logic**: `==`, `!=`, `<`, `>`, `<=`, `>=`, `&&`, `||`, `contains()`, `startsWith()`, `endsWith()`.
- **Attributes**: `id`, `step_id`, `condition`, `next_step_id`, `priority`, `created_at`, `updated_at`.

### 2.4 Execution & Logs
Tracks the running state of a workflow.
- **Attributes**: `id`, `workflow_id`, `status` (`in_progress`, `completed`, `failed`), `data`, `current_step_id`, `logs`.
- Logs include the evaluated rules and selected next steps.

---

## 3. Backend APIs

The backend exposes a full suite of RESTful APIs:
- `GET /workflows`, `POST /workflows`, `GET /workflows/<id>`, `PUT /workflows/<id>`, `DELETE /workflows/<id>`
- `GET /workflows/<id>/steps`, `POST /workflows/<id>/steps`, `DELETE /steps/<id>`
- `GET /steps/<id>/rules`, `POST /steps/<id>/rules`, `DELETE /rules/<id>`
- `POST /workflows/<id>/execute`, `GET /executions`, `GET /executions/<id>`

---

## 4. Rule Engine Behavior
- Python-based engine processes expressions natively.
- Evaluates rules dynamically during step execution (`engine.py`).
- Iterates over rules by priority. First matching rule dictates the `next_step_id`.
- If no rules match and there is no `DEFAULT` rule, the step fails.

---

## 5. Sample Execution

A sample workflow **"Expense Approval"** is pre-loaded via `seed.py`.
To execute it successfully, from the UI click **Execute** and provide:
```json
{
  "amount": 250,
  "country": "US",
  "department": "IT",
  "priority": "High"
}
```
*Expected Result:*
- **Manager Approval** evaluates rules.
- Rule 1 (`amount > 100 && country == 'US' && priority == 'High'`) evaluates to `true`.
- Next step becomes **Finance Notification**.
- The workflow will automatically progress and complete. You can view the full timeline in the **Audit Log** tab!
