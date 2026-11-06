## T01 PASS — At 100 concurrent clients, what authenticated-read throughput and p95 latency were reported?

Expected: 2,107.3 requests/s and p95 102.2 ms, specifically the 100-client row.

All stages met the runner's criteria. [1]
Peak observed throughput occurred at 50 clients. [1]
At 100 clients, throughput was approximately 25.4% lower and p95 approximately 3.15 times the 50-client value. [1]
The nonmonotonic single-client versus ten-client behavior is unexplained by the retained metadata. [1]
Warmup and shared-host interference are plausible hypotheses, not demonstrated causes. [1]
Table row: Clients = 100; Requests = 20,000; Errors = 0; Requests/s = 2,107.3; p50 ms = 39.7; p95 ms = 102.2; p99 ms = 162.0. [1]
Clients Requests Errors Requests/s p50 ms p95 ms p99 ms [1]

Review: Explicit 100-client row: 2,107.3 requests/s and p95 102.2 ms.

## T02 PASS — At 10 concurrent clients, what p50 latency was reported?

Expected: 3.3 ms, specifically the 10-client row.

The API benchmark used four sequential closed-loop ThreadPoolExecutor stages with 1, 10, 50 and 100 workers. [2]
Each made 20,000 requests: 75% workspace collection reads and 25% authenticated-profile reads. [2]
The same QA identity and small dataset were used. [2]
Throughput is request count divided by elapsed stage time. [2]
Per-request latency excludes executor waiting before a worker starts the call, and percentiles use nearest-rank selection. [2]
Acceptance was zero errors and p95 below 2 seconds at each stage. [2]
Table row: Clients = 10; Requests = 20,000; Errors = 0; Requests/s = 2,510.7; p50 ms = 3.3; p95 ms = 7.5; p99 ms = 15.2. [1]
Clients Requests Errors Requests/s p50 ms p95 ms p99 ms [1]

Review: Explicit 10-client row: p50 3.3 ms.

## T03 PASS — At 1 concurrent client, what throughput and p99 latency were reported?

Expected: 139.6 requests/s and p99 75.3 ms, specifically the 1-client row.

Table row: Clients = 1; Requests = 20,000; Errors = 0; Requests/s = 139.6; p50 ms = 2.2; p95 ms = 29.0; p99 ms = 75.3. [1]
Clients Requests Errors Requests/s p50 ms p95 ms p99 ms [1]

Review: Explicit 1-client row: 139.6 requests/s and p99 75.3 ms.