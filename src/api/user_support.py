"""User support API: the main API the front end talks to.

POST /api/user-support takes the user's question as a string and returns one JSON
response (no streaming):
  - answer: the full RAG-generated answer, followed by a "Sources:" list of the
    documentation sections it uses, numbered 1..n, with their links;
  - sources: the metadata of those sections, each with its "number" in that list.

The answer comes from the LLM chat service (ai_agents/llm_chat.py), which runs the
RAG graph built once at startup (see app.py).
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ai_agents.llm_chat import llm_chat

router = APIRouter(prefix="/user-support", tags=["user-support"])


class UserSupportRequest(BaseModel):
    """Request body of POST /api/user-support."""

    question: str = Field(min_length=1, description="The user's question.")


class Source(BaseModel):
    """A documentation section the answer uses."""

    number: int = Field(description='Its number in the "Sources:" list, 1..n.')
    page_title: str = Field(description="Title of the docs page.")
    headings: list[str] = Field(description="Heading path of the section within the page.")
    section_url: str = Field(description="Link to the section on the SciLifeLab Serve site.")
    source_url: str = Field(description="Link to the whole docs page.")
    type: str = Field(description='"section", or "faq" for an FAQ question + answer.')


class UserSupportResponse(BaseModel):
    """Response of POST /api/user-support."""

    answer: str = Field(description='The full answer, followed by its "Sources:" list.')
    sources: list[Source] = Field(description="Metadata of the sections the answer uses.")


@router.post("", response_model=UserSupportResponse)
def user_support_suggestion(body: UserSupportRequest, request: Request):
    """Answer the user's question with the RAG-generated response and its sources."""
    rag_graph = request.app.state.rag_graph
    answer, sources = llm_chat(rag_graph, body.question)
    return UserSupportResponse(answer=answer, sources=sources)
