"""
Spike script: ask the Genie space a starter question, poll to completion,
and print the normalized response shape.

Usage:
    export DATABRICKS_TOKEN="your-token-here"
    python spike.py
"""

import os
import sys
import time
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

WORKSPACE_HOST = "https://dbc-c400ac32-73d9.cloud.databricks.com"
SPACE_ID = "01f1e779eb1a1ff59c3deb83fa8f6810"
QUESTION = "What share of students admitted in each school year are still enrolled or have graduated?"

FINAL_STATUSES = {"COMPLETED", "FAILED", "CANCELLED"}
POLL_INTERVAL = 1.5  # seconds


def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def start_conversation(client: httpx.Client, token: str) -> tuple[str, str]:
    url = f"{WORKSPACE_HOST}/api/2.0/genie/spaces/{SPACE_ID}/start-conversation"
    resp = client.post(url, headers=headers(token), json={"content": QUESTION})
    resp.raise_for_status()
    data = resp.json()
    print("=== START CONVERSATION RESPONSE ===")
    print(json.dumps(data, indent=2))
    conversation_id = data.get("conversation_id") or data["id"]
    message_id = data.get("message_id")
    # message_id might be nested
    if not message_id:
        messages = data.get("messages", [])
        if messages:
            message_id = messages[0].get("id") or messages[0].get("message_id")
    if not message_id:
        print("WARNING: could not find message_id in response, dumping full response above")
        sys.exit(1)
    return conversation_id, message_id


def poll_message(client: httpx.Client, token: str, conversation_id: str, message_id: str) -> dict:
    url = f"{WORKSPACE_HOST}/api/2.0/genie/spaces/{SPACE_ID}/conversations/{conversation_id}/messages/{message_id}"
    while True:
        resp = client.get(url, headers=headers(token))
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")
        print(f"  status: {status}")
        if status in FINAL_STATUSES:
            return data
        time.sleep(POLL_INTERVAL)


def fetch_query_result(client: httpx.Client, token: str, conversation_id: str, message_id: str, attachment_id: str) -> dict | None:
    # Try the two known endpoint patterns
    paths = [
        f"/api/2.0/genie/spaces/{SPACE_ID}/conversations/{conversation_id}/messages/{message_id}/attachments/{attachment_id}/query-result",
        f"/api/2.0/genie/spaces/{SPACE_ID}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}",
    ]
    for path in paths:
        url = f"{WORKSPACE_HOST}{path}"
        resp = client.get(url, headers=headers(token))
        if resp.status_code == 200:
            print(f"  query-result path that worked: {path}")
            return resp.json()
        print(f"  tried {path} -> {resp.status_code}")
    return None


def normalize(message_data: dict, query_result: dict | None) -> dict:
    """Build the shape the backend will return to the frontend."""
    attachments = message_data.get("attachments", [])

    text = None
    sql = None
    description = None
    attachment_id = None
    statement_id = None
    suggested = []

    for att in attachments:
        # Attachments are identified by which key they carry, not a "type" field
        if "query" in att:
            query = att["query"]
            sql = query.get("query")
            description = query.get("description")
            attachment_id = att.get("attachment_id")
            statement_id = query.get("statement_id")
        elif "text" in att:
            text_obj = att["text"]
            purpose = text_obj.get("purpose", "")
            if purpose == "TEXT_ATTACHMENT_PURPOSE_ANSWER":
                text = text_obj.get("content")
            # skip FOLLOW_UP_QUESTION texts
        elif "suggested_questions" in att:
            suggested = att["suggested_questions"].get("questions", [])

    result = None
    if query_result:
        # The result may be nested under "statement_response"
        sr = query_result.get("statement_response", query_result)
        manifest = sr.get("manifest", {})
        columns_raw = manifest.get("schema", {}).get("columns", [])
        columns = [{"name": c.get("name"), "type": c.get("type_name", c.get("type_text", ""))} for c in columns_raw]
        rows = sr.get("result", {}).get("data_array", [])
        row_count = manifest.get("total_row_count") or sr.get("row_count") or len(rows)
        truncated = manifest.get("truncated", False)
        result = {
            "columns": columns,
            "rows": rows,
            "row_count": row_count,
            "truncated": truncated,
        }

    return {
        "status": message_data.get("status"),
        "text": text,
        "description": description,
        "sql": sql,
        "statement_id": statement_id,
        "attachment_id": attachment_id,
        "result": result,
        "suggested_questions": suggested,
    }


def main():
    token = os.environ.get("DATABRICKS_TOKEN")
    if not token:
        print("Set DATABRICKS_TOKEN env var first.")
        print('  export DATABRICKS_TOKEN="dapi..."')
        sys.exit(1)

    with httpx.Client(timeout=60) as client:
        print(f"Question: {QUESTION}\n")

        print("1) Starting conversation...")
        conversation_id, message_id = start_conversation(client, token)
        print(f"   conversation_id: {conversation_id}")
        print(f"   message_id: {message_id}\n")

        print("2) Polling for completion...")
        message_data = poll_message(client, token, conversation_id, message_id)
        print()

        print("=== RAW MESSAGE RESPONSE ===")
        print(json.dumps(message_data, indent=2))
        print()

        # Try to fetch query result if there's a query attachment
        query_result = None
        for att in message_data.get("attachments", []):
            if "query" in att:
                aid = att.get("attachment_id")
                if aid:
                    print(f"3) Fetching query result for attachment {aid}...")
                    query_result = fetch_query_result(client, token, conversation_id, message_id, aid)
                    if query_result:
                        print("\n=== RAW QUERY RESULT (first 500 chars) ===")
                        raw = json.dumps(query_result, indent=2)
                        print(raw[:500])
                        if len(raw) > 500:
                            print(f"  ... ({len(raw)} chars total)")
                    print()
                break

        print("=== NORMALIZED OUTPUT ===")
        normalized = normalize(message_data, query_result)
        print(json.dumps(normalized, indent=2))


if __name__ == "__main__":
    main()
