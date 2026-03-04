# ================================================================
# КОД БЕЗ ПАТТЕРНА — Code WITHOUT Prototype
#
# Demonstrates the problem:
# 1. Client must know every concrete type via isinstance chains
# 2. Adding new type (Contractor) breaks clone_naive() silently
# 3. Nested department subtrees are NOT deep-cloned correctly
# 4. Business rules (status reset) must be duplicated everywhere
# ================================================================

class EmployeeNaive:
    def __init__(self, name, position, salary, status, department_id):
        self.name          = name
        self.position      = position
        self.salary        = salary
        self.status        = status
        self.department_id = department_id


class DepartmentNaive:
    def __init__(self, name, parent_id=None):
        self.name      = name
        self.parent_id = parent_id
        self.children  = []   # client must handle every type inside


def clone_naive(obj):
    """
    WITHOUT Prototype pattern.
    - Must enumerate every possible type with isinstance
    - Adding ContractorNaive requires editing THIS function
    - Sub-department children are silently dropped (bug)
    """
    if isinstance(obj, EmployeeNaive):
        return EmployeeNaive(
            name=obj.name + " (copy)",
            position=obj.position,
            salary=obj.salary,
            status="Candidate",           # duplicated business rule
            department_id=obj.department_id,
        )
    elif isinstance(obj, DepartmentNaive):
        cloned = DepartmentNaive(name=obj.name + " (copy)", parent_id=obj.parent_id)
        for child in obj.children:
            if isinstance(child, EmployeeNaive):
                cloned.children.append(clone_naive(child))
            # BUG: DepartmentNaive children silently dropped here!
            # elif isinstance(child, DepartmentNaive): <-- forgot this
        return cloned
    else:
        raise TypeError(f"Cannot clone unknown type: {type(obj).__name__}")


if __name__ == "__main__":
    eng     = DepartmentNaive("Engineering")
    backend = DepartmentNaive("Backend Team")
    backend.children.append(EmployeeNaive("Alice", "Dev", 7000, "Active", 1))
    eng.children.append(backend)           # nested dept
    eng.children.append(EmployeeNaive("Bob", "Manager", 9000, "Active", 1))

    cloned = clone_naive(eng)
    print(f"Original: {len(eng.children)} children")   # 2
    print(f"Cloned:   {len(cloned.children)} children") # 1  ← backend dept LOST
