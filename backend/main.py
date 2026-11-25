"""FastAPI backend – thin proxy between the React frontend and Databricks Genie."""

import os
import logging

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from genie import GenieClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
WORKSPACE_HOST = os.getenv(
    "DATABRICKS_HOST", "https://dbc-c400ac32-73d9.cloud.databricks.com"
)
SPACE_ID = os.getenv("GENIE_SPACE_ID", "01f1e779eb1a1ff59c3deb83fa8f6810")
CATALOG = os.getenv("GENIE_CATALOG", "")
genie = GenieClient(WORKSPACE_HOST, SPACE_ID)

# Logging – never log tokens, SQL rows, or question text (student data).
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("genie-backend")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Genie Chat Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

http_client = httpx.AsyncClient(timeout=60)


def _token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")
    return authorization.removeprefix("Bearer ").strip()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


class AskRequest(BaseModel):
    question: str
    conversation_id: str | None = None


class AskResponse(BaseModel):
    conversation_id: str
    message_id: str


@app.get("/api/space")
async def space_info(authorization: str | None = Header(None)):
    token = _token(authorization)
    try:
        return await genie.get_space_info(http_client, token, catalog=CATALOG)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise HTTPException(401, "Token expired or invalid – please sign in again.")
        log.error("Genie space info error: %s", exc.response.status_code)
        raise HTTPException(502, "Could not fetch space info")


@app.post("/api/ask", response_model=AskResponse)
async def ask(body: AskRequest, authorization: str | None = Header(None)):
    token = _token(authorization)
    try:
        if body.conversation_id:
            message_id = await genie.send_followup(
                http_client, token, body.conversation_id, body.question
            )
            return AskResponse(conversation_id=body.conversation_id, message_id=message_id)
        else:
            cid, mid = await genie.start_conversation(http_client, token, body.question)
            return AskResponse(conversation_id=cid, message_id=mid)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise HTTPException(401, "Token expired or invalid – please sign in again.")
        log.error("Genie API error: %s", exc.response.status_code)
        raise HTTPException(502, "Genie API error")


@app.get("/api/status/{conversation_id}/{message_id}")
async def status(
    conversation_id: str, message_id: str, authorization: str | None = Header(None)
):
    token = _token(authorization)
    try:
        message_data = await genie.get_message(
            http_client, token, conversation_id, message_id
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise HTTPException(401, "Token expired or invalid – please sign in again.")
        log.error("Genie poll error: %s", exc.response.status_code)
        raise HTTPException(502, "Genie API error")

    # Only fetch query result when the message is done
    query_result = None
    if message_data.get("status") == "COMPLETED":
        for att in message_data.get("attachments", []):
            if "query" in att:
                aid = att.get("attachment_id")
                if aid:
                    query_result = await genie.get_query_result(
                        http_client, token, conversation_id, message_id, aid
                    )
                break

    return genie.normalize(message_data, query_result)


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------

@app.on_event("shutdown")
async def shutdown():
    await http_client.aclose()
