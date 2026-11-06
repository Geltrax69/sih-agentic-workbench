"""Explicit, unblinded labels for the frozen repaired-run outputs."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[3]
out=root/'tests/evaluation/results/lmstudio-document-2026-11-04-final'
review={'reviewer':'Authoring assistant; unblinded development-set regression review, not independent validation', 'rubric':'tests/evaluation/document_pilot/rubric.md', 'cases':{}}
def add(id,coverage,coverage_reason,mini,gemma,combined):
 def r(v):return {'correct':v[0],'unsupported_material':v[1],'reason':v[2]}
 review['cases'][id]={'retrieval_coverage':coverage,'coverage_reason':coverage_reason,'responses':{'eval-minicpm5-1b':r(mini),'eval-gemma4-e4b':r(gemma),'combined':r(combined)}}
add('Q01','complete','Page 8 contains all three gate decisions and page 4 contains the formal gate.',
 (False,False,'Selects generic retrieval metadata and limit, omitting the three boundary decisions.'),
 (False,False,'Selects similarity and section-heading text, omitting the boundary decisions.'),
 (True,False,'Selects the exact sentence giving refusal at 0.29, warning at 0.30, and answer at 0.45.'))
add('Q02','complete','Page 4 explicitly distinguishes thresholding from correctness probability.',
 (True,False,'Includes the explicit not-a-probability statement and correct threshold context.'),
 (True,False,'Returns the exact not-a-probability statement.'),
 (True,False,'Preserves the explicit not-a-probability statement.'))
add('Q03','complete','Lexical matching now includes the page 3 paragraph defining 800/100.',
 (True,False,'Returns the exact 800-character and nominal 100-character overlap definition.'),
 (True,False,'Returns the exact default definition.'),
 (True,False,'Preserves the exact default definition.'))
add('Q04','complete','The selected page 3 and page 8 passages specify vector(768).',
 (True,False,'Correct 768-dimensional storage statement.'),
 (True,False,'Both selected statements correctly specify vector(768).'),
 (False,False,'Unnecessary refusal despite both models supplying the dimension and evidence containing it.'))
add('Q05','complete','Page 3 supplies both the missing worker and Redis health-check role.',
 (True,False,'Includes worker absence and Redis not being demonstrated job transport.'),
 (False,False,'Only answers the Redis transport question; omits the worker absence.'),
 (True,False,'Contains both required negative conclusions.'))
add('Q06','complete','The selected page 4 passage contains the owner requirement and paused state.',
 (False,False,'Selects an unrelated architecture diagram and does not answer role/state.'),
 (False,False,'Names WAITING_FOR_APPROVAL but omits the owner role.'),
 (False,False,'Names the paused state but omits the owner role.'))
