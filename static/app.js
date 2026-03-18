const API_BASE = '';

const app = {
    currentRoute: 'workflows',
    currentWorkflowId: null,

    init() {
        this.bindEvents();
        this.navigate('workflows');
    },

    bindEvents() {
        document.querySelectorAll('.nav-links li').forEach(el => {
            el.addEventListener('click', (e) => {
                document.querySelectorAll('.nav-links li').forEach(li => li.classList.remove('active'));
                e.currentTarget.classList.add('active');
                this.navigate(e.currentTarget.dataset.route);
            });
        });

        // Modal overlay click to close
        document.getElementById('modal-overlay').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeModal();
        });
    },

    navigate(route, meta = {}) {
        this.currentRoute = route;
        const container = document.getElementById('view-container');
        const title = document.getElementById('page-title');
        container.innerHTML = '';

        if (route === 'dashboard') {
            title.textContent = 'Resource Dashboard';
            const tpl = document.getElementById('tpl-dashboard').content.cloneNode(true);
            container.appendChild(tpl);
            this.loadDashboardActivity();
        }
        else if (route === 'workflows') {
            title.textContent = 'Workflows';
            const tpl = document.getElementById('tpl-workflows-list').content.cloneNode(true);
            container.appendChild(tpl);
            this.loadWorkflows();
        }
        else if (route === 'workflow-editor') {
            title.textContent = 'Workflow Editor';
            this.currentWorkflowId = meta.id;
            const tpl = document.getElementById('tpl-workflow-editor').content.cloneNode(true);
            container.appendChild(tpl);
            this.loadWorkflowDetails(meta.id);
        }
        else if (route === 'executions') {
            title.textContent = 'Audit Log';
            const tpl = document.getElementById('tpl-executions-list').content.cloneNode(true);
            container.appendChild(tpl);
            this.loadExecutions();
        }
    },

    async api(endpoint, method = 'GET', body = null) {
        const options = { method, headers: { 'Content-Type': 'application/json' } };
        if (body) options.body = JSON.stringify(body);
        const res = await fetch(`${API_BASE}${endpoint}`, options);
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },

    async loadWorkflows() {
        try {
            const data = await this.api('/workflows');
            const tbody = document.getElementById('workflows-tbody');
            tbody.innerHTML = '';
            data.forEach(wf => {
                tbody.innerHTML += `
                    <tr>
                        <td style="font-family: monospace;">${wf.id.split('-')[0]}...</td>
                        <td><b>${wf.name}</b></td>
                        <td>v${wf.version}</td>
                        <td><span class="badge ${wf.is_active ? 'active' : ''}">${wf.is_active ? 'Active' : 'Inactive'}</span></td>
                        <td>
                            <button class="btn btn-sm btn-secondary" onclick="app.navigate('workflow-editor', {id: '${wf.id}'})">Edit</button>
                            <button class="btn btn-sm btn-primary" onclick="app.showExecuteModal('${wf.id}', '${wf.name}')">Execute</button>
                        </td>
                    </tr>
                `;
            });
        } catch (e) {
            alert('Error loading workflows');
        }
    },

    async loadWorkflowDetails(id) {
        try {
            const wf = await this.api(`/workflows/${id}`);
            document.getElementById('editor-wf-name').textContent = wf.name;
            document.getElementById('editor-wf-version').textContent = `v${wf.version}`;
            document.getElementById('wf-name-input').value = wf.name;
            document.getElementById('wf-schema-input').value = JSON.stringify(wf.input_schema, null, 2);

            // Load steps
            const steps = await this.api(`/workflows/${id}/steps`);
            this.renderSteps(steps);
        } catch (e) {
            alert('Error loading details');
        }
    },

    renderSteps(steps) {
        const container = document.getElementById('steps-list');
        container.innerHTML = '';
        if (steps.length === 0) {
            container.innerHTML = '<p class="text-muted">No steps configured.</p>';
            return;
        }

        steps.forEach((step, idx) => {
            container.innerHTML += `
                <div class="step-item">
                    <div class="step-info">
                        <h4>${idx + 1}. ${step.name}</h4>
                        <div class="meta">Type: ${step.step_type} | rules: ${step.rules ? step.rules.length : 0}</div>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-secondary" onclick="app.editStep('${step.id}')">Edit</button>
                        <button class="btn btn-sm btn-secondary" onclick="app.deleteStep('${step.id}')">Delete</button>
                        <button class="btn btn-sm btn-primary" onclick="app.showRulesModal('${step.id}', '${step.name}')">Rules</button>
                    </div>
                </div>
            `;
        });
    },

    async saveWorkflowDetails() {
        const name = document.getElementById('wf-name-input').value;
        let schema;
        try {
            schema = JSON.parse(document.getElementById('wf-schema-input').value);
        } catch (e) {
            alert('Invalid JSON schema');
            return;
        }

        try {
            await this.api(`/workflows/${this.currentWorkflowId}`, 'PUT', { name, input_schema: schema });
            this.loadWorkflowDetails(this.currentWorkflowId);
            this.toast('Saved successfully');
        } catch (e) {
            this.toast('Error saving', 'error');
        }
    },

    async showCreateWorkflow() {
        this.openModal(`
            <h3>Create Workflow</h3>
            <div class="form-group" style="margin-top:20px">
                <label>Name</label>
                <input type="text" id="new-wf-name" class="input-field" placeholder="e.g. Expense Approval">
            </div>
            <button class="btn btn-primary" onclick="app.createWorkflow()">Create</button>
        `);
    },

    async createWorkflow() {
        const name = document.getElementById('new-wf-name').value;
        if (!name) return;
        try {
            const wf = await this.api('/workflows', 'POST', {
                name,
                input_schema: {},
                is_active: true
            });
            this.closeModal();
            this.navigate('workflow-editor', { id: wf.id });
        } catch (e) { alert('Error creating'); }
    },

    async showAddStepModal() {
        this.openModal(`
            <h3>Add Step</h3>
            <div class="form-group" style="margin-top:20px">
                <label>Step Name</label>
                <input type="text" id="new-step-name" class="input-field">
            </div>
            <div class="form-group">
                <label>Type</label>
                <select id="new-step-type" class="input-field">
                    <option value="task">Task</option>
                    <option value="approval">Approval</option>
                    <option value="notification">Notification</option>
                </select>
            </div>
            <button class="btn btn-primary" onclick="app.createStep()">Add Step</button>
        `);
    },

    async createStep() {
        const name = document.getElementById('new-step-name').value;
        const type = document.getElementById('new-step-type').value;
        if (!name) return;

        try {
            await this.api(`/workflows/${this.currentWorkflowId}/steps`, 'POST', {
                name,
                step_type: type,
                order: 1
            });
            this.closeModal();
            this.loadWorkflowDetails(this.currentWorkflowId);
        } catch (e) { alert('Error creating step'); }
    },

    async showRulesModal(stepId, stepName) {
        // Load rules
        const rules = await this.api(`/steps/${stepId}/rules`);

        // Build rules html
        let rulesHtml = rules.map(r => `
            <div class="step-item" style="margin-bottom:10px">
                <div>
                    <b>Priority ${r.priority}</b>: <code>${r.condition}</code><br>
                    <small>Next: ${r.next_step_id || 'End Workflow'}</small>
                </div>
            </div>
        `).join('');

        // Also fetch workflow steps to populate "next_step_id" dropdown
        const steps = await this.api(`/workflows/${this.currentWorkflowId}/steps`);
        const options = steps.map(s => `<option value="${s.id}">${s.name}</option>`).join('');

        this.openModal(`
            <h3>Rules for: ${stepName}</h3>
            <div style="margin: 20px 0; max-height: 200px; overflow-y:auto">
                ${rulesHtml || '<p>No rules defined</p>'}
            </div>
            <hr style="border:0; border-top:1px solid var(--glass-border); margin:20px 0">
            <h4>Add New Rule</h4>
            <div class="form-group">
                <label>Condition (e.g. amount > 100)</label>
                <input type="text" id="rule-cond" class="input-field" placeholder="DEFAULT or logical expression">
            </div>
            <div class="form-group">
                <label>Next Step</label>
                <select id="rule-next" class="input-field">
                    <option value="">-- End Workflow --</option>
                    ${options}
                </select>
            </div>
            <div class="form-group">
                <label>Priority</label>
                <input type="number" id="rule-prio" class="input-field" value="1">
            </div>
            <button class="btn btn-primary" onclick="app.createRule('${stepId}')">Add Rule</button>
        `);
    },

    async createRule(stepId) {
        const condition = document.getElementById('rule-cond').value;
        const next_step_id = document.getElementById('rule-next').value || null;
        const priority = parseInt(document.getElementById('rule-prio').value);

        if (!condition) return;
        try {
            await this.api(`/steps/${stepId}/rules`, 'POST', {
                condition, next_step_id, priority
            });
            this.closeModal();
            alert('Rule added');
        } catch (e) { alert('Error adding rule'); }
    },

    async showExecuteModal(wfId, wfName) {
        // Get schema
        const wf = await this.api(`/workflows/${wfId}`);
        const schema = wf.input_schema || {};

        // generate inputs dynamically
        let inputsHtml = '';
        for (const [key, props] of Object.entries(schema)) {
            inputsHtml += `
                <div class="form-group">
                    <label>${key} ${props.required ? '*' : ''}</label>
                    <input type="text" id="exec-input-${key}" class="input-field" data-type="${props.type}" placeholder="${props.type}">
                </div>
            `;
        }

        if (!inputsHtml) inputsHtml = '<p>No input schema defined. Sending empty data.</p>';

        window.currentExecSchema = schema;
        window.currentExecWfId = wfId;

        this.openModal(`
            <h3>Execute: ${wfName}</h3>
            <div style="margin-top:20px">
                ${inputsHtml}
            </div>
            <button class="btn btn-primary" onclick="app.triggerExecution()">Start Execution</button>
        `);
    },

    async triggerExecution() {
        const schema = window.currentExecSchema;
        const data = {};

        for (const [key, props] of Object.entries(schema)) {
            const val = document.getElementById(`exec-input-${key}`).value;
            if (props.required && !val) {
                alert(`Missing required field: ${key}`);
                return;
            }
            if (val) {
                // simple type coercion
                data[key] = props.type === 'number' ? Number(val) : val;
            }
        }

        try {
            await this.api(`/workflows/${window.currentExecWfId}/execute`, 'POST', { data });
            this.closeModal();
            this.navigate('executions');
        } catch (e) { alert('Execution failed to start'); }
    },

    async loadExecutions() {
        try {
            const data = await this.api('/executions');
            const tbody = document.getElementById('executions-tbody');
            tbody.innerHTML = '';
            data.forEach(ex => {
                let dur = '';
                if (ex.ended_at && ex.started_at) {
                    dur = ((new Date(ex.ended_at) - new Date(ex.started_at)) / 1000) + 's';
                }

                let bclass = ex.status === 'completed' ? 'active' : (ex.status === 'failed' ? 'failed' : 'pending');

                tbody.innerHTML += `
                    <tr>
                        <td style="font-family: monospace;">${ex.id.split('-')[0]}...</td>
                        <td><small>${ex.workflow_id.split('-')[0]}...</small></td>
                        <td><span class="badge ${bclass}">${ex.status}</span></td>
                        <td>${new Date(ex.started_at).toLocaleString()}</td>
                        <td>${dur || '-'}</td>
                        <td>
                            <button class="btn btn-sm btn-secondary" onclick="app.showExecutionLogs('${ex.id}')">View Logs</button>
                        </td>
                    </tr>
                `;
            });
        } catch (e) {
            alert('Error loading executions');
        }
    },

    async showExecutionLogs(execId) {
        try {
            const ex = await this.api(`/executions/${execId}`);
            const logs = ex.logs || [];

            let html = logs.map(l => `
                <div class="step-item" style="margin-bottom:10px; display:block">
                    <h4>[${l.step_type.toUpperCase()}] ${l.step_name}</h4>
                    <span class="badge ${l.status === 'completed' ? 'active' : 'failed'}">${l.status}</span>
                    <div style="margin-top:10px; background: rgba(0,0,0,0.3); padding: 10px; border-radius:4px; font-family:monospace; font-size:12px">
                        Rules Evaluated:<br>
                        ${JSON.stringify(l.evaluated_rules, null, 2)}
                        <br><br>
                        Next Step ID: ${l.selected_next_step || 'None (End)'}
                    </div>
                </div>
            `).join('');

            this.openModal(`
                <h3>Execution Logs</h3>
                <div style="margin-top:20px; max-height:400px; overflow-y:auto">
                    ${html || '<p>No logs available.</p>'}
                </div>
            `);
        } catch (e) {
            alert('Load logs failed');
        }
    },

    async loadDashboardActivity() {
        try {
            const data = await this.api('/executions');
            const container = document.getElementById('live-activity');
            if(!container) return;
            
            container.innerHTML = data.slice(0, 5).map(ex => `
                <div style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px;">
                    <div class="flex-between">
                        <span style="color: var(--primary)">#${ex.id.split('-')[0]}</span>
                        <span class="badge ${ex.status === 'completed' ? 'active' : 'failed'}" style="scale: 0.8">${ex.status}</span>
                    </div>
                    <div class="text-muted" style="margin-top:4px">${new Date(ex.started_at).toLocaleTimeString()}</div>
                </div>
            `).join('') || '<p class="text-muted">No recent activity</p>';
        } catch(e) {}
    },

    toast(msg, type = 'success') {
        const container = document.getElementById('toast-container');
        const t = document.createElement('div');
        t.className = `toast glass ${type}`;
        t.innerHTML = `<span>${type === 'success' ? '✅' : '❌'}</span> ${msg}`;
        container.appendChild(t);
        setTimeout(() => t.classList.add('active'), 10);
        setTimeout(() => {
            t.classList.remove('active');
            setTimeout(() => t.remove(), 300);
        }, 3000);
    },

    openModal(html) {
        const overlay = document.getElementById('modal-overlay');
        const content = document.getElementById('modal-content');
        content.innerHTML = html;
        overlay.classList.add('active');
    },

    closeModal() {
        const overlay = document.getElementById('modal-overlay');
        overlay.classList.remove('active');
    }
};

window.onload = () => app.init();