"""Thin client for the Databricks Genie Conversation REST API."""

import httpx

FINAL_STATUSES = {"COMPLETED", "FAILED", "CANCELLED"}


class GenieClient:
    def __init__(self, workspace_host: str, space_id: str):
        self.base = workspace_host.rstrip("/")
        self.space_id = space_id

    def _url(self, path: str) -> str:
        return f"{self.base}/api/2.0/genie/spaces/{self.space_id}{path}"

    def _headers(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # -- API calls ----------------------------------------------------------

    async def get_space_info(self, client: httpx.AsyncClient, token: str, catalog: str = "") -> dict:
        """Fetch space metadata and tables from Databricks."""
        resp = await client.get(
            self._url(""),
            headers=self._headers(token),
        )
        resp.raise_for_status()
        data = resp.json()

        # Fetch tables from Unity Catalog if catalog is provided
        tables: list[str] = []
        if catalog and "." in catalog:
            catalog_name, schema_name = catalog.split(".", 1)
            uc_url = f"{self.base}/api/2.1/unity-catalog/tables"
            uc_resp = await client.get(
                uc_url,
                headers=self._headers(token),
                params={"catalog_name": catalog_name, "schema_name": schema_name},
            )
            if uc_resp.status_code == 200:
                uc_data = uc_resp.json()
                tables = [
                    {
                        "name": t["name"],
                        "type": t.get("table_type", "TABLE"),
                        "column_count": len(t.get("columns", [])),
                        "comment": t.get("comment", ""),
                    }
                    for t in uc_data.get("tables", [])
                ]

        return {
            "space_id": self.space_id,
            "space_name": data.get("title", data.get("name", "Genie Space")),
            "description": data.get("description", ""),
            "catalog": catalog,
            "tables": tables,
        }

    async def start_conversation(
        self, client: httpx.AsyncClient, token: str, question: str
    ) -> tuple[str, str]:
        resp = await client.post(
            self._url("/start-conversation"),
            headers=self._headers(token),
            json={"content": question},
        )
        resp.raise_for_status()
        data = resp.json()
        conversation_id = data.get("conversation_id")
        message_id = data.get("message_id")
        return conversation_id, message_id

    async def send_followup(
        self, client: httpx.AsyncClient, token: str, conversation_id: str, question: str
    ) -> str:
        resp = await client.post(
            self._url(f"/conversations/{conversation_id}/messages"),
            headers=self._headers(token),
            json={"content": question},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("message_id") or data.get("id")

    async def get_message(
        self, client: httpx.AsyncClient, token: str, conversation_id: str, message_id: str
    ) -> dict:
        resp = await client.get(
            self._url(f"/conversations/{conversation_id}/messages/{message_id}"),
            headers=self._headers(token),
        )
        resp.raise_for_status()
        return resp.json()

    async def get_query_result(
        self,
        client: httpx.AsyncClient,
        token: str,
        conversation_id: str,
        message_id: str,
        attachment_id: str,
    ) -> dict | None:
        url = self._url(
            f"/conversations/{conversation_id}/messages/{message_id}"
            f"/attachments/{attachment_id}/query-result"
        )
        resp = await client.get(url, headers=self._headers(token))
        if resp.status_code == 200:
            return resp.json()
        return None

    # -- Normalize ----------------------------------------------------------

    @staticmethod
    def normalize(message_data: dict, query_result: dict | None) -> dict:
        """Turn raw Genie JSON into the shape the frontend expects."""
        attachments = message_data.get("attachments", [])

        text = None
        sql = None
        description = None
        attachment_id = None
        statement_id = None
        suggested: list[str] = []
        tables_used: list[str] = []

        for att in attachments:
            if "query" in att:
                q = att["query"]
                sql = q.get("query")
                description = q.get("description")
                attachment_id = att.get("attachment_id")
                statement_id = q.get("statement_id")
                # Extract table names from THOUGHT_TYPE_DATA_SOURCING
                for thought in q.get("thoughts", []):
                    if thought.get("thought_type") == "THOUGHT_TYPE_DATA_SOURCING":
                        content = thought.get("content", "")
                        for line in content.splitlines():
                            line = line.strip().lstrip("- ").strip()
                            if line:
                                # e.g. "ld_analytics.kschools.student_information" -> "student_information"
                                tables_used.append(line.split(".")[-1])
            elif "text" in att:
                t = att["text"]
                if t.get("purpose") == "TEXT_ATTACHMENT_PURPOSE_ANSWER":
                    text = t.get("content")
            elif "suggested_questions" in att:
                suggested = att["suggested_questions"].get("questions", [])

        result = None
        if query_result:
            sr = query_result.get("statement_response", query_result)
            manifest = sr.get("manifest", {})
            columns_raw = manifest.get("schema", {}).get("columns", [])
            columns = [
                {"name": c.get("name"), "type": c.get("type_name", c.get("type_text", ""))}
                for c in columns_raw
            ]
            rows = sr.get("result", {}).get("data_array", [])
            row_count = manifest.get("total_row_count") or len(rows)
            truncated = manifest.get("truncated", False)
            result = {
                "columns": columns,
                "rows": rows,
                "row_count": row_count,
                "truncated": truncated,
            }

        status = message_data.get("status", "UNKNOWN")
        error = None
        if status == "FAILED":
            # Extract the real error from Genie's response
            err_obj = message_data.get("error", {})
            if isinstance(err_obj, dict):
                raw = err_obj.get("error", "")
                # Strip internal prefixes like "RESOURCE_EXHAUSTED: "
                if ": " in raw:
                    error = raw.split(": ", 1)[1]
                else:
                    error = raw or "Genie was unable to answer this question. Try rephrasing it."
            else:
                error = str(err_obj) if err_obj else "Genie was unable to answer this question. Try rephrasing it."

        return {
            "status": status,
            "text": text,
            "description": description,
            "sql": sql,
            "statement_id": statement_id,
            "attachment_id": attachment_id,
            "result": result,
            "tables_used": tables_used,
            "suggested_questions": suggested,
            "error": error,
        }
