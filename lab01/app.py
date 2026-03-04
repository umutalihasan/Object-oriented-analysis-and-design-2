from flask import Flask, jsonify, request, render_template
from models.employee import Employee
from models.department import Department
from datetime import datetime

app = Flask(__name__)

# ── In-memory store ──────────────────────────────────────────
_eid = [20]
_did = [10]
_employees:   list[Employee]   = []
_departments: list[Department] = []
_activity:    list[dict]       = []


def next_eid():
    _eid[0] += 1;  return _eid[0]

def next_did():
    _did[0] += 1;  return _did[0]

def find_emp(emp_id):
    return next((e for e in _employees if e.id == emp_id), None)

def find_dept(dept_id):
    return next((d for d in _departments if d.id == dept_id), None)

def log(icon, message, category="info"):
    _activity.insert(0, {
        "icon": icon, "message": message, "category": category,
        "time": datetime.now().strftime("%H:%M"),
    })
    if len(_activity) > 60:
        _activity.pop()


def seed():
    depts = [
        Department(1, "TechCorp HQ",     parent_id=None, budget=120000),
        Department(2, "Engineering",      parent_id=1,    budget=80000),
        Department(3, "Human Resources",  parent_id=1,    budget=25000),
        Department(4, "Backend Team",     parent_id=2,    budget=35000),
        Department(5, "Frontend Team",    parent_id=2,    budget=30000),
    ]
    _departments.extend(depts)
    _did[0] = 6

    emps = [
        Employee(1,  "Alice Johnson", "Backend Lead",    9500, "Active",    4),
        Employee(2,  "Bob Smith",     "Senior Dev",      7800, "Active",    4),
        Employee(3,  "Carol White",   "Junior Dev",      4500, "Candidate", 4),
        Employee(4,  "David Lee",     "React Dev",       7200, "Active",    5),
        Employee(5,  "Eva Brown",     "UX Engineer",     6800, "OnLeave",   5),
        Employee(6,  "Frank Miller",  "HR Manager",      8500, "Active",    3),
        Employee(7,  "Grace Kim",     "Recruiter",       5500, "Active",    3),
        Employee(8,  "Henry Park",    "DevOps Engineer", 8200, "Active",    4),
        Employee(9,  "Iris Chen",     "Frontend Lead",   9000, "Active",    5),
        Employee(10, "Jake Wilson",   "QA Engineer",     5800, "Candidate", 4),
    ]
    _employees.extend(emps)
    _eid[0] = 11
    log("🚀", "System initialized — TechCorp HQ loaded", "system")

seed()


def build_tree():
    dmap = {d.id: d for d in _departments}
    for d in _departments:
        d._children = []
    for e in _employees:
        if e.department_id and e.department_id in dmap:
            dmap[e.department_id].add(e)
    for d in _departments:
        if d.parent_id and d.parent_id in dmap:
            dmap[d.parent_id].add(d)
    return [d for d in _departments if d.parent_id is None]


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/tree")
def get_tree():
    roots = build_tree()
    return jsonify([r.to_dict() for r in roots])

# ── Employees ─────────────────────────────────────────────────
@app.route("/api/employees", methods=["GET"])
def list_employees():
    dept_id = request.args.get("dept_id", type=int)
    status  = request.args.get("status")
    result  = _employees
    if dept_id: result = [e for e in result if e.department_id == dept_id]
    if status:  result = [e for e in result if e.status == status]
    return jsonify([e.to_dict() for e in result])

@app.route("/api/employees", methods=["POST"])
def create_employee():
    d = request.json
    if not d.get("name") or not d.get("position") or not d.get("department_id"):
        return jsonify({"error": "name, position and department_id required"}), 400
    emp = Employee(next_eid(), d["name"].strip(), d["position"].strip(),
                   float(d.get("salary", 0)), "Candidate", int(d["department_id"]))
    _employees.append(emp)
    dept = find_dept(emp.department_id)
    log("➕", f'"{emp.name}" added to {dept.name if dept else "?"}', "hire")
    return jsonify(emp.to_dict()), 201

@app.route("/api/employees/<int:emp_id>", methods=["PUT"])
def update_employee(emp_id):
    emp = find_emp(emp_id)
    if not emp: return jsonify({"error": "Not found"}), 404
    d = request.json
    old = emp.name
    if "name"          in d: emp.name          = d["name"].strip()
    if "position"      in d: emp.position      = d["position"].strip()
    if "salary"        in d: emp.salary        = float(d["salary"])
    if "department_id" in d: emp.department_id = int(d["department_id"])
    if old != emp.name:
        log("✏️", f'Renamed "{old}" → "{emp.name}"', "edit")
    return jsonify(emp.to_dict())

