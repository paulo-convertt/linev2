#!/usr/bin/env python
from crewai.flow import Flow, listen, start, persist, router, or_
from crewai_lead_qualification_chatbot.crews.chat_crew.chat_crew import ChatCrew
from crewai_lead_qualification_chatbot.question_manager import QuestionManager
from crewai_lead_qualification_chatbot.models import ChatState


@persist()
class ChatFlow(Flow[ChatState]):
    def __init__(self, persistence=None):
        super().__init__(persistence=persistence)
        self.question_manager = QuestionManager()

    @start()
    def initialize_chat(self):
        print("Initializing chat...")
        print(f"Current state: {self.state.model_dump()}")

        """Initialize chat with first question if no state exists"""
        if not self.state.current_question_id:
            self.state.current_question_text, self.state.current_question_id = (
                self.question_manager.get_question("q1")
            )
            self.state.next_question_text, self.state.next_question_id = (
                self.question_manager.get_next_question("q1")
            )
            print(f"Starting chat with question: {self.state.current_question_text}")
            return "send_response_request"

        return "process_response_request"

    @router(initialize_chat)
    def route_request(self, classification: str):
        print("Routing request...")
        print(f"Current question ID: {self.state.current_question_id}")
        print(f"Current question: {self.state.current_question_text}")
        print(f"Next question: {self.state.next_question_text}")

        return classification

    @listen("process_response_request")
    def process_response(self):
        print("Processing response...")
        result = (
            ChatCrew()
            .crew()
            .kickoff(
                inputs={
                    "state": self.state.model_dump(),
                    "message": self.state.message,
                }
            )
        )

        if isinstance(result.pydantic, ChatState):
            new_state = result.pydantic.model_dump()
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
                    print("Chat completed!")
                else:
                    # Move to next question
                    self.state.current_question_id = self.state.next_question_id
                    self.state.current_question_text = self.state.next_question_text
                    self.state.next_question_text, self.state.next_question_id = (
                        self.question_manager.get_next_question(
                            self.state.current_question_id
                        )
                    )
                    print(
                        f"Moving to next question: {self.state.current_question_text}"
                    )
            else:
                print(
                    f"Question not answered properly, asking again: {self.state.current_question_text}"
                )

    @listen(or_("send_response_request", process_response))
    def send_response(self):
        print("Sending response...")
        if self.state.is_complete:
            return f"Thank you for completing the chat! Here are your responses: {self.state.model_dump()}"
        return self.state.message


def kickoff():
    chat_flow = ChatFlow()
    result = chat_flow.kickoff(
        inputs={
            "id": "7185dfae-590c-4751-be72-eee2122d15a6",
            "message": "Lennex Zinyando",
        }
    )
    print(f"Chatbot: {result}")


def plot():
    chat_flow = ChatFlow()
    chat_flow.plot()


if __name__ == "__main__":
    kickoff()
