"""Tests for genie.py normalize() against recorded Genie responses."""

from genie import GenieClient

# Recorded from the spike (trimmed to relevant fields)
SAMPLE_MESSAGE = {
    "status": "COMPLETED",
    "attachments": [
        {
            "query": {
                "query": "SELECT 1 AS n",
                "description": "A test query.",
                "statement_id": "stmt-123",
                "query_result_metadata": {"row_count": 1},
                "thoughts": [
                    {"thought_type": "THOUGHT_TYPE_DESCRIPTION", "content": "A test."},
                    {
                        "thought_type": "THOUGHT_TYPE_DATA_SOURCING",
                        "content": "- ld_analytics.kschools.student_information\n- ld_analytics.kschools.student_enrollment",
                    },
                ],
            },
            "attachment_id": "att-q1",
        },
        {
            "text": {
                "content": "Here is the summary.",
                "purpose": "TEXT_ATTACHMENT_PURPOSE_ANSWER",
            }
        },
        {
            "text": {
                "content": "Would you like to refine?",
                "purpose": "FOLLOW_UP_QUESTION",
            },
            "attachment_id": "att-fq",
        },
        {
            "suggested_questions": {
                "questions": ["Q1?", "Q2?"]
            },
            "attachment_id": "att-sq",
        },
        {
            "viz": {"query_attachment_id": "att-q1"},
            "attachment_id": "att-viz",
        },
    ],
}

SAMPLE_QUERY_RESULT = {
    "statement_response": {
        "statement_id": "stmt-123",
        "status": {"state": "SUCCEEDED"},
        "manifest": {
            "format": "JSON_ARRAY",
            "schema": {
                "column_count": 1,
                "columns": [
                    {"name": "n", "type_text": "INT", "type_name": "INT", "position": 0}
                ],
            },
            "total_row_count": 1,
            "truncated": False,
        },
        "result": {"data_array": [["1"]]},
    }
}


def test_normalize_completed():
    out = GenieClient.normalize(SAMPLE_MESSAGE, SAMPLE_QUERY_RESULT)

    assert out["status"] == "COMPLETED"
    assert out["text"] == "Here is the summary."
    assert out["description"] == "A test query."
    assert out["sql"] == "SELECT 1 AS n"
    assert out["statement_id"] == "stmt-123"
    assert out["attachment_id"] == "att-q1"
    assert out["error"] is None

    assert out["result"]["columns"] == [{"name": "n", "type": "INT"}]
    assert out["result"]["rows"] == [["1"]]
    assert out["result"]["row_count"] == 1
    assert out["result"]["truncated"] is False

    assert out["tables_used"] == ["student_information", "student_enrollment"]
    assert out["suggested_questions"] == ["Q1?", "Q2?"]


def test_normalize_failed():
    msg = {"status": "FAILED", "attachments": []}
    out = GenieClient.normalize(msg, None)

    assert out["status"] == "FAILED"
    assert out["error"] is not None
    assert out["text"] is None
    assert out["result"] is None
    assert out["suggested_questions"] == []


def test_normalize_no_query_result():
    out = GenieClient.normalize(SAMPLE_MESSAGE, None)

    assert out["sql"] == "SELECT 1 AS n"
    assert out["result"] is None


def test_normalize_no_attachments():
    msg = {"status": "ASKING_AI", "attachments": []}
    out = GenieClient.normalize(msg, None)

    assert out["status"] == "ASKING_AI"
    assert out["text"] is None
    assert out["sql"] is None
    assert out["result"] is None
