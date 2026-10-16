"""Health check API.

GET /health returns 200 {"status": "ok"} while the app is running, so a deployment
(load balancer, Kubernetes, uptime monitor) can check that the service is up.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class Health(BaseModel):
    """Response of GET /health."""

    status: str


@router.get("/health", response_model=Health)
def health():
    """Return {"status": "ok"} while the app is running."""
    return Health(status="ok")
