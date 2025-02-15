#!/usr/bin/env python
from crewai.flow import Flow, listen, start, persist, router, or_
from crewai_lead_qualification_chatbot.crews.chat_crew.chat_crew import ChatCrew
from crewai_lead_qualification_chatbot.question_manager import QuestionManager
from crewai_lead_qualification_chatbot.models import ChatState
import gradio as gr
import uuid
from typing import List, Dict, Any
from datetime import datetime


@persist()
class ChatFlow(Flow[ChatState]):
    def __init__(self, persistence=None):
        super().__init__(persistence=persistence)
        self.question_manager = QuestionManager()

    def calculate_lead_score(self) -> Dict[str, Any]:
        """
        Calculate lead score based on industry standard metrics:
        - Budget alignment (30 points)
        - Timeline urgency (25 points)
        - Pre-approval status (20 points)
        - Agent exclusivity (15 points)
        - Motivation clarity (10 points)
        """
        score = 0
        reasons = []
        state_dict = self.state.model_dump()

        # Budget alignment (30 points)
        budget = str(state_dict.get("budget") or "0").replace("$", "").replace(",", "")
        try:
            budget_value = float(budget)
            if budget_value >= 500000:
                score += 30
                reasons.append("High budget range (30 points)")
            elif budget_value >= 300000:
                score += 20
                reasons.append("Medium budget range (20 points)")
            else:
                score += 10
                reasons.append("Lower budget range (10 points)")
        except ValueError:
            reasons.append("Could not evaluate budget (0 points)")

        # Timeline urgency (25 points)
        timeline = str(state_dict.get("timeline") or "").lower()
        if "immediate" in timeline or "1 month" in timeline:
            score += 25
            reasons.append("Immediate timeline (25 points)")
        elif "3 month" in timeline or "6 month" in timeline:
            score += 15
            reasons.append("Medium-term timeline (15 points)")
        else:
            score += 5
            reasons.append("Long-term timeline (5 points)")

        # Pre-approval status (20 points)
        pre_approved = str(state_dict.get("pre_approved") or "").lower()
        if "yes" in pre_approved:
            score += 20
            reasons.append("Pre-approved for mortgage (20 points)")
        elif "in process" in pre_approved:
            score += 10
            reasons.append("Pre-approval in process (10 points)")

        # Agent exclusivity (15 points)
        other_agents = str(state_dict.get("other_agents") or "").lower()
        if "no" in other_agents:
            score += 15
            reasons.append("Not working with other agents (15 points)")
        elif "considering" in other_agents:
            score += 5
            reasons.append("Considering other agents (5 points)")

        # Motivation clarity (10 points)
        motivation = str(state_dict.get("search_reason") or "").lower()
        if motivation and len(motivation) > 20:
            score += 10
            reasons.append("Clear motivation provided (10 points)")
        elif motivation:
            score += 5
            reasons.append("Some motivation indicated (5 points)")

        # Calculate lead quality
        quality = "Hot" if score >= 80 else "Warm" if score >= 50 else "Cold"

        return {
            "score": score,
            "quality": quality,
            "reasons": reasons,
            "timestamp": datetime.now().isoformat(),
        }

    @start()
    def initialize_chat(self):
        if not self.state.current_question_id:
            self.state.current_question_text, self.state.current_question_id = (
                self.question_manager.get_question("q1")
            )
            self.state.next_question_text, self.state.next_question_id = (
                self.question_manager.get_next_question("q1")
            )

            return "send_response_request"

        return "process_response_request"

    @router(initialize_chat)
    def route_request(self, classification: str):
        return classification

    @listen("process_response_request")
    def process_response(self):
        result = (
            ChatCrew()
            .crew()
            .kickoff(
                inputs={
                    "state": self.state.model_dump(),
                    "message": self.state.message,
                    "current_question_text": self.state.current_question_text,
                    "state": self.state.model_dump(),
                }
            )
        )

        self.state.message = ""

        if isinstance(result.pydantic, ChatState):
            new_state = result.pydantic.model_dump()
            self.state.message = new_state["message"]
            field_id = self.question_manager.get_field_id(
                self.state.current_question_id
            )

            # Check if the question was answered
            if new_state.get(field_id):
                # Update state fields individually
                for key, value in new_state.items():
                    if hasattr(self.state, key):
                        setattr(self.state, key, value)

                if self.question_manager.is_last_question(
                    self.state.current_question_id
                ):
                    self.state.is_complete = True
                else:
                    # Move to next question
                    self.state.current_question_id = self.state.next_question_id
                    self.state.current_question_text = self.state.next_question_text
                    self.state.next_question_text, self.state.next_question_id = (
                        self.question_manager.get_next_question(
                            self.state.current_question_id
                        )
                    )

    @listen(or_("send_response_request", process_response))
    def send_response(self):
        if self.state.is_complete:
            try:
                lead_score = self.calculate_lead_score()
                score_details = (
                    f"\n\nLead Score Analysis:"
                    f"\nOverall Score: {lead_score['score']}/100"
                    f"\nLead Quality: {lead_score['quality']}"
                    f"\nScoring Factors:"
                )
                for reason in lead_score["reasons"]:
                    score_details += f"\n- {reason}"

                return f"Thank you for completing the chat! Here's your lead qualification summary: {score_details}"
            except Exception as e:
                print(f"Error calculating lead score: {str(e)}")
                return "Thank you for completing the chat! An error occurred while calculating your lead score."

        return (
            self.state.message
            if self.state.message
            else self.state.current_question_text
        )


class ChatbotInterface:
    def __init__(self):
        self.chat_flows = {}
        self.chat_id = None

    def chat(self, message: str, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process chat messages and maintain conversation history"""
        if not self.chat_id or not message:
            # Initialize new chat session
            self.chat_id = str(uuid.uuid4())
            self.chat_flows[self.chat_id] = ChatFlow()
            response = self._process_message("", self.chat_id)
            return [{"role": "assistant", "content": response}]

        # Process user message
        response = self._process_message(message, self.chat_id)

        # Create a new history list to avoid modifying the input
        new_history = history.copy()
        new_history.append({"role": "user", "content": message})
        new_history.append({"role": "assistant", "content": response})
        return [{"role": "assistant", "content": response}]

    def _process_message(self, message: str, chat_id: str) -> str:
        """Process a message through the chat flow"""
        chat_flow = self.chat_flows[chat_id]

        print(f"Processing message: {message} for chat ID: {chat_id}")
        print(f"Chat flow: {chat_flow}")

        result = chat_flow.kickoff(
            inputs={
                "id": chat_id,
                "message": message,
            }
        )
        return result


def create_lead_qualification_chatbot() -> gr.Blocks:
    """Create and configure the lead qualification chatbot"""
    chatbot = ChatbotInterface()

    demo = gr.ChatInterface(
        chatbot.chat,
        chatbot=gr.Chatbot(
            label="Lead Qualification Chat",
            height=600,
            show_copy_button=True,
            type="messages",
        ),
        textbox=gr.Textbox(
            placeholder="Type your response here and press Enter",
            container=False,
            scale=7,
            show_label=False,
        ),
        title="Lead Qualification Chatbot",
        description="I'll help qualify you as a potential lead by asking a series of questions about your real estate needs.",
        theme="soft",
        examples=[
            "Hi, I'm looking to buy a property",
            "Hi, I'm looking to rent a property",
        ],
        type="messages",
    )

    return demo


def plot():
    chat_flow = ChatFlow()
    chat_flow.plot()


if __name__ == "__main__":
    chatbot = create_lead_qualification_chatbot()
    chatbot.launch(share=True)
