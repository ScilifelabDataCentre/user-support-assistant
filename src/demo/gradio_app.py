"""Gradio demo: a chat page for trying the user support assistant in the browser.

app.py mounts it on the FastAPI app at /demo, so it runs in the same process as the
API (one command: python main.py) and is served at http://127.0.0.1:8000/demo.

It answers with the same LLM chat service as POST /api/user-support (ai_agents/llm_chat.py)
and the RAG graph built once at startup, so the demo shows exactly what the API returns.
Single-turn only: the page looks like a chat, but each question is answered on its own.
The RAG graph and POST /api/user-support take one question and no chat history, so a
follow-up such as "What about Shiny?" is retrieved and answered without the earlier turns.

The demo is for people. Other services call POST /api/user-support, not Gradio's own API.
"""

import gradio as gr

from ai_agents.llm_chat import llm_chat

# Questions shown under the chat box, to try with one click
EXAMPLES = [
    "How do I deploy a Streamlit app on SciLifeLab Serve?",
    "What are the resource limits for an app?",
    "How do I make my app private?",
]


def build_demo(app):
    """Build the Gradio chat page; it reads the RAG graph from app.state when a question
    comes in (app.py's lifespan creates it at startup, after this page is built)."""

    async def answer(message, history):
        """Answer the user's message; the answer already ends with its "Sources:" list."""
        # Single-turn: Gradio passes the earlier turns in history, but they are not used;
        # only this message goes to the RAG graph (see the module docstring).
        rag_graph = app.state.rag_graph
        answer_text, _sources = await llm_chat(rag_graph, message)
        return answer_text

    demo = gr.ChatInterface(
        fn=answer,
        title="User Support Assistant",
        description="Ask a question about SciLifeLab Serve. Each question is answered on its own.",
        examples=EXAMPLES,
        analytics_enabled=False,
    )
    return demo
