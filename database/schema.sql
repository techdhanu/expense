-- ============================================================
-- PERSONAL EXPENSE TRACKER
-- Supabase PostgreSQL Database Schema
-- ============================================================

-- Required extension for UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- ============================================================
-- 1. APP ACCESS / USERS
-- ============================================================

CREATE TABLE IF NOT EXISTS app_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    username VARCHAR(100) NOT NULL UNIQUE,

    password_hash TEXT NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- 2. ACCOUNTS
-- ============================================================

CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(100) NOT NULL UNIQUE,

    account_type VARCHAR(50) NOT NULL DEFAULT 'bank',

    opening_balance NUMERIC(15, 2) NOT NULL DEFAULT 0,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT accounts_opening_balance_non_negative
        CHECK (opening_balance >= 0),

    CONSTRAINT accounts_account_type_valid
        CHECK (
            account_type IN (
                'bank',
                'cash',
                'other'
            )
        )
);


-- ============================================================
-- 3. CATEGORIES
-- ============================================================

CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(100) NOT NULL,

    category_type VARCHAR(20) NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT categories_type_valid
        CHECK (
            category_type IN (
                'income',
                'expense'
            )
        ),

    CONSTRAINT categories_unique_name_type
        UNIQUE (name, category_type)
);


-- ============================================================
-- 4. PEOPLE
-- ============================================================

CREATE TABLE IF NOT EXISTS people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(150) NOT NULL UNIQUE,

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- 5. TRANSACTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

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

    CONSTRAINT transactions_source_account_fk
        FOREIGN KEY (source_account_id)
        REFERENCES accounts(id)
        ON DELETE RESTRICT,

    CONSTRAINT transactions_destination_account_fk
        FOREIGN KEY (destination_account_id)
        REFERENCES accounts(id)
        ON DELETE RESTRICT,

    CONSTRAINT transactions_category_fk
        FOREIGN KEY (category_id)
        REFERENCES categories(id)
        ON DELETE RESTRICT,

    CONSTRAINT transactions_person_fk
        FOREIGN KEY (person_id)
        REFERENCES people(id)
        ON DELETE RESTRICT
);


-- ============================================================
-- 6. TRANSFERS
-- ============================================================

CREATE TABLE IF NOT EXISTS transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    transaction_id UUID NOT NULL UNIQUE,

    from_account_id UUID NOT NULL,

    to_account_id UUID NOT NULL,

    amount NUMERIC(15, 2) NOT NULL,

    transfer_date DATE NOT NULL,

    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT transfers_amount_positive
        CHECK (amount > 0),

    CONSTRAINT transfers_different_accounts
        CHECK (from_account_id <> to_account_id),

    CONSTRAINT transfers_transaction_fk
        FOREIGN KEY (transaction_id)
        REFERENCES transactions(id)
        ON DELETE CASCADE,

    CONSTRAINT transfers_from_account_fk
        FOREIGN KEY (from_account_id)
        REFERENCES accounts(id)
        ON DELETE RESTRICT,

    CONSTRAINT transfers_to_account_fk
        FOREIGN KEY (to_account_id)
        REFERENCES accounts(id)
        ON DELETE RESTRICT
);


-- ============================================================
-- 7. FRIENDS' MONEY
-- ============================================================

CREATE TABLE IF NOT EXISTS friends_money (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

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
        FOREIGN KEY (person_id)
        REFERENCES people(id)
        ON DELETE RESTRICT,

    CONSTRAINT friends_money_transaction_fk
        FOREIGN KEY (transaction_id)
        REFERENCES transactions(id)
        ON DELETE RESTRICT,

    CONSTRAINT friends_money_account_fk
        FOREIGN KEY (account_id)
        REFERENCES accounts(id)
        ON DELETE RESTRICT
);


-- ============================================================
-- 8. BUDGETS
-- ============================================================

CREATE TABLE IF NOT EXISTS budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    category_id UUID NOT NULL,

    budget_month INTEGER NOT NULL,

    budget_year INTEGER NOT NULL,

    budget_amount NUMERIC(15, 2) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT budgets_month_valid
        CHECK (budget_month BETWEEN 1 AND 12),

    CONSTRAINT budgets_year_valid
        CHECK (budget_year >= 2000),

    CONSTRAINT budgets_amount_positive
        CHECK (budget_amount > 0),

    CONSTRAINT budgets_category_fk
        FOREIGN KEY (category_id)
        REFERENCES categories(id)
        ON DELETE RESTRICT,

    CONSTRAINT budgets_unique_category_month
        UNIQUE (
            category_id,
            budget_month,
            budget_year
        )
);


-- ============================================================
-- 9. SAVINGS GOALS
-- ============================================================

CREATE TABLE IF NOT EXISTS savings_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(150) NOT NULL,

    target_amount NUMERIC(15, 2) NOT NULL,

    target_date DATE,

    status VARCHAR(30) NOT NULL DEFAULT 'active',

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT savings_goals_target_positive
        CHECK (target_amount > 0),

    CONSTRAINT savings_goals_status_valid
        CHECK (
            status IN (
                'active',
                'completed',
                'cancelled'
            )
        )
);


-- ============================================================
-- 10. SAVINGS CONTRIBUTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS savings_contributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    savings_goal_id UUID NOT NULL,

    transaction_id UUID,

    account_id UUID NOT NULL,

    amount NUMERIC(15, 2) NOT NULL,

    contribution_date DATE NOT NULL,

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT savings_contributions_amount_positive
        CHECK (amount > 0),

    CONSTRAINT savings_contributions_goal_fk
        FOREIGN KEY (savings_goal_id)
        REFERENCES savings_goals(id)
        ON DELETE CASCADE,

    CONSTRAINT savings_contributions_transaction_fk
        FOREIGN KEY (transaction_id)
        REFERENCES transactions(id)
        ON DELETE RESTRICT,

    CONSTRAINT savings_contributions_account_fk
        FOREIGN KEY (account_id)
        REFERENCES accounts(id)
        ON DELETE RESTRICT
);


-- ============================================================
-- 11. RECURRING TRANSACTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS recurring_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

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

    CONSTRAINT recurring_source_destination_different
        CHECK (
            account_id IS NULL
            OR destination_account_id IS NULL
            OR account_id <> destination_account_id
        ),

    CONSTRAINT recurring_account_fk
        FOREIGN KEY (account_id)
        REFERENCES accounts(id)
        ON DELETE RESTRICT,

    CONSTRAINT recurring_destination_account_fk
        FOREIGN KEY (destination_account_id)
        REFERENCES accounts(id)
        ON DELETE RESTRICT,

    CONSTRAINT recurring_category_fk
        FOREIGN KEY (category_id)
        REFERENCES categories(id)
        ON DELETE RESTRICT
);


-- ============================================================
-- 12. BACKUP HISTORY
-- ============================================================

CREATE TABLE IF NOT EXISTS backup_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    backup_type VARCHAR(20) NOT NULL,

    backup_filename VARCHAR(255) NOT NULL,

    backup_version VARCHAR(20) NOT NULL,

    record_count INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

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


-- ============================================================
-- 13. APP SETTINGS
-- ============================================================

CREATE TABLE IF NOT EXISTS app_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    setting_key VARCHAR(100) NOT NULL UNIQUE,

    setting_value TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);