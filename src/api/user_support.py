"""User support API: the main API the front end talks to.

POST /api/user-support takes the user's question as a string and returns the
RAG-generated answer in one JSON response (no streaming).

The RAG call is not wired in yet: until it is, the endpoint returns 501 Not Implemented.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/user-support", tags=["user-support"])


class UserSupportRequest(BaseModel):
    """Request body of POST /api/user-support."""

    question: str = Field(min_length=1, description="The user's question.")


class UserSupportResponse(BaseModel):
    """Response of POST /api/user-support."""

    answer: str


@router.post("", response_model=UserSupportResponse)
def user_support_suggestion(body: UserSupportRequest):
    """Answer the user's question with the RAG-generated response."""
    # TODO: call the RAG pipeline with body.question and return its answer.
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "The user support answer is not implemented yet.")
