# Chat over Databricks Genie: build spec

Hand this file to Claude Code as the starting point. Read it fully before writing code.

## Goal

A custom chat UI where people ask questions in plain English about student data and get back a summary, a chart, a table, and the SQL that produced it. The "brain" is a Databricks Genie space. We do not write text-to-SQL ourselves.

## Decisions already made

- Genie is the brain. Our app is a UI plus a thin backend.
- The backend calls the Genie Conversation REST API directly. We do not use MCP inside this app. MCP only makes sense later if we add an agent that uses Genie as one tool among several.
- The backend forwards the signed-in user's Databricks OAuth token to Genie, so Unity Catalog permissions apply per person. Do not switch to a shared service principal without asking.
- Backend: Python, FastAPI, httpx.
- Frontend: React + Vite + TypeScript (open choice, change only if there is a good reason and say so).
- Read-only. Nothing in this app writes to Databricks.

## The Genie space

- Name: Student Journey Insights
- Space ID: `<fill in>`
- Workspace host: `<fill in>`
- Catalog and schema: `ld_analytics.kschools`
- Scope: admissions, enrollment by campus/grade/school year, withdrawals and retention, graduation outcomes, SAT scores, parent/guardian context.

Tables (schema only, learned from Genie; no student rows were read):

| Table | Purpose | Main columns |
|---|---|---|
| student_admission_data | Applications and assessment percentiles | student_id, ctp5_math_percentile_national, ctp5_reading_percentile_national |
| student_enrollment | Year-by-year enrollment by school, grade, campus, region | EnrollmentSK, SchoolYearStart, SchoolYearEnd, SchoolYearDesc, SchoolCode, SchoolName, SchoolLevel, CampusAbbr, StdNumber, Grade, KSZip, KSRegionName, EnrollDesc, BoarderStatusDesc |
| student_information | Student profile, entry cohort, graduation status | StdNumber, LatestGrade, LatestSchoolCode, LatestSchoolName, OnTimeGradYear, HasGraduated, GradYear, EntrySchoolYearStart, EntrySchoolYearDesc, EntryGrade, EntrySchoolName, EntrySchoolLevel |
| student_parent_guardian_data | Student to guardian links | StdNumber, Grade, SchoolYearDesc |
| student_sat_score_data_file_1 | SAT records, demographics, benchmarks, college fields | AI_NAME, COHORT_YEAR, GENDER, Student Id, LATEST_SAT_DATE, LATEST_SAT_GRADE, LATEST_SAT_TOTAL, PERCENTILE_STATE_TOTAL, PERCENTILE_COUNTRY_TOTAL, MATH_CCR_BENCHMARK, ADMIN2..6_SAT_TOTAL, COLLEGE_NAME1..4 and more |
| student_sat_score_data_file_2 | SAT records, subject tests, GPA, college preferences | AI_NAME, COHORT_YEAR, Student Id, LATEST_SAT_TOTAL, SDQ_GPA, SDQ_RANK, LATEST_SUBJ_1_SCORE and more |

Genie's own suggested starter questions (use these on the new-chat screen):

1. What share of students admitted in each school year are still enrolled or have graduated?
2. What is the average latest SAT total and percent meeting the math benchmark by campus, across both SAT files?
3. What are the main grade levels and school years covered in the student enrollment data?

## How the Genie API works

Verify every path and field below with a spike script (step 1 in the plan) before building on them. These come from the Databricks docs and may differ slightly by workspace or SDK version.

1. Start: `POST /api/2.0/genie/spaces/{space_id}/start-conversation` with `{"content": "<question>"}`. Returns `conversation_id` and `message_id`.
2. Follow-up: `POST /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages` with `{"content": "..."}`. Genie uses earlier messages in the conversation as context.
3. Poll: `GET /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}` every 1 to 2 seconds.
4. Statuses seen in the docs: SUBMITTED, FETCHING_METADATA, FILTERING_CONTEXT, ASKING_AI, PENDING_WAREHOUSE, EXECUTING_QUERY, COMPLETED, FAILED, CANCELLED, QUERY_RESULT_EXPIRED. Treat COMPLETED, FAILED and CANCELLED as final.
5. When COMPLETED, the message has `attachments`. A query attachment has the SQL, a description of it, a `statement_id` and an `attachment_id`. A text attachment has the prose answer. Suggested questions also come back.
6. Rows: call the query-result endpoint for the `attachment_id`. The path may be `.../messages/{mid}/attachments/{aid}/query-result` or the older `.../messages/{mid}/query-result/{aid}`. Use whichever works. The metadata has a row count and a truncated flag.
7. If status is QUERY_RESULT_EXPIRED, call the execute-attachment-query endpoint to re-run the SQL.
8. The space must be configured in the Databricks UI. The user needs access to the space and at least CAN USE on a SQL warehouse.

## Backend contract (FastAPI)

