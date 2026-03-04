class OrgComponent:
    """Abstract Prototype — every component clones itself."""

    def clone(self):
        raise NotImplementedError

    def get_name(self) -> str:
        raise NotImplementedError

    def get_salary_fund(self) -> float:
        raise NotImplementedError

    def get_employee_count(self) -> int:
        raise NotImplementedError

    def is_composite(self) -> bool:
        raise NotImplementedError

    def to_dict(self) -> dict:
        raise NotImplementedError
