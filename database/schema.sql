-- ============================================================
-- PERSONAL EXPENSE TRACKER
-- Enterprise Multi-User Supabase PostgreSQL Database Schema
-- Canonical source schema
-- ============================================================

-- IMPORTANT:
-- This file describes the target/final database architecture.
-- It is NOT a migration for an already-populated production database.
-- Run this file only when creating a fresh database.
-- Existing production data should be upgraded with a separate migration.

-- ============================================================
-- REQUIRED EXTENSION
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- ============================================================
-- 1. APP ACCESS / USERS
-- ============================================================

CREATE TABLE IF NOT EXISTS app_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    username VARCHAR(100) NOT NULL,

    password_hash TEXT NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT app_users_username_not_empty
        CHECK (length(trim(username)) > 0)
);

-- Username matching is case-insensitive.
CREATE UNIQUE INDEX IF NOT EXISTS idx_app_users_username_unique
    ON app_users (lower(username));


-- ============================================================
-- 2. ACCOUNTS
-- ============================================================

CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    name VARCHAR(100) NOT NULL,

    account_type VARCHAR(50) NOT NULL DEFAULT 'bank',

    opening_balance NUMERIC(15, 2) NOT NULL DEFAULT 0,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT accounts_user_fk
        FOREIGN KEY (user_id)
        REFERENCES app_users(id)
        ON DELETE CASCADE,

    CONSTRAINT accounts_opening_balance_non_negative
        CHECK (opening_balance >= 0),

    CONSTRAINT accounts_account_type_valid
        CHECK (
            account_type IN (
                'bank',
                'cash',
                'other'
            )
        ),

    CONSTRAINT accounts_user_id_unique
        UNIQUE (user_id, id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_user_name_unique
    ON accounts (user_id, name);

CREATE INDEX IF NOT EXISTS idx_accounts_user_id
    ON accounts(user_id);

CREATE INDEX IF NOT EXISTS idx_accounts_user_active
    ON accounts(user_id, is_active);


-- ============================================================
-- 3. CATEGORIES
-- ============================================================

CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    name VARCHAR(100) NOT NULL,

    category_type VARCHAR(20) NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT categories_user_fk
        FOREIGN KEY (user_id)
        REFERENCES app_users(id)
        ON DELETE CASCADE,

    CONSTRAINT categories_type_valid
        CHECK (
            category_type IN (
                'income',
                'expense'
            )
        ),

    CONSTRAINT categories_user_id_unique
        UNIQUE (user_id, id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_categories_user_name_type_unique
    ON categories(user_id, name, category_type);

CREATE INDEX IF NOT EXISTS idx_categories_user_id
    ON categories(user_id);

CREATE INDEX IF NOT EXISTS idx_categories_user_type
    ON categories(user_id, category_type);


-- ============================================================
-- 4. PEOPLE
-- ============================================================

CREATE TABLE IF NOT EXISTS people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    name VARCHAR(150) NOT NULL,

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT people_user_fk
        FOREIGN KEY (user_id)
        REFERENCES app_users(id)
        ON DELETE CASCADE,

    CONSTRAINT people_name_not_empty
        CHECK (length(trim(name)) > 0),

    CONSTRAINT people_user_id_unique
        UNIQUE (user_id, id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_people_user_name_unique
    ON people(user_id, name);

CREATE INDEX IF NOT EXISTS idx_people_user_id
    ON people(user_id);


-- ============================================================
-- 5. TRANSACTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    transaction_date DATE NOT NULL,

    transaction_type VARCHAR(40) NOT NULL,

    amount NUMERIC(15, 2) NOT NULL,

    source_account_id UUID,

    destination_account_id UUID,

    category_id UUID,

    payment_method VARCHAR(40),

    person_id UUID,

    description TEXT,

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT transactions_user_fk
        FOREIGN KEY (user_id)
        REFERENCES app_users(id)
        ON DELETE CASCADE,

    CONSTRAINT transactions_amount_positive
        CHECK (amount > 0),

    CONSTRAINT transactions_type_valid
        CHECK (
            transaction_type IN (
                'income',
                'expense',
                'internal_transfer',
                'friend_money_received',
                'friend_money_returned',
                'friend_money_lent',
                'friend_money_lent_returned',
                'balance_adjustment',
                'savings_goal_contribution'
            )
        ),

    CONSTRAINT transactions_payment_method_valid
        CHECK (
            payment_method IS NULL
            OR payment_method IN (
                'upi',
                'debit_card',
                'bank_transfer',
                'cash',
                'auto_debit',
                'other'
            )
        ),

    CONSTRAINT transactions_source_destination_different
        CHECK (
            source_account_id IS NULL
            OR destination_account_id IS NULL
            OR source_account_id <> destination_account_id
        ),

    CONSTRAINT transactions_user_id_unique
        UNIQUE (user_id, id),

    CONSTRAINT transactions_source_account_fk
        FOREIGN KEY (user_id, source_account_id)
        REFERENCES accounts(user_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT transactions_destination_account_fk
        FOREIGN KEY (user_id, destination_account_id)
        REFERENCES accounts(user_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT transactions_category_fk
        FOREIGN KEY (user_id, category_id)
        REFERENCES categories(user_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT transactions_person_fk
        FOREIGN KEY (user_id, person_id)
        REFERENCES people(user_id, id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_transactions_user_id
    ON transactions(user_id);

CREATE INDEX IF NOT EXISTS idx_transactions_user_date
    ON transactions(user_id, transaction_date DESC);

CREATE INDEX IF NOT EXISTS idx_transactions_user_type
    ON transactions(user_id, transaction_type);

CREATE INDEX IF NOT EXISTS idx_transactions_user_category
    ON transactions(user_id, category_id);

CREATE INDEX IF NOT EXISTS idx_transactions_user_source_account
    ON transactions(user_id, source_account_id);

CREATE INDEX IF NOT EXISTS idx_transactions_user_person
    ON transactions(user_id, person_id);


-- ============================================================
-- 6. TRANSFERS
-- ============================================================

CREATE TABLE IF NOT EXISTS transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    transaction_id UUID NOT NULL UNIQUE,

    from_account_id UUID NOT NULL,

    to_account_id UUID NOT NULL,

    amount NUMERIC(15, 2) NOT NULL,

    transfer_date DATE NOT NULL,

    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT transfers_user_fk
        FOREIGN KEY (user_id)
        REFERENCES app_users(id)
        ON DELETE CASCADE,

    CONSTRAINT transfers_amount_positive
        CHECK (amount > 0),

    CONSTRAINT transfers_different_accounts
        CHECK (from_account_id <> to_account_id),

    CONSTRAINT transfers_transaction_fk
        FOREIGN KEY (user_id, transaction_id)
        REFERENCES transactions(user_id, id)
        ON DELETE CASCADE,

    CONSTRAINT transfers_from_account_fk
        FOREIGN KEY (user_id, from_account_id)
        REFERENCES accounts(user_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT transfers_to_account_fk
        FOREIGN KEY (user_id, to_account_id)
        REFERENCES accounts(user_id, id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_transfers_user_id
    ON transfers(user_id);

CREATE INDEX IF NOT EXISTS idx_transfers_user_date
    ON transfers(user_id, transfer_date DESC);


-- ============================================================
-- 7. FRIENDS' MONEY
-- ============================================================

CREATE TABLE IF NOT EXISTS friends_money (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    person_id UUID NOT NULL,

    transaction_id UUID NOT NULL,

    account_id UUID NOT NULL,

    amount_received NUMERIC(15, 2) NOT NULL DEFAULT 0,

    amount_returned NUMERIC(15, 2) NOT NULL DEFAULT 0,

    received_date DATE NOT NULL,

    expected_return_date DATE,

    status VARCHAR(30) NOT NULL DEFAULT 'holding',

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT friends_money_user_fk
        FOREIGN KEY (user_id)
        REFERENCES app_users(id)
        ON DELETE CASCADE,

    CONSTRAINT friends_money_received_non_negative
        CHECK (amount_received >= 0),

    CONSTRAINT friends_money_returned_non_negative
        CHECK (amount_returned >= 0),

    CONSTRAINT friends_money_returned_not_greater
        CHECK (amount_returned <= amount_received),

    CONSTRAINT friends_money_status_valid
        CHECK (
            status IN (
                'holding',
                'partially_returned',
                'fully_returned'
            )
        ),

    CONSTRAINT friends_money_person_fk
        FOREIGN KEY (user_id, person_id)
        REFERENCES people(user_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT friends_money_transaction_fk
        FOREIGN KEY (user_id, transaction_id)
        REFERENCES transactions(user_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT friends_money_account_fk
        FOREIGN KEY (user_id, account_id)
        REFERENCES accounts(user_id, id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_friends_money_user_id
    ON friends_money(user_id);

CREATE INDEX IF NOT EXISTS idx_friends_money_user_person
    ON friends_money(user_id, person_id);

CREATE INDEX IF NOT EXISTS idx_friends_money_user_status
    ON friends_money(user_id, status);

CREATE INDEX IF NOT EXISTS idx_friends_money_user_date
    ON friends_money(user_id, received_date DESC);


-- ============================================================
-- 8. BUDGETS
-- ============================================================

CREATE TABLE IF NOT EXISTS budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    category_id UUID NOT NULL,

    budget_month INTEGER NOT NULL,

    budget_year INTEGER NOT NULL,

    budget_amount NUMERIC(15, 2) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT budgets_user_fk
        FOREIGN KEY (user_id)
        REFERENCES app_users(id)
        ON DELETE CASCADE,

    CONSTRAINT budgets_month_valid
        CHECK (budget_month BETWEEN 1 AND 12),

    CONSTRAINT budgets_year_valid
        CHECK (budget_year >= 2000),

    CONSTRAINT budgets_amount_positive
        CHECK (budget_amount > 0),

    CONSTRAINT budgets_category_fk
        FOREIGN KEY (user_id, category_id)
        REFERENCES categories(user_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT budgets_unique_category_month
        UNIQUE (
            user_id,
            category_id,
            budget_month,
            budget_year
        )
);

CREATE INDEX IF NOT EXISTS idx_budgets_user_id
    ON budgets(user_id);

CREATE INDEX IF NOT EXISTS idx_budgets_user_period
    ON budgets(user_id, budget_year DESC, budget_month DESC);


-- ============================================================
-- 9. SAVINGS GOALS
-- ============================================================

CREATE TABLE IF NOT EXISTS savings_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    name VARCHAR(150) NOT NULL,

    target_amount NUMERIC(15, 2) NOT NULL,

    target_date DATE,

    status VARCHAR(30) NOT NULL DEFAULT 'active',

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT savings_goals_user_fk
        FOREIGN KEY (user_id)
        REFERENCES app_users(id)
        ON DELETE CASCADE,

    CONSTRAINT savings_goals_name_not_empty
        CHECK (length(trim(name)) > 0),

    CONSTRAINT savings_goals_target_positive
        CHECK (target_amount > 0),

    CONSTRAINT savings_goals_status_valid
        CHECK (
            status IN (
                'active',
                'completed',
                'cancelled'
            )
        ),

    CONSTRAINT savings_goals_user_id_unique
        UNIQUE (user_id, id)
);

CREATE INDEX IF NOT EXISTS idx_savings_goals_user_id
    ON savings_goals(user_id);

CREATE INDEX IF NOT EXISTS idx_savings_goals_user_status
    ON savings_goals(user_id, status);


-- ============================================================
-- 10. SAVINGS CONTRIBUTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS savings_contributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    savings_goal_id UUID NOT NULL,

    transaction_id UUID NOT NULL,

    account_id UUID NOT NULL,

    amount NUMERIC(15, 2) NOT NULL,

    contribution_date DATE NOT NULL,

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT savings_contributions_user_fk
        FOREIGN KEY (user_id)
        REFERENCES app_users(id)
        ON DELETE CASCADE,

    CONSTRAINT savings_contributions_amount_positive
        CHECK (amount > 0),

    CONSTRAINT savings_contributions_goal_fk
        FOREIGN KEY (user_id, savings_goal_id)
        REFERENCES savings_goals(user_id, id)
        ON DELETE CASCADE,

    CONSTRAINT savings_contributions_transaction_fk
        FOREIGN KEY (user_id, transaction_id)
        REFERENCES transactions(user_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT savings_contributions_account_fk
        FOREIGN KEY (user_id, account_id)
        REFERENCES accounts(user_id, id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_savings_contributions_user_id
    ON savings_contributions(user_id);

CREATE INDEX IF NOT EXISTS idx_savings_contributions_user_goal
    ON savings_contributions(user_id, savings_goal_id);

CREATE INDEX IF NOT EXISTS idx_savings_contributions_user_date
    ON savings_contributions(user_id, contribution_date DESC);


-- ============================================================
-- 11. RECURRING TRANSACTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS recurring_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    transaction_name VARCHAR(150) NOT NULL,

    transaction_type VARCHAR(40) NOT NULL,

    amount NUMERIC(15, 2) NOT NULL,

    account_id UUID,

    destination_account_id UUID,

    category_id UUID,

    payment_method VARCHAR(40),

    frequency VARCHAR(20) NOT NULL,

    start_date DATE NOT NULL,

    next_due_date DATE NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    auto_create BOOLEAN NOT NULL DEFAULT FALSE,

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT recurring_user_fk
        FOREIGN KEY (user_id)
        REFERENCES app_users(id)
        ON DELETE CASCADE,

    CONSTRAINT recurring_name_not_empty
        CHECK (length(trim(transaction_name)) > 0),

    CONSTRAINT recurring_amount_positive
        CHECK (amount > 0),

    CONSTRAINT recurring_frequency_valid
        CHECK (
            frequency IN (
                'weekly',
                'monthly',
                'quarterly',
                'yearly'
            )
        ),

    CONSTRAINT recurring_type_valid
        CHECK (
            transaction_type IN (
                'income',
                'expense',
                'internal_transfer'
            )
        ),

    CONSTRAINT recurring_payment_method_valid
        CHECK (
            payment_method IS NULL
            OR payment_method IN (
                'upi',
                'debit_card',
                'bank_transfer',
                'cash',
                'auto_debit',
                'other'
            )
        ),

    CONSTRAINT recurring_source_destination_different
        CHECK (
            account_id IS NULL
            OR destination_account_id IS NULL
            OR account_id <> destination_account_id
        ),

    CONSTRAINT recurring_account_fk
        FOREIGN KEY (user_id, account_id)
        REFERENCES accounts(user_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT recurring_destination_account_fk
        FOREIGN KEY (user_id, destination_account_id)
        REFERENCES accounts(user_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT recurring_category_fk
        FOREIGN KEY (user_id, category_id)
        REFERENCES categories(user_id, id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_recurring_user_id
    ON recurring_transactions(user_id);

CREATE INDEX IF NOT EXISTS idx_recurring_user_due
    ON recurring_transactions(user_id, next_due_date);

CREATE INDEX IF NOT EXISTS idx_recurring_user_active
    ON recurring_transactions(user_id, is_active);


-- ============================================================
-- 12. BACKUP HISTORY
-- ============================================================

CREATE TABLE IF NOT EXISTS backup_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    backup_type VARCHAR(20) NOT NULL,

    backup_filename VARCHAR(255) NOT NULL,

    backup_version VARCHAR(20) NOT NULL,

    record_count INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT backup_history_user_fk
        FOREIGN KEY (user_id)
        REFERENCES app_users(id)
        ON DELETE CASCADE,

    CONSTRAINT backup_type_valid
        CHECK (
            backup_type IN (
                'csv',
                'json'
            )
        ),

    CONSTRAINT backup_record_count_valid
        CHECK (record_count >= 0)
);

CREATE INDEX IF NOT EXISTS idx_backup_history_user_id
    ON backup_history(user_id);

CREATE INDEX IF NOT EXISTS idx_backup_history_user_date
    ON backup_history(user_id, created_at DESC);


-- ============================================================
-- 13. APP SETTINGS
-- ============================================================

CREATE TABLE IF NOT EXISTS app_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    setting_key VARCHAR(100) NOT NULL,

    setting_value TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT app_settings_user_fk
        FOREIGN KEY (user_id)
        REFERENCES app_users(id)
        ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_app_settings_user_key_unique
    ON app_settings(user_id, setting_key);

CREATE INDEX IF NOT EXISTS idx_app_settings_user_id
    ON app_settings(user_id);


-- ============================================================
-- 14. MONEY LENT / RECEIVABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS money_lent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL,

    person_id UUID NOT NULL,

    transaction_id UUID NOT NULL,

    account_id UUID NOT NULL,

    amount_lent NUMERIC(15, 2) NOT NULL,

    amount_returned NUMERIC(15, 2) NOT NULL DEFAULT 0,

    lent_date DATE NOT NULL,

    expected_return_date DATE,

    status VARCHAR(30) NOT NULL DEFAULT 'lent',

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT money_lent_user_fk
        FOREIGN KEY (user_id)
        REFERENCES app_users(id)
        ON DELETE CASCADE,

    CONSTRAINT money_lent_amount_positive
        CHECK (amount_lent > 0),

    CONSTRAINT money_lent_returned_non_negative
        CHECK (amount_returned >= 0),

    CONSTRAINT money_lent_returned_not_greater
        CHECK (amount_returned <= amount_lent),

    CONSTRAINT money_lent_status_valid
        CHECK (
            status IN (
                'lent',
                'partially_returned',
                'fully_returned'
            )
        ),

    CONSTRAINT money_lent_person_fk
        FOREIGN KEY (user_id, person_id)
        REFERENCES people(user_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT money_lent_transaction_fk
        FOREIGN KEY (user_id, transaction_id)
        REFERENCES transactions(user_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT money_lent_account_fk
        FOREIGN KEY (user_id, account_id)
        REFERENCES accounts(user_id, id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_money_lent_user_id
    ON money_lent(user_id);

CREATE INDEX IF NOT EXISTS idx_money_lent_user_person
    ON money_lent(user_id, person_id);

CREATE INDEX IF NOT EXISTS idx_money_lent_user_account
    ON money_lent(user_id, account_id);

CREATE INDEX IF NOT EXISTS idx_money_lent_user_status
    ON money_lent(user_id, status);

CREATE INDEX IF NOT EXISTS idx_money_lent_user_date
    ON money_lent(user_id, lent_date DESC);


-- ============================================================
-- 15. ROW LEVEL SECURITY
-- ============================================================

-- The application currently uses custom app_users authentication
-- and a server-side Supabase secret key.
--
-- RLS is enabled as defense-in-depth.
-- The service key bypasses RLS, so application-level user_id
-- scoping remains mandatory in every service/query.

ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE people ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE transfers ENABLE ROW LEVEL SECURITY;
ALTER TABLE friends_money ENABLE ROW LEVEL SECURITY;
ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE savings_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE savings_contributions ENABLE ROW LEVEL SECURITY;
ALTER TABLE recurring_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE backup_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE money_lent ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- 16. ATOMIC JSON BACKUP RESTORE
-- ============================================================
--
-- Security model:
--   1. Python supplies the authenticated application's user UUID.
--   2. The backup's top-level user_id must equal that UUID.
--   3. Every row in every restored table must contain the same user_id.
--   4. app_users is NEVER restored.
--   5. SECURITY DEFINER uses a fixed search_path.
--   6. The function runs atomically: any exception rolls back
--      the complete restore.
--
-- The Python backup service should call:
--
-- restore_expense_tracker_backup(backup_data, current_user_id)
--
-- where current_user_id comes from get_current_user_id().

CREATE OR REPLACE FUNCTION restore_expense_tracker_backup(
    backup_data JSONB,
    p_user_id UUID
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    records JSONB;
    record_item JSONB;
    restored_counts JSONB := '{}'::JSONB;
    record_count INTEGER;
    expected_user_id UUID;
BEGIN

    -- --------------------------------------------------------
    -- Validate authenticated application user
    -- --------------------------------------------------------

    IF p_user_id IS NULL THEN
        RAISE EXCEPTION 'Current user ID is required.';
    END IF;

    SELECT id
    INTO expected_user_id
    FROM app_users
    WHERE id = p_user_id
      AND is_active = TRUE;

    IF expected_user_id IS NULL THEN
        RAISE EXCEPTION 'Current user does not exist or is inactive.';
    END IF;


    -- --------------------------------------------------------
    -- Validate backup structure
    -- --------------------------------------------------------

    IF backup_data IS NULL THEN
        RAISE EXCEPTION 'Backup data is required.';
    END IF;

    IF backup_data->>'backup_version' IS NULL THEN
        RAISE EXCEPTION 'Backup version is missing.';
    END IF;

    IF backup_data->'user_id' IS NULL THEN
        RAISE EXCEPTION 'Backup user ID is missing.';
    END IF;

    IF (backup_data->>'user_id')::UUID <> p_user_id THEN
        RAISE EXCEPTION 'Backup belongs to a different user.';
    END IF;

    IF backup_data->'tables' IS NULL
       OR jsonb_typeof(backup_data->'tables') <> 'object' THEN
        RAISE EXCEPTION 'Backup does not contain valid table data.';
    END IF;


    -- --------------------------------------------------------
    -- Helper validation:
    -- every restored row must belong to p_user_id.
    --
    -- The explicit loops are intentionally repetitive because
    -- this is security-sensitive database code.
    -- --------------------------------------------------------


    -- ========================================================
    -- ACCOUNTS
    -- ========================================================

    records := backup_data->'tables'->'accounts';

    IF records IS NOT NULL THEN

        IF jsonb_typeof(records) <> 'array' THEN
            RAISE EXCEPTION 'Invalid accounts backup data.';
        END IF;

        FOR record_item IN
            SELECT value FROM jsonb_array_elements(records)
        LOOP
            IF (record_item->>'user_id')::UUID <> p_user_id THEN
                RAISE EXCEPTION 'Account record belongs to another user.';
            END IF;
        END LOOP;

        INSERT INTO accounts (
            id,
            user_id,
            name,
            account_type,
            opening_balance,
            is_active,
            created_at,
            updated_at
        )
        SELECT
            id,
            user_id,
            name,
            account_type,
            opening_balance,
            is_active,
            created_at,
            updated_at
        FROM jsonb_populate_recordset(
            NULL::accounts,
            records
        )
        ON CONFLICT (id) DO UPDATE
        SET
            name = EXCLUDED.name,
            account_type = EXCLUDED.account_type,
            opening_balance = EXCLUDED.opening_balance,
            is_active = EXCLUDED.is_active,
            updated_at = EXCLUDED.updated_at
        WHERE accounts.user_id = p_user_id;

        GET DIAGNOSTICS record_count = ROW_COUNT;

    ELSE
        record_count := 0;
    END IF;

    restored_counts :=
        restored_counts ||
        jsonb_build_object('accounts', record_count);


    -- ========================================================
    -- CATEGORIES
    -- ========================================================

    records := backup_data->'tables'->'categories';

    IF records IS NOT NULL THEN

        IF jsonb_typeof(records) <> 'array' THEN
            RAISE EXCEPTION 'Invalid categories backup data.';
        END IF;

        FOR record_item IN
            SELECT value FROM jsonb_array_elements(records)
        LOOP
            IF (record_item->>'user_id')::UUID <> p_user_id THEN
                RAISE EXCEPTION 'Category record belongs to another user.';
            END IF;
        END LOOP;

        INSERT INTO categories (
            id,
            user_id,
            name,
            category_type,
            is_active,
            created_at,
            updated_at
        )
        SELECT
            id,
            user_id,
            name,
            category_type,
            is_active,
            created_at,
            updated_at
        FROM jsonb_populate_recordset(
            NULL::categories,
            records
        )
        ON CONFLICT (id) DO UPDATE
        SET
            name = EXCLUDED.name,
            category_type = EXCLUDED.category_type,
            is_active = EXCLUDED.is_active,
            updated_at = EXCLUDED.updated_at
        WHERE categories.user_id = p_user_id;

        GET DIAGNOSTICS record_count = ROW_COUNT;

    ELSE
        record_count := 0;
    END IF;

    restored_counts :=
        restored_counts ||
        jsonb_build_object('categories', record_count);


    -- ========================================================
    -- PEOPLE
    -- ========================================================

    records := backup_data->'tables'->'people';

    IF records IS NOT NULL THEN

        IF jsonb_typeof(records) <> 'array' THEN
            RAISE EXCEPTION 'Invalid people backup data.';
        END IF;

        FOR record_item IN
            SELECT value FROM jsonb_array_elements(records)
        LOOP
            IF (record_item->>'user_id')::UUID <> p_user_id THEN
                RAISE EXCEPTION 'People record belongs to another user.';
            END IF;
        END LOOP;

        INSERT INTO people (
            id,
            user_id,
            name,
            notes,
            created_at,
            updated_at
        )
        SELECT
            id,
            user_id,
            name,
            notes,
            created_at,
            updated_at
        FROM jsonb_populate_recordset(
            NULL::people,
            records
        )
        ON CONFLICT (id) DO UPDATE
        SET
            name = EXCLUDED.name,
            notes = EXCLUDED.notes,
            updated_at = EXCLUDED.updated_at
        WHERE people.user_id = p_user_id;

        GET DIAGNOSTICS record_count = ROW_COUNT;

    ELSE
        record_count := 0;
    END IF;

    restored_counts :=
        restored_counts ||
        jsonb_build_object('people', record_count);


    -- ========================================================
    -- SAVINGS GOALS
    -- ========================================================

    records := backup_data->'tables'->'savings_goals';

    IF records IS NOT NULL THEN

        IF jsonb_typeof(records) <> 'array' THEN
            RAISE EXCEPTION 'Invalid savings goals backup data.';
        END IF;

        FOR record_item IN
            SELECT value FROM jsonb_array_elements(records)
        LOOP
            IF (record_item->>'user_id')::UUID <> p_user_id THEN
                RAISE EXCEPTION 'Savings goal belongs to another user.';
            END IF;
        END LOOP;

        INSERT INTO savings_goals (
            id,
            user_id,
            name,
            target_amount,
            target_date,
            status,
            notes,
            created_at,
            updated_at
        )
        SELECT
            id,
            user_id,
            name,
            target_amount,
            target_date,
            status,
            notes,
            created_at,
            updated_at
        FROM jsonb_populate_recordset(
            NULL::savings_goals,
            records
        )
        ON CONFLICT (id) DO UPDATE
        SET
            name = EXCLUDED.name,
            target_amount = EXCLUDED.target_amount,
            target_date = EXCLUDED.target_date,
            status = EXCLUDED.status,
            notes = EXCLUDED.notes,
            updated_at = EXCLUDED.updated_at
        WHERE savings_goals.user_id = p_user_id;

        GET DIAGNOSTICS record_count = ROW_COUNT;

    ELSE
        record_count := 0;
    END IF;

    restored_counts :=
        restored_counts ||
        jsonb_build_object('savings_goals', record_count);


    -- ========================================================
    -- TRANSACTIONS
    -- ========================================================
    --
    -- Transactions are restored after their referenced master
    -- records and before their dependent child records.

    records := backup_data->'tables'->'transactions';

    IF records IS NOT NULL THEN

        IF jsonb_typeof(records) <> 'array' THEN
            RAISE EXCEPTION 'Invalid transactions backup data.';
        END IF;

        FOR record_item IN
            SELECT value FROM jsonb_array_elements(records)
        LOOP
            IF (record_item->>'user_id')::UUID <> p_user_id THEN
                RAISE EXCEPTION 'Transaction record belongs to another user.';
            END IF;
        END LOOP;

        INSERT INTO transactions (
            id,
            user_id,
            transaction_date,
            transaction_type,
            amount,
            source_account_id,
            destination_account_id,
            category_id,
            payment_method,
            person_id,
            description,
            notes,
            created_at,
            updated_at
        )
        SELECT
            id,
            user_id,
            transaction_date,
            transaction_type,
            amount,
            source_account_id,
            destination_account_id,
            category_id,
            payment_method,
            person_id,
            description,
            notes,
            created_at,
            updated_at
        FROM jsonb_populate_recordset(
            NULL::transactions,
            records
        )
        ON CONFLICT (id) DO UPDATE
        SET
            transaction_date = EXCLUDED.transaction_date,
            transaction_type = EXCLUDED.transaction_type,
            amount = EXCLUDED.amount,
            source_account_id = EXCLUDED.source_account_id,
            destination_account_id = EXCLUDED.destination_account_id,
            category_id = EXCLUDED.category_id,
            payment_method = EXCLUDED.payment_method,
            person_id = EXCLUDED.person_id,
            description = EXCLUDED.description,
            notes = EXCLUDED.notes,
            updated_at = EXCLUDED.updated_at
        WHERE transactions.user_id = p_user_id;

        GET DIAGNOSTICS record_count = ROW_COUNT;

    ELSE
        record_count := 0;
    END IF;

    restored_counts :=
        restored_counts ||
        jsonb_build_object('transactions', record_count);


    -- ========================================================
    -- TRANSFERS
    -- ========================================================

    records := backup_data->'tables'->'transfers';

    IF records IS NOT NULL THEN

        IF jsonb_typeof(records) <> 'array' THEN
            RAISE EXCEPTION 'Invalid transfers backup data.';
        END IF;

        FOR record_item IN
            SELECT value FROM jsonb_array_elements(records)
        LOOP
            IF (record_item->>'user_id')::UUID <> p_user_id THEN
                RAISE EXCEPTION 'Transfer record belongs to another user.';
            END IF;
        END LOOP;

        INSERT INTO transfers (
            id,
            user_id,
            transaction_id,
            from_account_id,
            to_account_id,
            amount,
            transfer_date,
            description,
            created_at,
            updated_at
        )
        SELECT
            id,
            user_id,
            transaction_id,
            from_account_id,
            to_account_id,
            amount,
            transfer_date,
            description,
            created_at,
            updated_at
        FROM jsonb_populate_recordset(
            NULL::transfers,
            records
        )
        ON CONFLICT (id) DO UPDATE
        SET
            transaction_id = EXCLUDED.transaction_id,
            from_account_id = EXCLUDED.from_account_id,
            to_account_id = EXCLUDED.to_account_id,
            amount = EXCLUDED.amount,
            transfer_date = EXCLUDED.transfer_date,
            description = EXCLUDED.description,
            updated_at = EXCLUDED.updated_at
        WHERE transfers.user_id = p_user_id;

        GET DIAGNOSTICS record_count = ROW_COUNT;

    ELSE
        record_count := 0;
    END IF;

    restored_counts :=
        restored_counts ||
        jsonb_build_object('transfers', record_count);


    -- ========================================================
    -- FRIENDS' MONEY
    -- ========================================================

    records := backup_data->'tables'->'friends_money';

    IF records IS NOT NULL THEN

        IF jsonb_typeof(records) <> 'array' THEN
            RAISE EXCEPTION 'Invalid friends_money backup data.';
        END IF;

        FOR record_item IN
            SELECT value FROM jsonb_array_elements(records)
        LOOP
            IF (record_item->>'user_id')::UUID <> p_user_id THEN
                RAISE EXCEPTION 'Friends money record belongs to another user.';
            END IF;
        END LOOP;

        INSERT INTO friends_money (
            id,
            user_id,
            person_id,
            transaction_id,
            account_id,
            amount_received,
            amount_returned,
            received_date,
            expected_return_date,
            status,
            notes,
            created_at,
            updated_at
        )
        SELECT
            id,
            user_id,
            person_id,
            transaction_id,
            account_id,
            amount_received,
            amount_returned,
            received_date,
            expected_return_date,
            status,
            notes,
            created_at,
            updated_at
        FROM jsonb_populate_recordset(
            NULL::friends_money,
            records
        )
        ON CONFLICT (id) DO UPDATE
        SET
            person_id = EXCLUDED.person_id,
            transaction_id = EXCLUDED.transaction_id,
            account_id = EXCLUDED.account_id,
            amount_received = EXCLUDED.amount_received,
            amount_returned = EXCLUDED.amount_returned,
            received_date = EXCLUDED.received_date,
            expected_return_date = EXCLUDED.expected_return_date,
            status = EXCLUDED.status,
            notes = EXCLUDED.notes,
            updated_at = EXCLUDED.updated_at
        WHERE friends_money.user_id = p_user_id;

        GET DIAGNOSTICS record_count = ROW_COUNT;

    ELSE
        record_count := 0;
    END IF;

    restored_counts :=
        restored_counts ||
        jsonb_build_object('friends_money', record_count);


    -- ========================================================
    -- BUDGETS
    -- ========================================================

    records := backup_data->'tables'->'budgets';

    IF records IS NOT NULL THEN

        IF jsonb_typeof(records) <> 'array' THEN
            RAISE EXCEPTION 'Invalid budgets backup data.';
        END IF;

        FOR record_item IN
            SELECT value FROM jsonb_array_elements(records)
        LOOP
            IF (record_item->>'user_id')::UUID <> p_user_id THEN
                RAISE EXCEPTION 'Budget record belongs to another user.';
            END IF;
        END LOOP;

        INSERT INTO budgets (
            id,
            user_id,
            category_id,
            budget_month,
            budget_year,
            budget_amount,
            created_at,
            updated_at
        )
        SELECT
            id,
            user_id,
            category_id,
            budget_month,
            budget_year,
            budget_amount,
            created_at,
            updated_at
        FROM jsonb_populate_recordset(
            NULL::budgets,
            records
        )
        ON CONFLICT (id) DO UPDATE
        SET
            category_id = EXCLUDED.category_id,
            budget_month = EXCLUDED.budget_month,
            budget_year = EXCLUDED.budget_year,
            budget_amount = EXCLUDED.budget_amount,
            updated_at = EXCLUDED.updated_at
        WHERE budgets.user_id = p_user_id;

        GET DIAGNOSTICS record_count = ROW_COUNT;

    ELSE
        record_count := 0;
    END IF;

    restored_counts :=
        restored_counts ||
        jsonb_build_object('budgets', record_count);


    -- ========================================================
    -- SAVINGS CONTRIBUTIONS
    -- ========================================================

    records := backup_data->'tables'->'savings_contributions';

    IF records IS NOT NULL THEN

        IF jsonb_typeof(records) <> 'array' THEN
            RAISE EXCEPTION 'Invalid savings contributions backup data.';
        END IF;

        FOR record_item IN
            SELECT value FROM jsonb_array_elements(records)
        LOOP
            IF (record_item->>'user_id')::UUID <> p_user_id THEN
                RAISE EXCEPTION 'Savings contribution belongs to another user.';
            END IF;
        END LOOP;

        INSERT INTO savings_contributions (
            id,
            user_id,
            savings_goal_id,
            transaction_id,
            account_id,
            amount,
            contribution_date,
            notes,
            created_at,
            updated_at
        )
        SELECT
            id,
            user_id,
            savings_goal_id,
            transaction_id,
            account_id,
            amount,
            contribution_date,
            notes,
            created_at,
            updated_at
        FROM jsonb_populate_recordset(
            NULL::savings_contributions,
            records
        )
        ON CONFLICT (id) DO UPDATE
        SET
            savings_goal_id = EXCLUDED.savings_goal_id,
            transaction_id = EXCLUDED.transaction_id,
            account_id = EXCLUDED.account_id,
            amount = EXCLUDED.amount,
            contribution_date = EXCLUDED.contribution_date,
            notes = EXCLUDED.notes,
            updated_at = EXCLUDED.updated_at
        WHERE savings_contributions.user_id = p_user_id;

        GET DIAGNOSTICS record_count = ROW_COUNT;

    ELSE
        record_count := 0;
    END IF;

    restored_counts :=
        restored_counts ||
        jsonb_build_object('savings_contributions', record_count);


    -- ========================================================
    -- RECURRING TRANSACTIONS
    -- ========================================================

    records := backup_data->'tables'->'recurring_transactions';

    IF records IS NOT NULL THEN

        IF jsonb_typeof(records) <> 'array' THEN
            RAISE EXCEPTION 'Invalid recurring transactions backup data.';
        END IF;

        FOR record_item IN
            SELECT value FROM jsonb_array_elements(records)
        LOOP
            IF (record_item->>'user_id')::UUID <> p_user_id THEN
                RAISE EXCEPTION 'Recurring transaction belongs to another user.';
            END IF;
        END LOOP;

        INSERT INTO recurring_transactions (
            id,
            user_id,
            transaction_name,
            transaction_type,
            amount,
            account_id,
            destination_account_id,
            category_id,
            payment_method,
            frequency,
            start_date,
            next_due_date,
            is_active,
            auto_create,
            notes,
            created_at,
            updated_at
        )
        SELECT
            id,
            user_id,
            transaction_name,
            transaction_type,
            amount,
            account_id,
            destination_account_id,
            category_id,
            payment_method,
            frequency,
            start_date,
            next_due_date,
            is_active,
            auto_create,
            notes,
            created_at,
            updated_at
        FROM jsonb_populate_recordset(
            NULL::recurring_transactions,
            records
        )
        ON CONFLICT (id) DO UPDATE
        SET
            transaction_name = EXCLUDED.transaction_name,
            transaction_type = EXCLUDED.transaction_type,
            amount = EXCLUDED.amount,
            account_id = EXCLUDED.account_id,
            destination_account_id = EXCLUDED.destination_account_id,
            category_id = EXCLUDED.category_id,
            payment_method = EXCLUDED.payment_method,
            frequency = EXCLUDED.frequency,
            start_date = EXCLUDED.start_date,
            next_due_date = EXCLUDED.next_due_date,
            is_active = EXCLUDED.is_active,
            auto_create = EXCLUDED.auto_create,
            notes = EXCLUDED.notes,
            updated_at = EXCLUDED.updated_at
        WHERE recurring_transactions.user_id = p_user_id;

        GET DIAGNOSTICS record_count = ROW_COUNT;

    ELSE
        record_count := 0;
    END IF;

    restored_counts :=
        restored_counts ||
        jsonb_build_object('recurring_transactions', record_count);


    -- ========================================================
    -- BACKUP HISTORY
    -- ========================================================

    records := backup_data->'tables'->'backup_history';

    IF records IS NOT NULL THEN

        IF jsonb_typeof(records) <> 'array' THEN
            RAISE EXCEPTION 'Invalid backup history data.';
        END IF;

        FOR record_item IN
            SELECT value FROM jsonb_array_elements(records)
        LOOP
            IF (record_item->>'user_id')::UUID <> p_user_id THEN
                RAISE EXCEPTION 'Backup history record belongs to another user.';
            END IF;
        END LOOP;

        INSERT INTO backup_history (
            id,
            user_id,
            backup_type,
            backup_filename,
            backup_version,
            record_count,
            created_at
        )
        SELECT
            id,
            user_id,
            backup_type,
            backup_filename,
            backup_version,
            record_count,
            created_at
        FROM jsonb_populate_recordset(
            NULL::backup_history,
            records
        )
        ON CONFLICT (id) DO UPDATE
        SET
            backup_type = EXCLUDED.backup_type,
            backup_filename = EXCLUDED.backup_filename,
            backup_version = EXCLUDED.backup_version,
            record_count = EXCLUDED.record_count,
            created_at = EXCLUDED.created_at
        WHERE backup_history.user_id = p_user_id;

        GET DIAGNOSTICS record_count = ROW_COUNT;

    ELSE
        record_count := 0;
    END IF;

    restored_counts :=
        restored_counts ||
        jsonb_build_object('backup_history', record_count);


    -- ========================================================
    -- APP SETTINGS
    -- ========================================================

    records := backup_data->'tables'->'app_settings';

    IF records IS NOT NULL THEN

        IF jsonb_typeof(records) <> 'array' THEN
            RAISE EXCEPTION 'Invalid app settings backup data.';
        END IF;

        FOR record_item IN
            SELECT value FROM jsonb_array_elements(records)
        LOOP
            IF (record_item->>'user_id')::UUID <> p_user_id THEN
                RAISE EXCEPTION 'App setting belongs to another user.';
            END IF;
        END LOOP;

        INSERT INTO app_settings (
            id,
            user_id,
            setting_key,
            setting_value,
            created_at,
            updated_at
        )
        SELECT
            id,
            user_id,
            setting_key,
            setting_value,
            created_at,
            updated_at
        FROM jsonb_populate_recordset(
            NULL::app_settings,
            records
        )
        ON CONFLICT (id) DO UPDATE
        SET
            setting_key = EXCLUDED.setting_key,
            setting_value = EXCLUDED.setting_value,
            updated_at = EXCLUDED.updated_at
        WHERE app_settings.user_id = p_user_id;

        GET DIAGNOSTICS record_count = ROW_COUNT;

    ELSE
        record_count := 0;
    END IF;

    restored_counts :=
        restored_counts ||
        jsonb_build_object('app_settings', record_count);


    -- ========================================================
    -- MONEY LENT
    -- ========================================================

    records := backup_data->'tables'->'money_lent';

    IF records IS NOT NULL THEN

        IF jsonb_typeof(records) <> 'array' THEN
            RAISE EXCEPTION 'Invalid money lent backup data.';
        END IF;

        FOR record_item IN
            SELECT value FROM jsonb_array_elements(records)
        LOOP
            IF (record_item->>'user_id')::UUID <> p_user_id THEN
                RAISE EXCEPTION 'Money lent record belongs to another user.';
            END IF;
        END LOOP;

        INSERT INTO money_lent (
            id,
            user_id,
            person_id,
            transaction_id,
            account_id,
            amount_lent,
            amount_returned,
            lent_date,
            expected_return_date,
            status,
            notes,
            created_at,
            updated_at
        )
        SELECT
            id,
            user_id,
            person_id,
            transaction_id,
            account_id,
            amount_lent,
            amount_returned,
            lent_date,
            expected_return_date,
            status,
            notes,
            created_at,
            updated_at
        FROM jsonb_populate_recordset(
            NULL::money_lent,
            records
        )
        ON CONFLICT (id) DO UPDATE
        SET
            person_id = EXCLUDED.person_id,
            transaction_id = EXCLUDED.transaction_id,
            account_id = EXCLUDED.account_id,
            amount_lent = EXCLUDED.amount_lent,
            amount_returned = EXCLUDED.amount_returned,
            lent_date = EXCLUDED.lent_date,
            expected_return_date = EXCLUDED.expected_return_date,
            status = EXCLUDED.status,
            notes = EXCLUDED.notes,
            updated_at = EXCLUDED.updated_at
        WHERE money_lent.user_id = p_user_id;

        GET DIAGNOSTICS record_count = ROW_COUNT;

    ELSE
        record_count := 0;
    END IF;

    restored_counts :=
        restored_counts ||
        jsonb_build_object('money_lent', record_count);


    -- ========================================================
    -- FINAL RESULT
    -- ========================================================

    RETURN jsonb_build_object(
        'backup_version',
        backup_data->>'backup_version',

        'user_id',
        p_user_id,

        'restored_counts',
        restored_counts,

        'total_records',
        (
            SELECT COALESCE(
                SUM((value)::INTEGER),
                0
            )
            FROM jsonb_each_text(restored_counts)
        )
    );

END;
$$;


-- ============================================================
-- 17. FUNCTION PRIVILEGES
-- ============================================================

-- Prevent ordinary anon/authenticated callers from executing
-- the SECURITY DEFINER restore function directly.
REVOKE ALL
ON FUNCTION restore_expense_tracker_backup(JSONB, UUID)
FROM PUBLIC;

REVOKE ALL
ON FUNCTION restore_expense_tracker_backup(JSONB, UUID)
FROM anon;

REVOKE ALL
ON FUNCTION restore_expense_tracker_backup(JSONB, UUID)
FROM authenticated;


-- ============================================================
-- 18. SCHEMA NOTES
-- ============================================================

-- Money calculations MUST use NUMERIC, never FLOAT/REAL.
--
-- Transfers:
--   internal_transfer is neither income nor expense.
--
-- Friend's money:
--   friend_money_received increases account balance but represents
--   a liability and is therefore excluded from "actual money".
--
-- Money lent:
--   friend_money_lent decreases account balance but is NOT an
--   expense.
--
-- Money returned:
--   friend_money_lent_returned increases the original account
--   balance but is NOT income.
--
-- Savings contributions:
--   treated as an internal movement and not normal spending.
--
-- Account balances are derived from opening_balance plus the
-- transaction ledger. The database does not store a mutable
-- current_balance column.
--
-- Application services MUST always filter by user_id.
--
-- The database additionally enforces same-user relationships
-- through composite foreign keys such as:
--     (user_id, account_id)
--     (user_id, category_id)
--     (user_id, person_id)
--     (user_id, transaction_id)
--
-- app_users is intentionally excluded from JSON/CSV application
-- backups. Authentication credentials must never be restored
-- from a personal financial backup.


-- ============================================================
-- END OF CANONICAL SCHEMA
-- ============================================================
