# Local PostgreSQL Setup Task List
*Goal: Match production environment by using PostgreSQL locally*

## Phase 1: PostgreSQL Installation & Setup
- [x] Install PostgreSQL on Windows
- [x] Verify PostgreSQL service is running
- [x] Create database and user for the application
- [x] Install psycopg2-binary in virtual environment

## Phase 2: Configuration
- [x] Update environment variables for PostgreSQL connection
- [x] Test database connection (ready when PostgreSQL is installed)
- [x] Run Flask-Migrate to create schema in PostgreSQL

## Phase 3: Data Migration
- [x] Export existing data from SQLite
- [x] Import data into PostgreSQL
- [x] Verify data integrity (user count, submissions, etc.)

## Phase 4: Verification
- [x] Test application with PostgreSQL
- [x] Verify all routes work correctly
- [x] Run existing test suite
- [x] Confirm Celery tasks work with new database