All routes require the user's Databricks token, passed through from the frontend (Authorization header). Never log tokens, SQL result rows, or question text that could contain student details.

- `POST /api/ask` body `{question, conversation_id?}` returns `{conversation_id, message_id}`
- `GET /api/status/{conversation_id}/{message_id}` returns:
  - `status` (Genie status string)
  - when COMPLETED: `text?`, `description?`, `sql?`, `result?` as `{columns: [{name, type}], rows: [[...]], row_count, truncated}`, `suggested_questions: []`
  - when FAILED: `error` with a short, user-safe message
- `POST /api/cancel/{conversation_id}/{message_id}` if Genie supports cancel for the message (check)
- `POST /api/feedback` for thumbs up/down if Genie has a feedback endpoint (check, otherwise skip)
- Normalize Genie's response into the shape above so the frontend never sees raw Genie JSON.
- Map Genie errors to clear messages. Handle token expiry (401) by telling the frontend to re-authenticate.

## Frontend: four screens

The visual reference is the published canvas: https://claude.ai/artifact/QfqqehUmP5Fr6QLAdkoANZ . The `mockups/` folder has the source of each screen (`.dc.html` canvas files). They need the canvas runtime, so they will not render standalone. Read them for exact markup, spacing and colors, and use the canvas link to see them. The chart numbers in the mockups are made up. Do not copy them anywhere.

1. **Answer screen (desktop).** Sidebar (new chat, Genie space card, recent chats). Header with chat title. Message list: user bubble, then an assistant block with the summary text, a "How Genie read this" note (the query description), and a result card with Chart / Table / SQL tabs. Card footer: tables used, row count, elapsed time, thumbs up/down, Copy SQL, Export CSV, Open in Databricks. Below: Genie's suggested follow-ups as chips. Composer at the bottom with the note "Genie writes the SQL, so check the query before you rely on a number."
2. **New chat.** Heading, one line on what you can ask, the three starter questions, the list of tables in the space, composer.
3. **Working state.** While polling: a step list driven by the real Genie status (read question, found tables, writing SQL, running on warehouse, writing summary), a Stop button, skeleton lines, composer disabled. Show the table names Genie used once known.
4. **Mobile (390 wide).** Same answer, stacked bars per row, tabs full width, chips in a horizontal scroll, 44px touch targets.

Rules for the result card:
- Pick the chart from the result shape on the client: one category plus one or two numbers is a bar chart, a date column plus numbers is a line chart, shares that sum to about 100 is a stacked bar. Anything else falls back to the table. The table tab is always available.
- Always show the SQL. Never hide where a number came from.
- If `truncated` is true, say "Showing first N rows".
- Empty result: say so plainly and show the SQL.
- Errors: say what failed in one sentence, offer Retry, keep the SQL if there is any.

Design tokens:
- Colors: ink `#15181C`, page `#F6F6F3`, surface `#FFFFFF`, border `#E3E3DD`, muted text `#5A606A`, accent `#0B6E6E`, accent soft `#E3F1F0`, chart series `#0B6E6E` `#7DA7A3` `#C9CDD2`, negative `#A5361F`, warning chip bg `#FFF1D6` text `#6B4500`, SQL block bg `#15181C`.
- Fonts: Inter for UI, JetBrains Mono for SQL and table names.
- Text must meet 4.5:1 contrast. Use real buttons and inputs, label icon-only buttons, 44px minimum touch targets.
- The "Mockup values" chip in the mockups is for the mockups only. Remove it in the real app.

## Data handling (student data)

This space holds student-level data, including IDs, demographics, and guardian links. Before shipping, decide with the data owner:
- Which questions are allowed. For example, block or warn on requests for lists of individual students.
- Whether to hide or suppress small groups in results.
- What is logged. Default: log request IDs, status, timing, and errors only. No question text, SQL results, or tokens.
- Whether the Export CSV button is allowed for everyone.

Until those are decided, build the plumbing so these can be switched on (a result post-processing hook on the backend) but do not invent policy.

## Plan

1. **Spike (first).** A single Python script that logs in with a token, asks the first starter question, polls to COMPLETED, prints the normalized JSON. Confirm paths, statuses and shapes. Report anything that differs from this spec.
2. **Backend.** The three or four routes above, with tests against recorded Genie responses.
3. **Frontend shell.** Layout, new-chat screen, composer, conversation state.
4. **Answer flow.** Polling, working state, result card with chart/table/SQL tabs, follow-up chips.
5. **Polish.** Mobile layout, errors, empty states, expired results, token expiry.
6. **Auth.** Databricks OAuth sign-in in the frontend, token forwarded to the backend.

Work in small commits. After step 1, stop and show me the real response shapes before going further.

## Open questions

- Space ID and workspace host.
- How users sign in (Databricks OAuth in the browser, or something else).
- Where this is hosted.
- Data handling decisions above.
- Do we want more than one Genie space later? If yes, keep the space ID in config, not hard-coded.