from fastapi import APIRouter

router = APIRouter(prefix="/server", tags=["server"])


@router.get("/live")
async def live() -> dict[str, str]:
    """
    Liveness: answers as long as the process is up.
    Public, so Docker and monitors can call it.
    """
    return {"status": "ok"}
