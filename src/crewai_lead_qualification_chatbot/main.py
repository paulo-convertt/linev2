#!/usr/bin/env python
from typing import Optional
from pydantic import BaseModel
from crewai.flow import Flow, listen, start, persist
from crewai_lead_qualification_chatbot.crews.chat_crew.chat_crew import ChatCrew


class LeadData(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    property_type: Optional[str] = None
    price_range: Optional[str] = None
    location: Optional[str] = None
    timeline: Optional[str] = None
    financing: Optional[str] = None
    other_agents: Optional[str] = None
    search_reason: Optional[str] = None


class ChatState(BaseModel):
    message: str = ""
    lead_data: LeadData = LeadData()
    current_question: str = ""
    next_question: str = ""


@persist()
class ChatFlow(Flow[ChatState]):
    @start()
    def qualify_lead(self):
        print("Starting lead qualification conversation")
        result = (
            ChatCrew()
            .crew()
            .kickoff(
                inputs={
                    "id": self.state.id,
                    "lead_data": self.state.lead_data,
                    "current_question": self.state.current_question,
                    "next_question": self.state.next_question,
                }
            )
        )
        print("Conversation completed")
        self.state.message = result.raw

    @listen(qualify_lead)
    def extract_lead_data(self):
        print("Extracting lead data from conversation")
        # Here we would typically use an LLM to extract structured data
        # from the conversation, but for now we'll just store the raw conversation
        self.state.lead_data = LeadData(
            full_name="Extracted from conversation",
            email="Extracted from conversation",
            phone="Extracted from conversation",
            property_type="Extracted from conversation",
            price_range="Extracted from conversation",
            location="Extracted from conversation",
            timeline="Extracted from conversation",
            financing="Extracted from conversation",
            other_agents="Extracted from conversation",
            search_reason="Extracted from conversation",
        )
        print(f"Lead data extracted: {self.state.lead_data}")


def kickoff():
    chat_flow = ChatFlow()
    chat_flow.kickoff(inputs={"id": "1fc0f9f6-989e-4137-a7f3-e30b12e550h0"})


def plot():
    chat_flow = ChatFlow()
    chat_flow.plot()


if __name__ == "__main__":
    kickoff()
