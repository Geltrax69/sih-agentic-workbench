"""Exercise real pgvector SQL in a disposable local test database, not user data."""
from pathlib import Path
import json, sys, uuid
import psycopg
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'services/ai'))
from app.ingestion import search_workspace
from app.retrieval import expand_context, select_evidence

admin_dsn='postgresql://postgres:sih-pilot-local@127.0.0.1:55437/postgres'
database='codex_pilot_'+uuid.uuid4().hex
with psycopg.connect(admin_dsn,autocommit=True) as admin:
 admin.execute(psycopg.sql.SQL('CREATE DATABASE {}').format(psycopg.sql.Identifier(database)))
dsn=admin_dsn.rsplit('/',1)[0]+'/'+database
ws,other=str(uuid.uuid4()),str(uuid.uuid4())
doc,foreign,deleted,lexical=[str(uuid.uuid4()) for _ in range(4)]
with psycopg.connect(dsn,autocommit=True) as conn:
 conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
 conn.execute('CREATE TABLE documents(id uuid PRIMARY KEY, filename text NOT NULL, deleted_at timestamptz)')
 conn.execute('CREATE TABLE document_chunks(id uuid PRIMARY KEY, document_id uuid REFERENCES documents(id), workspace_id uuid, embedding vector(3), chunk_index integer, location text, content text)')
 for id,name,revoked in [(doc,'manual.pdf',False),(foreign,'foreign.pdf',False),(deleted,'deleted.pdf',True),(lexical,'lexical.pdf',False)]:
  conn.execute('INSERT INTO documents VALUES(%s,%s,CASE WHEN %s THEN now() ELSE NULL END)',(id,name,revoked))
 cases=[(doc,ws,0,'page 1','Replacement bearings require a torque of 45 Nm.','[1,0,0]'),
        (doc,ws,1,'page 1','First disconnect power and lock out the pump.','[0.01,1,0]'),
        (foreign,other,0,'page 1','Replacement bearings PRIVATE_OTHER_TENANT.','[1,0,0]'),
        (deleted,ws,0,'page 1','Replacement bearings DELETED_SOURCE.','[1,0,0]'),
        (lexical,ws,0,'page 1','Approved sealant compatibility for silicon seals.','[0,1,0]')]
 for d,w,idx,loc,text,vec in cases:
  conn.execute('INSERT INTO document_chunks VALUES(%s,%s,%s,%s::vector,%s,%s,%s)',(str(uuid.uuid4()),d,w,vec,idx,loc,text))
rows=search_workspace(dsn,ws,[1,0,0],limit=1,question='Which replacement bearing torque is required?')
assert len(rows)==2,rows
assert all(str(r['document_id'])==doc for r in rows)
assert any(r['context_only'] for r in rows)
converted=[{**r,'document_id':str(r['document_id']),'score':float(r['score'])} for r in rows]
expanded=expand_context(select_evidence('Replacement bearing torque',converted),converted)
assert len(expanded)==1 and '45 Nm' in expanded[0]['content'] and 'disconnect power' in expanded[0]['content']
assert not any('PRIVATE_OTHER_TENANT' in r['content'] or 'DELETED_SOURCE' in r['content'] for r in rows)
plain=search_workspace(dsn,ws,[1,0,0],limit=8)
assert all(str(r['document_id']) in {doc,lexical} for r in plain)
lexical_rows=search_workspace(dsn,ws,[1,0,0],limit=1,question='approved sealants')
assert any(str(r['document_id'])==lexical for r in lexical_rows), lexical_rows
result={'real_database':'PostgreSQL 16 + pgvector in a disposable loopback-only container',
        'hybrid_sql_executes':True,'english_inflection_search':True,'same_page_neighbor_included':True,
        'foreign_workspace_excluded':True,'deleted_document_excluded':True,'vector_only_scope_preserved':True,
        'source_context_includes_low_vector_neighbor':True,
        'scope':'Real retrieval SQL and page expansion only; not a Go authentication or full application deployment test.'}
out=Path(__file__).resolve().parents[2]/'tests/evaluation/results/qa-v3-validation/database.json'
out.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

with psycopg.connect(admin_dsn,autocommit=True) as admin:
 admin.execute(psycopg.sql.SQL('DROP DATABASE {}').format(psycopg.sql.Identifier(database)))
