"""Final, source-reviewed combined-answer results for the >80% repair task."""
from review_v4 import record, POSTGRES, VALIDATION, MAINTENANCE

TABLES={
 'T01':(True,'Explicit 100-client row: 2,107.3 requests/s and p95 102.2 ms.'),
 'T02':(True,'Explicit 10-client row: p50 3.3 ms.'),
 'T03':(True,'Explicit 1-client row: 139.6 requests/s and p99 75.3 ms.')}

if __name__=='__main__':
 record('lmstudio-postgres-2026-11-04-v5',POSTGRES,'Original 20-question development regression; real production PostgreSQL/pgvector retrieval')
 record('lmstudio-validation-2026-11-04-v5',VALIDATION,'Ten additional questions authored before the paragraph/ranking fixes, not used to tune them; real PostgreSQL retrieval, unblinded review')
 record('maintenance-2026-11-04-v5',MAINTENANCE,'Second-document Markdown regression; used for development')
 record('lmstudio-tables-2026-11-04-v5',TABLES,'Targeted table-row regression cases; not independent accuracy evidence')
