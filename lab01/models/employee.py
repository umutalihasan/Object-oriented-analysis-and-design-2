from models.prototype import OrgComponent


VALID_TRANSITIONS = {
    "Candidate": ["Active", "Fired"],
    "Active":    ["OnLeave", "Fired"],
    "OnLeave":   ["Active", "Fired"],
    "Fired":     [],
}

STATUS_META = {
    "Active":    {"color": "#22c55e", "bg": "rgba(34,197,94,.13)",  "label": "Active"},
    "Candidate": {"color": "#f59e0b", "bg": "rgba(245,158,11,.13)", "label": "Candidate"},
    "OnLeave":   {"color": "#38bdf8", "bg": "rgba(56,189,248,.13)", "label": "On Leave"},
    "Fired":     {"color": "#ef4444", "bg": "rgba(239,68,68,.13)",  "label": "Fired"},
}


class Employee(OrgComponent):
    """Concrete Prototype — Leaf node."""

    def __init__(self, emp_id, name, position, salary,
                 status="Candidate", department_id=None):
        self.id            = emp_id
        self.name          = name
        self.position      = position
        self.salary        = float(salary)
        self.status        = status
        self.department_id = department_id

    # ── Prototype ────────────────────────────────────────────
    def clone(self):
        """
        PROTOTYPE: employee clones itself.
        Copies role/salary template. Resets status → Candidate.
        Client never needs to know internal fields.
        """
        return Employee(
            emp_id=None,
            name=self.name + " (copy)",
            position=self.position,
            salary=self.salary,
            status="Candidate",
            department_id=self.department_id,
        )

    # ── State transitions ─────────────────────────────────────
    def can_transition_to(self, new_status: str) -> bool:
        return new_status in VALID_TRANSITIONS.get(self.status, [])

    def transition_to(self, new_status: str):
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition '{self.status}' → '{new_status}'"
            )
        self.status = new_status

    def available_transitions(self) -> list[str]:
        return VALID_TRANSITIONS.get(self.status, [])

    # ── OrgComponent ─────────────────────────────────────────
    def get_name(self):            return self.name
    def get_salary_fund(self):     return self.salary if self.status not in ("Fired",) else 0.0
    def get_employee_count(self):  return 1 if self.status != "Fired" else 0
    def is_composite(self):        return False

    def to_dict(self):
        meta = STATUS_META.get(self.status, STATUS_META["Active"])
        return {
            "id":             self.id,
            "name":           self.name,
            "type":           "employee",
            "position":       self.position,
            "salary":         self.salary,
            "status":         self.status,
            "statusLabel":    meta["label"],
            "statusColor":    meta["color"],
            "statusBg":       meta["bg"],
            "department_id":  self.department_id,
            "employeeCount":  self.get_employee_count(),
            "salaryFund":     self.get_salary_fund(),
            "transitions":    self.available_transitions(),
            "children":       [],
        }
