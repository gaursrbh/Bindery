class DesignSystemError(Exception):
    """Raised for any malformed system.yaml, missing tokens.json, unresolvable
    version spec, or missing layout function. Message format: "<file>: <field>:
    <what's wrong>" per M0-spec.md §3.2."""

    def __init__(self, file: str, field: str, detail: str):
        self.file = file
        self.field = field
        self.detail = detail
        super().__init__(f"{file}: {field}: {detail}")
