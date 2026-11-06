-- Where a chunk came from inside its document ("page 3", "slide 2", "sheet Sales"),
-- so answers can cite file + page. Empty for plain text and pre-existing chunks.
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS location TEXT NOT NULL DEFAULT '';
