import asyncio
import json
import sys

from pathlib import Path

from fastapi import (
    FastAPI,
    HTTPException,
)

from fastapi.responses import (
    StreamingResponse,
)

from pydantic import BaseModel

AGENT_PATH = Path(__file__).resolve().parents[1] / "agent"

sys.path.insert(
    0,
    str(AGENT_PATH),
)


from agents.database_agent import DatabaseAgent
from agents.docker_agent import DockerAgent
from agents.network_agent import NetworkAgent
from agents.orchestrator import Orchestrator

from history import (
    complete_investigation,
    create_investigation,
    fail_investigation,
    get_investigation,
    init_history_database,
    list_investigations,
    save_event,
)

app = FastAPI(
    title=("AI DevOps Agent API"),
    version="0.2.0",
)


docker_agent = None
database_agent = None
network_agent = None
orchestrator = None


class InvestigationRequest(BaseModel):
    message: str


@app.on_event("startup")
async def startup():

    global docker_agent
    global database_agent
    global network_agent
    global orchestrator

    print("[API] Initializing history database...")

    await init_history_database()

    print("[API] History database ready.")

    print("[API] Starting agents...")

    docker_agent = DockerAgent()

    database_agent = DatabaseAgent()

    network_agent = NetworkAgent()

    await docker_agent.connect()

    await database_agent.connect()

    await network_agent.connect()

    orchestrator = Orchestrator(
        docker_agent=docker_agent,
        database_agent=database_agent,
        network_agent=network_agent,
    )

    print("[API] Agents ready.")


@app.on_event("shutdown")
async def shutdown():

    print("[API] Closing agents...")

    if network_agent:

        await network_agent.close()

    if database_agent:

        await database_agent.close()

    if docker_agent:

        await docker_agent.close()


@app.get("/health")
async def health():

    return {
        "status": "ok",
        "service": "ai-devops-api",
    }


@app.post("/investigate")
async def investigate(
    request: InvestigationRequest,
):

    diagnosis = await orchestrator.run(request.message)

    return {
        "message": request.message,
        "diagnosis": diagnosis,
        "result": diagnosis.get(
            "narrative",
            "",
        ),
    }


@app.post("/investigate/stream")
async def investigate_stream(
    request: InvestigationRequest,
):

    investigation = await create_investigation(request.message)

    investigation_id = investigation.id

    queue = asyncio.Queue()

    sequence = 0

    async def event_callback(
        event: dict,
    ):

        nonlocal sequence

        sequence += 1

        await save_event(
            investigation_id,
            sequence,
            event,
        )

        await queue.put(event)

    async def run_investigation():

        try:

            diagnosis = await orchestrator.run(
                request.message,
                event_callback=event_callback,
            )

            await complete_investigation(
                investigation_id,
                diagnosis,
            )

            await queue.put(
                {
                    "type": "result",
                    "investigation_id": investigation_id,
                    "diagnosis": diagnosis,
                    "result": diagnosis.get(
                        "narrative",
                        "",
                    ),
                }
            )

        except Exception as exc:

            error_message = str(exc)

            await fail_investigation(
                investigation_id,
                error_message,
            )

            await queue.put(
                {
                    "type": "error",
                    "investigation_id": investigation_id,
                    "message": error_message,
                }
            )

        finally:

            await queue.put(
                {
                    "type": "done",
                    "investigation_id": investigation_id,
                }
            )

    async def event_generator():

        yield (
            "data: "
            + json.dumps(
                {
                    "type": "investigation_created",
                    "investigation_id": investigation_id,
                }
            )
            + "\n\n"
        )

        task = asyncio.create_task(run_investigation())

        try:

            while True:

                event = await queue.get()

                yield ("data: " + json.dumps(event) + "\n\n")

                if event.get("type") == "done":
                    break

        finally:

            await task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/investigations")
async def investigations():

    return await list_investigations()


@app.get("/investigations/{investigation_id}")
async def investigation_detail(
    investigation_id: str,
):

    investigation = await get_investigation(investigation_id)

    if investigation is None:

        raise HTTPException(
            status_code=404,
            detail=("Investigation not found"),
        )

    return investigation
