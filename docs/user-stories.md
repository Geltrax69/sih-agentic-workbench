# User Stories — Sovereign Agentic AI Workbench

Primary personas: **Admin** (platform), **Org Owner**, **Analyst** (workspace
member), **Approver** (workspace owner), **Auditor**.

## US-1 Authentication
As any user, I log in with email/password so that my actions are attributable.
AC: valid login returns token + profile; invalid login returns 401 without
revealing which field failed; login events audited.

## US-2 Organization / workspace creation
As an Org Owner, I create isolated workspaces so teams only see their own
knowledge. AC: workspace lists only for members; cross-workspace document fetch
returns 404/403 and writes an audit event.

## US-3 Model configuration
As an Admin, I register a local model endpoint and check its health so the team
uses approved models only. AC: health endpoint shows reachable/model list;
sovereign mode rejects remote base URLs.

## US-4 Document upload
As an Analyst, I upload a PDF/CSV so it becomes searchable knowledge.
AC: accepted types indexed; invalid type rejected with clear error; ingestion
status visible (UPLOADED→PROCESSING→INDEXED/FAILED); original stored in MinIO.

## US-5 Grounded question
As an Analyst, I ask "What caused the repeated pump shutdowns?" and receive an
answer that cites internal sources only.
AC: answer lists citations with document + chunk; if evidence is insufficient
the system refuses/cautions; no cross-workspace leakage.

## US-6 Task with tools
As an Analyst, I ask for a failure-trend analysis over maintenance CSVs.
AC: supervisor plans steps; data agent runs read-only SQL; report agent emits a
structured report; progress streams to UI; full run audited.

## US-7 Dangerous action approval
As an Approver, I must approve any write/destructive tool action.
AC: task pauses in WAITING_FOR_APPROVAL; approve/reject recorded with identity;
execution only continues after approval.

## US-8 Audit review
As an Auditor, I open the audit view and filter by user/workspace/task.
AC: append-only events, immutable ordering, exportable.

## US-9 Controlled learning
As the system, I persist verified lessons from completed tasks so future runs
improve, without storing hallucinations as facts.
AC: memory writes only for verified results / human-approved decisions;
speculation blocked by policy.

## US-10 Demo (killer demo)
A judge watches: login → create workspace → upload maintenance PDF + 2 CSVs +
image → ask grounded question → cited answer → generate maintenance action
report → approve export → audit trail shows every step. No cloud model used.
