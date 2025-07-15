from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from models import ChatState
import os


@CrewBase
class ChatCrew:
    """Chat Crew for Lead Qualification"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    api_key = os.getenv('OPENAI_API_KEY')

    @agent
    def line_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["line_agent"],
            llm=LLM(
                model="openai/gpt-4o-mini",
                api_key=self.api_key,
                temperature=0
            )
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
            verbose=True
        )