@app.route("/api/employees/<int:emp_id>/transition", methods=["POST"])
def transition_employee(emp_id):
    emp = find_emp(emp_id)
    if not emp: return jsonify({"error": "Not found"}), 404
    new_status = request.json.get("status")
    old_status = emp.status
    try:
        emp.transition_to(new_status)
        verbs = {
            ("Candidate","Active"):  ("✅","hired"),
            ("Active","OnLeave"):    ("🌴","went on leave"),
            ("OnLeave","Active"):    ("↩️","returned from leave"),
            ("Active","Fired"):      ("❌","terminated"),
            ("OnLeave","Fired"):     ("❌","terminated"),
        }
        icon, verb = verbs.get((old_status, new_status), ("🔄", f"→ {new_status}"))
        log(icon, f'"{emp.name}" {verb}', "transition")
        return jsonify(emp.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/employees/<int:emp_id>", methods=["DELETE"])
def delete_employee(emp_id):
    global _employees
    emp = find_emp(emp_id)
    if emp: log("🗑", f'"{emp.name}" removed', "delete")
    _employees = [e for e in _employees if e.id != emp_id]
    return jsonify({"success": True})

# ── Departments ───────────────────────────────────────────────
@app.route("/api/departments", methods=["GET"])
def list_departments():
    build_tree()
    return jsonify([d.to_dict() for d in _departments])

@app.route("/api/departments", methods=["POST"])
def create_department():
    d = request.json
    if not d.get("name"): return jsonify({"error": "name required"}), 400
    pid    = int(d["parent_id"]) if d.get("parent_id") else None
    budget = float(d["budget"])  if d.get("budget")    else None
    dept   = Department(next_did(), d["name"].strip(), pid, budget)
    _departments.append(dept)
    log("🏢", f'Department "{dept.name}" created', "dept")
    return jsonify(dept.to_dict()), 201

@app.route("/api/departments/<int:dept_id>", methods=["PUT"])
def update_department(dept_id):
    dept = find_dept(dept_id)
    if not dept: return jsonify({"error": "Not found"}), 404
    d = request.json
    if "name"   in d: dept.name   = d["name"].strip()
    if "budget" in d: dept.budget = float(d["budget"]) if d["budget"] else None
    build_tree()
    return jsonify(dept.to_dict())

@app.route("/api/departments/<int:dept_id>", methods=["DELETE"])
def delete_department(dept_id):
    global _departments, _employees
    dept = find_dept(dept_id)
    if dept: log("🗑", f'Department "{dept.name}" deleted', "delete")
    _departments = [d for d in _departments if d.id != dept_id]
    _employees   = [e for e in _employees if e.department_id != dept_id]
    return jsonify({"success": True})

# ── Clone (Prototype) ─────────────────────────────────────────
@app.route("/api/clone/<string:obj_type>/<int:obj_id>", methods=["POST"])
def clone(obj_type, obj_id):
    body     = request.json or {}
    new_name = body.get("name", "").strip() or None

    if obj_type == "employee":
        emp = find_emp(obj_id)
        if not emp: return jsonify({"error": "Not found"}), 404
        cloned    = emp.clone()                    # ← PROTOTYPE
        if new_name: cloned.name = new_name
        cloned.id = next_eid()
        _employees.append(cloned)
        log("⧉", f'"{emp.name}" cloned → "{cloned.name}"', "clone")
        return jsonify({"success": True,
                        "message": f'"{emp.name}" → "{cloned.name}" (Candidate)',
                        "cloned":  cloned.to_dict()})

    elif obj_type == "department":
        build_tree()
        dept = find_dept(obj_id)
        if not dept: return jsonify({"error": "Not found"}), 404
        n         = dept.get_employee_count()
        cloned    = dept.clone()                   # ← PROTOTYPE deep clone
        if new_name: cloned.name = new_name

        def register(d):
            d.id = next_did(); _departments.append(d)
            for c in d.get_children():
                if c.is_composite():
                    c.parent_id = d.id; register(c)
                else:
                    c.id = next_eid(); c.department_id = d.id; _employees.append(c)
        register(cloned)
        log("⧉", f'Dept "{dept.name}" deep-cloned → "{cloned.name}" ({n} templates)', "clone")
        return jsonify({"success": True,
                        "message": f'"{dept.name}" → "{cloned.name}" with {n} templates',
                        "cloned":  cloned.to_dict()})

    return jsonify({"error": "Invalid type"}), 400

# ── Activity ──────────────────────────────────────────────────
@app.route("/api/activity")
def get_activity():
    return jsonify(_activity[:request.args.get("limit", 25, type=int)])

# ── Pipeline (Kanban) ─────────────────────────────────────────
@app.route("/api/pipeline")
def get_pipeline():
    build_tree()
    dmap = {d.id: d.name for d in _departments}
    result = {}
    for status in ["Candidate", "Active", "OnLeave", "Fired"]:
        result[status] = [{**e.to_dict(), "deptName": dmap.get(e.department_id,"—")}
                          for e in _employees if e.status == status]
    return jsonify(result)

# ── Stats ─────────────────────────────────────────────────────
@app.route("/api/stats")
def stats():
    build_tree()
    active     = [e for e in _employees if e.status == "Active"]
    total_fund = sum(e.salary for e in active)
    dept_map   = {d.id: d.name for d in _departments}

    breakdown = []
    for d in _departments:
        emps = [e for e in _employees if e.department_id == d.id and e.status == "Active"]
        if emps:
            breakdown.append({"name": d.name, "count": len(emps),
                               "fund": sum(e.salary for e in emps)})

    return jsonify({
        "departments":   len(_departments),
        "employees":     len(active),
        "totalFund":     total_fund,
        "active":        len(active),
        "candidates":    sum(1 for e in _employees if e.status == "Candidate"),
        "onLeave":       sum(1 for e in _employees if e.status == "OnLeave"),
        "fired":         sum(1 for e in _employees if e.status == "Fired"),
        "overBudget":    [d.name for d in _departments if d.is_over_budget()],
        "deptBreakdown": breakdown,
    })


if __name__ == "__main__":
    app.run(debug=True)
