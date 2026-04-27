from backend.database.models import AgentDecision


class BaseAgent:
    name = "Base Agent"

    def log(self, message: str) -> AgentDecision:
        return AgentDecision(agent=self.name, message=message)

