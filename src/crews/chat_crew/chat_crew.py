from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from distro import name
from knowledge.knowledge_base import ConsorcioFAQTool, create_faq_collection, setup_chromadb_client
from models import ChatState
from typing import Optional, Dict, Any
from pydantic import BaseModel
import os
import logging
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LeadQualificationOutput(BaseModel):
    """Output model for lead qualification task."""
    whatsapp_number: str
    history: str
    nome: Optional[str] = None
    cpf: Optional[str] = None
    estado_civil: Optional[str] = None
    naturalidade: Optional[str] = None
    endereco: Optional[str] = None
    email: Optional[str] = None
    nome_mae: Optional[str] = None
    renda: Optional[str] = None
    profissao: Optional[str] = None
    mensagem: str
    conversation_stage: str
    is_complete: bool
    requires_human_handoff: bool


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
        self._faq_tool: Optional[ConsorcioFAQTool] = None
        self._faq_initialized = False
        self._agents_config_data: Optional[Dict[str, Any]] = None
        self._tasks_config_data: Optional[Dict[str, Any]] = None
        self.agent = self.line_agent()

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
            # Try optimized config first, fallback to original
            try:
                self._agents_config_data = self._load_config("config/agents_optimized.yaml")
                logger.info("Using optimized agents configuration")
            except FileNotFoundError:
                self._agents_config_data = self._load_config("config/agents.yaml")
                logger.info("Using standard agents configuration")
        return self._agents_config_data

    def _get_tasks_config(self) -> Dict[str, Any]:
        """Get tasks configuration, loading if necessary."""
        if self._tasks_config_data is None:
            self._tasks_config_data = self._load_config("config/tasks.yaml")
        return self._tasks_config_data

    def _initialize_faq_system(self) -> ConsorcioFAQTool:
        """
        Initialize the FAQ knowledge base system.

        Returns:
            ConsorcioFAQTool: Configured FAQ search tool

        Raises:
            Exception: If FAQ system initialization fails
        """
        if self._faq_tool and self._faq_initialized:
            logger.info("Using cached FAQ tool")
            return self._faq_tool

        try:
            logger.info("Initializing FAQ knowledge base system...")

            # Setup ChromaDB client
            client = setup_chromadb_client()
            logger.info("ChromaDB client connected successfully")

            # Get or create FAQ collection
            collection = create_faq_collection(client)
            logger.info(f"FAQ collection ready: {collection.name}")

            # Create FAQ tool
            self._faq_tool = ConsorcioFAQTool(collection)
            self._faq_initialized = True

            logger.info("FAQ system initialized successfully")
            return self._faq_tool

        except Exception as e:
            logger.error(f"Failed to initialize FAQ system: {e}")
            raise Exception(f"FAQ system initialization failed: {e}")

    def _create_base_llm(self, temperature: float = 0.7) -> LLM:
        """
        Create base LLM configuration optimized for speed and stability.

        Args:
            temperature: LLM temperature setting (higher = faster responses)

        Returns:
            LLM: Configured language model
        """
        return LLM(
            model="gpt-4o-mini",  # ✅ Corrigido para consistência
            api_key=self.api_key,
            temperature=temperature,
            max_tokens=1000,
            timeout=30      # ✅ Timeout de 20s para gpt-4o-mini
        )

    @agent
    def line_agent(self) -> Agent:
        """
        Create LINE agent for customer interaction and lead qualification.

        This agent is equipped with:
        - FAQ knowledge base for consórcio questions
        - Optimized temperature for consistent responses
        - Lead qualification capabilities

        Returns:
            Agent: Configured LINE agent
        """

        # Get agent config
        agents_config = self._get_agents_config()
        agent_config = agents_config["line_agent"]

        # Create agent with FAQ tool
        agent = Agent(
            role=agent_config["role"],
            goal=agent_config["goal"],
            backstory=agent_config["backstory"],
            llm=self._create_base_llm(temperature=0.7),
            allow_delegation=False,
            # ✅ Removidos parâmetros inválidos para Agent
        )

        logger.info("LINE agent created successfully with FAQ capabilities")
        return agent


    @task
    def qualify_lead(self) -> Task:
        """
        Create lead qualification task.

        Returns:
            Task: Configured lead qualification task with structured output
        """
        faq_tool = self._initialize_faq_system()

        tasks_config = self._get_tasks_config()
        task_config = tasks_config["qualify_lead"]

        return Task(
            agent=self.agent,
            description=task_config["description"],
            expected_output=task_config["expected_output"],
            tools=[faq_tool],
        )

    @task
    def answer_faq(self) -> Task:
        """
        Create FAQ answering task for qualified leads or urgent clients.

        This task is executed when:
        - Lead qualification is complete (is_complete=True)
        - Client shows urgency (urgency=True)

        Returns:
            Task: Configured FAQ answering task
        """

        # Initialize FAQ system
        faq_tool = self._initialize_faq_system()

        tasks_config = self._get_tasks_config()
        task_config = tasks_config["answer_faq"]

        return Task(
            agent=self.agent,
            description=task_config["description"],
            expected_output=task_config["expected_output"],
            tools=[faq_tool],
        )

    def _should_execute_faq_task(self, chat_state: Optional[ChatState] = None) -> bool:
        """
        Determine if FAQ task should be executed based on chat state.

        Args:
            chat_state: Current chat state from qualify_lead task

        Returns:
            bool: True if FAQ task should be executed
        """
        if not chat_state:
            return False

        return chat_state.is_complete

    def _initialize_precreated_crews(self):
        """
        Inicializa os crews pré-criados para otimização de performance.

        Cria duas instâncias de crews:
        1. Qualification Crew: Apenas task de qualificação
        2. Complete Crew: Qualificação + FAQ
        """
        if self._crews_initialized:
            return

        try:
            logger.info("Inicializando crews pré-criados...")

            # Crew apenas para qualificação
            self._qualification_crew = Crew(
                agents=[self.agent],
                tasks=[self.qualify_lead()],  # ✅ Corrigido: usar qualify_lead para qualificação
                process=Process.sequential,
                verbose=False,
                cache=True,
                memory=False,
            )

            self._crews_initialized = True
            logger.info("✅ Crews pré-criados inicializados com sucesso")

        except Exception as e:
            logger.error(f"❌ Erro ao inicializar crews pré-criados: {e}")
            raise

    def get_crew(self) -> Crew:
        self._initialize_precreated_crews()
        if self._qualification_crew is None:
            raise RuntimeError("Failed to initialize qualification crew")
        return self._qualification_crew
