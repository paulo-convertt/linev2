from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_lead_qualification_chatbot.models import ChatState


@CrewBase
class ChatCrew:
    """Chat Crew for Lead Qualification"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def lead_qualifier(self) -> Agent:
        return Agent(
            config=self.agents_config["lead_qualifier"],
        )

    @task
    def qualify_lead(self) -> Task:
        return Task(
            config=self.tasks_config["qualify_lead"],
            output_pydantic=ChatState,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Lead Qualification Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
