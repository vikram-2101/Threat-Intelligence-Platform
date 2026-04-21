-- Remove a05 from alembic_version — a06 is the current head (it depends on a05)
DELETE FROM alembic_version WHERE version_num = 'a05';
SELECT * FROM alembic_version;
