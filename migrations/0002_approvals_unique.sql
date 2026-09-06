-- approvals are one-per-step: makes the approval gate idempotent
CREATE UNIQUE INDEX IF NOT EXISTS idx_approvals_task_step ON approvals(task_id, step_key);
