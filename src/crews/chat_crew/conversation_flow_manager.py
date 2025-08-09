from enum import Enum
from typing import Optional, List, Dict, Any
from database.models import ChatState
import re
import logging

logger = logging.getLogger(__name__)


class ConversationIntent(Enum):
    """Possible conversation intents."""
    FAQ = "faq"
    SIMULATION = "simulation"
    QUALIFICATION = "qualification"
    MIXED = "mixed"
    GREETING = "greeting"
    UNKNOWN = "unknown"


class ConversationStage(Enum):
    """Conversation stages in the sales funnel."""
    INITIAL = "initial"
    RAPPORT_BUILDING = "rapport_building"
    NEED_DISCOVERY = "need_discovery"
    PRESENTATION = "presentation"
    OBJECTION_HANDLING = "objection_handling"
    QUALIFICATION = "qualification"
    CLOSING = "closing"
    FOLLOW_UP = "follow_up"


class ConversationFlowManager:
    """
    Manages conversation flow and determines appropriate tasks to execute.

    This class acts as an intelligent orchestrator that:
    1. Analyzes user messages to detect intent
    2. Determines conversation stage
    3. Decides which tasks should be executed
    4. Manages flow between different conversation phases
    """

    def __init__(self):
        """Initialize the flow manager with intent detection patterns."""
        self.faq_patterns = [
            r'\b(como funciona|o que é|quais são|qual a|quanto tempo|quando)\b',
            r'\b(dúvida|pergunta|não entendi|explica|esclarece)\b',
            r'\b(taxa|juros|lance|contemplação|sorteio)\b',
            r'\b(consórcio|grupo|carta|parcela)\b'
        ]

        self.simulation_patterns = [
            r'\b(simula|simulação|quanto fica|valor|preço|custo)\b',
            r'\b(opções|planos|modalidades|cartas)\b',
            r'\b(carro|veículo|moto|imóvel|casa)\b',
            r'\b(R\$|\d+\.?\d*\s*(mil|reais))\b'
        ]

        self.qualification_patterns = [
            r'\b(interessado|quero|vou|sim|aceito|concordo)\b',
            r'\b(meu nome|me chamo|sou|dados|informações)\b',
            r'\b(contato|telefone|email|endereço)\b',
            r'\b(renda|salário|profissão|trabalho)\b'
        ]

    def analyze_message_intent(self, message: str, chat_state: Optional[ChatState] = None) -> ConversationIntent:
        """
        Analyze user message to determine primary intent.

        Args:
            message: User's message
            chat_state: Current chat state

        Returns:
            ConversationIntent: Detected intent
        """
        message_lower = message.lower()

        # Check for greeting patterns
        if self._is_greeting(message_lower):
            return ConversationIntent.GREETING

        # Count pattern matches for each intent
        faq_score = sum(1 for pattern in self.faq_patterns if re.search(pattern, message_lower))
        simulation_score = sum(1 for pattern in self.simulation_patterns if re.search(pattern, message_lower))
        qualification_score = sum(1 for pattern in self.qualification_patterns if re.search(pattern, message_lower))

        # Determine intent based on highest score
        scores = {
            ConversationIntent.FAQ: faq_score,
            ConversationIntent.SIMULATION: simulation_score,
            ConversationIntent.QUALIFICATION: qualification_score
        }

        # Check for mixed intent (multiple high scores)
        high_scores = [intent for intent, score in scores.items() if score >= 2]
        if len(high_scores) > 1:
            return ConversationIntent.MIXED

        # Return intent with highest score
        max_intent = max(scores.keys(), key=lambda x: scores[x])
        if scores[max_intent] > 0:
            return max_intent

        return ConversationIntent.UNKNOWN

    def determine_conversation_stage(self, chat_state: Optional[ChatState], intent: ConversationIntent) -> ConversationStage:
        """
        Determine current conversation stage based on state and intent.

        Args:
            chat_state: Current chat state
            intent: Detected conversation intent

        Returns:
            ConversationStage: Current stage in conversation
        """
        if not chat_state:
            return ConversationStage.INITIAL

        # If qualification is complete, move to closing
        if hasattr(chat_state, 'is_complete') and chat_state.is_complete:
            return ConversationStage.CLOSING

        # If some qualification data exists, we're in qualification stage
        if self._has_qualification_data(chat_state):
            return ConversationStage.QUALIFICATION

        # Based on intent, determine stage
        stage_mapping = {
            ConversationIntent.GREETING: ConversationStage.INITIAL,
            ConversationIntent.FAQ: ConversationStage.RAPPORT_BUILDING,
            ConversationIntent.SIMULATION: ConversationStage.PRESENTATION,
            ConversationIntent.QUALIFICATION: ConversationStage.QUALIFICATION,
            ConversationIntent.MIXED: ConversationStage.NEED_DISCOVERY
        }

        return stage_mapping.get(intent, ConversationStage.RAPPORT_BUILDING)

    def get_recommended_tasks(self, intent: ConversationIntent, stage: ConversationStage,
                            chat_state: Optional[ChatState] = None) -> List[str]:
        """
        Get recommended tasks to execute based on intent and stage.

        Args:
            intent: Conversation intent
            stage: Conversation stage
            chat_state: Current chat state

        Returns:
            List[str]: List of task names to execute
        """
        # Priority-based task selection
        tasks = []

        # Always include qualify_lead as it handles all conversation flow
        tasks.append("qualify_lead")

        # Add specific tasks based on intent and stage
        if intent == ConversationIntent.FAQ or stage == ConversationStage.RAPPORT_BUILDING:
            tasks.append("answer_faq")

        elif intent == ConversationIntent.SIMULATION or stage == ConversationStage.PRESENTATION:
            tasks.append("simulate_options")

        elif intent == ConversationIntent.MIXED:
            # For mixed intent, add both FAQ and simulation
            tasks.extend(["answer_faq", "simulate_options"])

        # Remove duplicates while preserving order
        return list(dict.fromkeys(tasks))

    def should_execute_parallel_tasks(self, intent: ConversationIntent, tasks: List[str]) -> bool:
        """
        Determine if tasks can be executed in parallel.

        Args:
            intent: Conversation intent
            tasks: List of tasks to execute

        Returns:
            bool: True if tasks can run in parallel
        """
        # Only allow parallel execution for mixed intent with multiple tasks
        return intent == ConversationIntent.MIXED and len(tasks) > 1

    def get_task_priority(self, task_name: str, intent: ConversationIntent) -> int:
        """
        Get priority for task execution (lower number = higher priority).

        Args:
            task_name: Name of the task
            intent: Conversation intent

        Returns:
            int: Priority score
        """
        priority_map = {
            "qualify_lead": 1,  # Always highest priority
            "answer_faq": 2,
            "simulate_options": 3
        }

        # Adjust priority based on intent
        if intent == ConversationIntent.FAQ and task_name == "answer_faq":
            return 1
        elif intent == ConversationIntent.SIMULATION and task_name == "simulate_options":
            return 1

        return priority_map.get(task_name, 10)

    def _is_greeting(self, message: str) -> bool:
        """Check if message is a greeting."""
        greeting_patterns = [
            r'\b(oi|olá|ola|hey|eai|e ai|bom dia|boa tarde|boa noite)\b',
            r'\b(tchau|até logo|falou|vlw|obrigad)\b'
        ]
        return any(re.search(pattern, message) for pattern in greeting_patterns)

    def _has_qualification_data(self, chat_state: ChatState) -> bool:
        """Check if chat state has any qualification data."""
        if not chat_state:
            return False

        qualification_fields = ['nome', 'cpf', 'email', 'renda', 'profissao']
        return any(getattr(chat_state, field, None) for field in qualification_fields)

    def log_flow_decision(self, message: str, intent: ConversationIntent,
                         stage: ConversationStage, tasks: List[str]) -> None:
        """Log flow decisions for debugging and optimization."""
        logger.info(f"Flow Decision - Message: '{message[:50]}...', "
                   f"Intent: {intent.value}, Stage: {stage.value}, "
                   f"Tasks: {tasks}")
