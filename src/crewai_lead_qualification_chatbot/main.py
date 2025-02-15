#!/usr/bin/env python
from crewai.flow import Flow, listen, start, persist, router, or_
from crewai_lead_qualification_chatbot.crews.chat_crew.chat_crew import ChatCrew
from crewai_lead_qualification_chatbot.question_manager import QuestionManager
from crewai_lead_qualification_chatbot.models import ChatState
import gradio as gr
import uuid


@persist()
class ChatFlow(Flow[ChatState]):
    def __init__(self, persistence=None):
        super().__init__(persistence=persistence)
        self.question_manager = QuestionManager()

    @start()
    def initialize_chat(self):
        print("Initializing chat...")
        """Initialize chat with first question if no state exists"""
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
        print("Routing request...")
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
                    "state": self.state.model_dump(),
                }
            )
        )

        self.state.message = ""

        if isinstance(result.pydantic, ChatState):
            new_state = result.pydantic.model_dump()
            print(f"New state message: {new_state['message']}")
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

        print(f"Message: {self.state.message}")
        return (
            self.state.message
            if self.state.message
            else self.state.current_question_text
        )


class ChatbotInterface:
    def __init__(self):
        self.chat_flows = {}

    def respond(self, message, chat_id, history):
        if not chat_id:
            chat_id = str(uuid.uuid4())
            self.chat_flows[chat_id] = ChatFlow()
            # Start with the first question
            response, _ = self.process_message("", chat_id)
            history.append(("", response))
            return "", chat_id, history

        response, _ = self.process_message(message, chat_id)
        history.append((message, response))
        return "", chat_id, history

    def process_message(self, message, chat_id):
        if chat_id not in self.chat_flows:
            self.chat_flows[chat_id] = ChatFlow()

        chat_flow = self.chat_flows[chat_id]

        result = chat_flow.kickoff(
            inputs={
                "id": chat_id,
                "message": message,
            }
        )

        return result, chat_id


def create_lead_qualification_chatbot():
    chatbot = ChatbotInterface()

    with gr.Blocks(title="Lead Qualification Chatbot") as demo:
        gr.Markdown("# Lead Qualification Chatbot")
        gr.Markdown(
            "I'll help qualify you as a potential lead by asking a series of questions."
        )

        with gr.Row():
            with gr.Column(scale=1):
                chat_id = gr.State()  # Hidden state to track chat session
                history = gr.State([])  # Chat history state
                chatbox = gr.Chatbot(
                    label="Chat History",
                    height=400,
                    show_copy_button=True,
                )
                msg = gr.Textbox(
                    label="Your Message",
                    placeholder="Type your message here and press Enter",
                    show_label=False,
                )
                clear = gr.ClearButton([msg, chatbox])

        msg.submit(
            fn=chatbot.respond,
            inputs=[msg, chat_id, history],
            outputs=[msg, chat_id, chatbox],
        )

        # Start the chat automatically when loaded
        demo.load(
            fn=chatbot.respond,
            inputs=[msg, chat_id, history],
            outputs=[msg, chat_id, chatbox],
        )

    return demo


def plot():
    chat_flow = ChatFlow()
    chat_flow.plot()


if __name__ == "__main__":
    chatbot = create_lead_qualification_chatbot()
    chatbot.launch(share=True)
