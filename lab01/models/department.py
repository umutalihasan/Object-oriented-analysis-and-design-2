from models.prototype import OrgComponent


class Department(OrgComponent):
    """Concrete Prototype — Composite node."""

    def __init__(self, dept_id, name, parent_id=None, budget=None):
        self.id        = dept_id
        self.name      = name
        self.parent_id = parent_id
        self.budget    = float(budget) if budget else None
        self._children: list[OrgComponent] = []

    def add(self, component: OrgComponent):
        self._children.append(component)

    def get_children(self):
        return list(self._children)

    # ── Prototype ─────────────────────────────────────────────
    def clone(self):
        """
        PROTOTYPE — recursive deep clone of entire subtree.
        Each child calls its own clone() polymorphically.
        One call, any depth, no isinstance anywhere.
        """
        cloned = Department(
            dept_id=None,
            name=self.name + " (copy)",
            parent_id=self.parent_id,
            budget=self.budget,
        )
        for child in self._children:
            cloned.add(child.clone())   # polymorphic recursive call
        return cloned

    # ── Budget helpers ────────────────────────────────────────
    def budget_usage(self) -> float:
        """Salary fund as % of budget (0-100+). None if no budget set."""
        if not self.budget:
            return None
        return round(self.get_salary_fund() / self.budget * 100, 1)

    def is_over_budget(self) -> bool:
        u = self.budget_usage()
        return u is not None and u > 100

    # ── OrgComponent ─────────────────────────────────────────
    def get_name(self):           return self.name
    def get_salary_fund(self):    return sum(c.get_salary_fund() for c in self._children)
    def get_employee_count(self): return sum(c.get_employee_count() for c in self._children)
    def is_composite(self):       return True

    def to_dict(self):
        usage = self.budget_usage()
        return {
            "id":            self.id,
            "name":          self.name,
            "type":          "department",
            "parent_id":     self.parent_id,
            "budget":        self.budget,
            "budgetUsage":   usage,
            "overBudget":    self.is_over_budget(),
            "employeeCount": self.get_employee_count(),
            "salaryFund":    self.get_salary_fund(),
            "children":      [c.to_dict() for c in self._children],
        }
