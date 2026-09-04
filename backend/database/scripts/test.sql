-- Create the database
CREATE DATABASE phishguard_db
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    TEMPLATE = template0;

-- Create a dedicated user for the app
CREATE USER phishguard_user WITH PASSWORD 'phishguard123';

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE phishguard_db TO phishguard_user;

-- Database privileges do not include table and SERIAL sequence privileges.
\c phishguard_db
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO phishguard_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO phishguard_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO phishguard_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO phishguard_user;

-- Verify the database was created
SELECT datname FROM pg_database WHERE datname = 'phishguard_db';