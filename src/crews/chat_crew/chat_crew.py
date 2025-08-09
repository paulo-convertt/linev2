from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from database.models import ChatState
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import os
import logging
import yaml

# Import our custom tools
from tools.knowledge_search_tool import knowledge_search_tool
from tools.simulation_tool import vehicle_simulation_tool
from tools.lead_qualification_tool import lead_qualification_tool

# Import flow manager
from .conversation_flow_manager import ConversationFlowManager, ConversationIntent, ConversationStage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LeadQualificationOutput(BaseModel):
    """Pydantic model for lead qualification task output - ensures JSON structure."""
    whatsapp_number: Optional[str] = Field(None, description="WhatsApp number of the user")
    history: Optional[str] = Field(None, description="Conversation history")
    nome: Optional[str] = Field(None, description="Name of the client")
    cpf: Optional[str] = Field(None, description="CPF of the client")
    estado_civil: Optional[str] = Field(None, description="Marital status")
    naturalidade: Optional[str] = Field(None, description="Place of birth")
    endereco: Optional[str] = Field(None, description="Address")
    email: Optional[str] = Field(None, description="Email address")
    nome_mae: Optional[str] = Field(None, description="Mother's name")
    renda: Optional[str] = Field(None, description="Monthly income")
    profissao: Optional[str] = Field(None, description="Profession")
    mensagem: str = Field(..., description="Response message to the user")
    conversation_stage: Optional[str] = Field(None, description="Current conversation stage")
    is_complete: Optional[bool] = Field(False, description="Whether all data collection is complete")


class SimulationOutput(BaseModel):
    """Pydantic model for simulation task output - ensures JSON structure."""
    mensagem: str = Field(..., description="Simulation message with options for the user")


class ChatResponse(BaseModel):
    """Output model for chat response with integrated tools."""
    message: str
    conversation_stage: str
    next_action: Optional[str] = None
    lead_data: Optional[Dict] = None
    vehicle_simulation: Optional[Dict] = None
    faq_answer: Optional[str] = None
    requires_human_handoff: bool = False


@CrewBase
class ChatCrew:
    """
    Chat Crew for Lead Qualification with FAQ Knowledge Base Integration.

    This crew manages the qualification of leads using AI agents equipped
    with a comprehensive FAQ knowledge base about consórcio products.
    """

    def __init__(self):
        """Initialize the ChatCrew with necessary configurations."""
        self.api_key = self._get_api_key()
        self._agents_config_data: Optional[Dict[str, Any]] = None
        self._tasks_config_data: Optional[Dict[str, Any]] = None
        self.agent = self.line_agent()

        # ✅ Flow Manager for intelligent task orchestration
        self.flow_manager = ConversationFlowManager()

        # ✅ Pré-criar instâncias dos crews para performance
        self._qualification_crew: Optional[Crew] = None
        self._complete_crew: Optional[Crew] = None
        self._crews_initialized = False

    def _get_api_key(self) -> str:
        """Retrieve and validate OpenAI API key."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it before running the crew."
            )
        return api_key

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_path = os.path.join(os.path.dirname(__file__), config_file)
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)

    def _get_agents_config(self) -> Dict[str, Any]:
        """Get agents configuration, loading optimized version if available."""
        if self._agents_config_data is None:
            self._agents_config_data = self._load_config("config/agents.yaml")
        return self._agents_config_data

    def _get_tasks_config(self) -> Dict[str, Any]:
        """Get tasks configuration, loading if necessary."""
        if self._tasks_config_data is None:
            self._tasks_config_data = self._load_config("config/tasks_unified.yaml")
        return self._tasks_config_data

    def _create_base_llm(self, temperature: float = 0.3) -> LLM:
        """
        Create base LLM configuration optimized for speed and stability.

        Args:
            temperature: LLM temperature setting (lower = more consistent tool usage)

        Returns:
            LLM: Configured language model
        """
        return LLM(
            model="o4-mini",  # ✅ Corrigido para consistência
            api_key=self.api_key,
            temperature=temperature,
            #max_tokens=1000,  # ✅ Aumentado para permitir resposta + tool usage
            timeout=30      # ✅ Timeout aumentado para tools
        )

    @agent
    def line_agent(self) -> Agent:
        """
        Create LINE agent for customer interaction and lead qualification.

        This agent is equipped with:
        - Knowledge base search for consórcio questions
        - Vehicle simulation tool for pricing and options
        - Lead qualification tool for structured data collection
        - Optimized temperature for consistent responses

        Returns:
            Agent: Configured LINE agent
        """

        # Get agent config
        agents_config = self._get_agents_config()
        agent_config = agents_config["line_agent"]

        # Create agent with all tools assigned
        agent = Agent(
            role=agent_config["role"],
            goal=agent_config["goal"],
            backstory=agent_config["backstory"],
            llm=self._create_base_llm(temperature=0.1),  # ✅ Lower temperature for more consistent tool usage
            tools=[
                knowledge_search_tool,
                vehicle_simulation_tool,
                lead_qualification_tool
            ],  # ✅ Agent must have tools assigned
            allow_delegation=False,  # ✅ Disable delegation to force tool usage
            verbose=True,
        )

        logger.info("LINE agent created successfully with all tools (FAQ, Simulation, Lead Qualification)")
        return agent


    @task
    def conversation_handler(self) -> Task:
        """
        Create unified conversation handler task with all available tools.
        This single task can handle FAQ, simulations, and lead qualification seamlessly.

        Returns:
            Task: Configured conversation handler task with structured JSON output
        """
        tasks_config = self._get_tasks_config()
        task_config = tasks_config["conversation_handler"]

        return Task(
            agent=self.agent,
            description=task_config["description"],
            expected_output=task_config["expected_output"],
            output_pydantic=LeadQualificationOutput,  # ✅ Force JSON output with Pydantic
        )

    # ✅ Unified approach: all functionality now handled by conversation_handler() task

    def get_crew(self, message: str = "", chat_state: Optional[ChatState] = None) -> Crew:
        """
        Get simplified crew with single unified task.

        Args:
            message: Current user message for context
            chat_state: Current chat state

        Returns:
            Crew: Unified crew with single conversation handler task
        """
        logger.info("🚀 Creating unified crew with single conversation handler task")

        return Crew(
            agents=[self.agent],
            tasks=[self.conversation_handler()],  # ✅ Single unified task
            process=Process.sequential,
            verbose=True,
            cache=True,
            memory=False,
        )
