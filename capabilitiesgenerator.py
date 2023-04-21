"""A module for generating the constraints and capabilities available to the AI"""
class CapabilitiesGenerator:
    """
    A class for generating the constraints and capabilities available to the AI
    """
    def __init__(self):
        self.constraints = []
        self.capabilities = []

    def add_constraint(self, constraint: str) -> None:
        """
        Add a constraint to the constraints list.

        Args:
            constraint (str): The constraint to be added.
        """
        self.constraints.append(constraint)

    def add_capability(self, capability: str) -> None:
        """
        Add a capability to the capabilities list.

        Args:
            constraint (str): The constraint to be added.
        """
        self.capabilities.append(capability)

    def get_constraints_capabilities(self) -> str:
        """
        Return a string containing the constraints and capabilities.
        """
        constraints = ""
        for constraint in self.constraints:
            constraints += f"{constraint}; "
        constraints.strip('; ')

        capabilities = ""
        for capability in self.capabilities:
            capabilities += f"{capability}; "
        capabilities.strip('; ')

        constraints_capabilities = f"CONSTRAINTS: {constraints}. CAPABILITIES: {capabilities}."

        return constraints_capabilities
