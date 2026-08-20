import sys
from pathlib import Path

import asyncio
import json

from fastapi.responses import StreamingResponse

from fastapi import FastAPI
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

app = FastAPI(
    title="AI DevOps Agent API",
    version="0.1.0",
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

    result = await orchestrator.run(request.message)

    return {
        "message": request.message,
        "result": result,
    }


@app.post("/investigate/stream")
async def investigate_stream(
    request: InvestigationRequest,
):

    queue = asyncio.Queue()

    async def event_callback(event: dict):
        await queue.put(event)

    async def run_investigation():

        try:

            result = await orchestrator.run(
                request.message,
                event_callback=event_callback,
            )

            await queue.put(
                {
                    "type": "result",
                    "result": result,
                }
            )

        except Exception as exc:

            await queue.put(
                {
                    "type": "error",
                    "message": str(exc),
                }
            )

        finally:

            await queue.put(
                {
                    "type": "done",
                }
            )

    async def event_generator():

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
