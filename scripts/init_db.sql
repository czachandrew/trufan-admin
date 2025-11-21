-- Initialize test database
CREATE DATABASE trufan_test;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE trufan TO trufan;
GRANT ALL PRIVILEGES ON DATABASE trufan_test TO trufan;
