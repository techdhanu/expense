
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

-- ============================================================
-- ATOMIC JSON BACKUP RESTORE
-- ============================================================

create or replace function restore_expense_tracker_backup(backup_data jsonb)
returns jsonb
language plpgsql
security definer
as $$
declare
    table_name text;
    records jsonb;
    restored_counts jsonb := '{}'::jsonb;
    record_count integer;
begin
    -- Validate top-level structure
    if backup_data->>'backup_version' is null then
        raise exception 'Backup version is missing.';
    end if;

    if backup_data->'tables' is null
       or jsonb_typeof(backup_data->'tables') <> 'object' then
        raise exception 'Backup does not contain valid table data.';
    end if;

    -- Restore in foreign-key-safe order.
    -- PostgreSQL automatically rolls back the entire function
    -- if any statement raises an exception.

    -- app_users
    records := backup_data->'tables'->'app_users';
    if records is not null and jsonb_array_length(records) > 0 then
        insert into app_users
        select *
        from jsonb_populate_recordset(null::app_users, records)
        on conflict (id) do update set
            username = excluded.username,
            password_hash = excluded.password_hash,
            is_active = excluded.is_active,
            updated_at = excluded.updated_at;

        get diagnostics record_count = row_count;
    else
        record_count := 0;
    end if;
    restored_counts := restored_counts || jsonb_build_object('app_users', record_count);

    -- accounts
    records := backup_data->'tables'->'accounts';
    if records is not null and jsonb_array_length(records) > 0 then
        insert into accounts
        select *
        from jsonb_populate_recordset(null::accounts, records)
        on conflict (id) do update set
            name = excluded.name,
            account_type = excluded.account_type,
            opening_balance = excluded.opening_balance,
            is_active = excluded.is_active,
            updated_at = excluded.updated_at;

        get diagnostics record_count = row_count;
    else
        record_count := 0;
    end if;
    restored_counts := restored_counts || jsonb_build_object('accounts', record_count);

    -- categories
    records := backup_data->'tables'->'categories';
    if records is not null and jsonb_array_length(records) > 0 then
        insert into categories
        select *
        from jsonb_populate_recordset(null::categories, records)
        on conflict (id) do update set
            name = excluded.name,
            category_type = excluded.category_type,
            is_active = excluded.is_active,
            updated_at = excluded.updated_at;

        get diagnostics record_count = row_count;
    else
        record_count := 0;
    end if;
    restored_counts := restored_counts || jsonb_build_object('categories', record_count);

    -- people
    records := backup_data->'tables'->'people';
    if records is not null and jsonb_array_length(records) > 0 then
        insert into people
        select *
        from jsonb_populate_recordset(null::people, records)
        on conflict (id) do update set
            name = excluded.name,
            notes = excluded.notes,
            updated_at = excluded.updated_at;

        get diagnostics record_count = row_count;
    else
        record_count := 0;
    end if;
    restored_counts := restored_counts || jsonb_build_object('people', record_count);

    -- transactions
    records := backup_data->'tables'->'transactions';
    if records is not null and jsonb_array_length(records) > 0 then
        insert into transactions
        select *
        from jsonb_populate_recordset(null::transactions, records)
        on conflict (id) do update set
            transaction_date = excluded.transaction_date,
            transaction_type = excluded.transaction_type,
            amount = excluded.amount,
            source_account_id = excluded.source_account_id,
            destination_account_id = excluded.destination_account_id,
            category_id = excluded.category_id,
            person_id = excluded.person_id,
            payment_method = excluded.payment_method,
            description = excluded.description,
            notes = excluded.notes,
            updated_at = excluded.updated_at;

        get diagnostics record_count = row_count;
    else
        record_count := 0;
    end if;
    restored_counts := restored_counts || jsonb_build_object('transactions', record_count);

    -- transfers
    records := backup_data->'tables'->'transfers';
    if records is not null and jsonb_array_length(records) > 0 then
        insert into transfers
        select *
        from jsonb_populate_recordset(null::transfers, records)
        on conflict (id) do update set
            transaction_id = excluded.transaction_id,
            from_account_id = excluded.from_account_id,
            to_account_id = excluded.to_account_id,
            amount = excluded.amount,
            transfer_date = excluded.transfer_date,
            description = excluded.description,
            updated_at = excluded.updated_at;

        get diagnostics record_count = row_count;
    else
        record_count := 0;
    end if;
    restored_counts := restored_counts || jsonb_build_object('transfers', record_count);

    -- friends_money
    records := backup_data->'tables'->'friends_money';
    if records is not null and jsonb_array_length(records) > 0 then
        insert into friends_money
        select *
        from jsonb_populate_recordset(null::friends_money, records)
        on conflict (id) do update set
            person_id = excluded.person_id,
            transaction_id = excluded.transaction_id,
            account_id = excluded.account_id,
            amount_received = excluded.amount_received,
            amount_returned = excluded.amount_returned,
            received_date = excluded.received_date,
            expected_return_date = excluded.expected_return_date,
            status = excluded.status,
            notes = excluded.notes,
            updated_at = excluded.updated_at;

        get diagnostics record_count = row_count;
    else
        record_count := 0;
    end if;
    restored_counts := restored_counts || jsonb_build_object('friends_money', record_count);

    -- budgets
    records := backup_data->'tables'->'budgets';
    if records is not null and jsonb_array_length(records) > 0 then
        insert into budgets
        select *
        from jsonb_populate_recordset(null::budgets, records)
        on conflict (id) do update set
            category_id = excluded.category_id,
            budget_month = excluded.budget_month,
            budget_year = excluded.budget_year,
            budget_amount = excluded.budget_amount,
            updated_at = excluded.updated_at;

        get diagnostics record_count = row_count;
    else
        record_count := 0;
    end if;
    restored_counts := restored_counts || jsonb_build_object('budgets', record_count);

    -- savings_goals
    records := backup_data->'tables'->'savings_goals';
    if records is not null and jsonb_array_length(records) > 0 then
        insert into savings_goals
        select *
        from jsonb_populate_recordset(null::savings_goals, records)
        on conflict (id) do update set
            name = excluded.name,
            target_amount = excluded.target_amount,
            target_date = excluded.target_date,
            status = excluded.status,
            notes = excluded.notes,
            updated_at = excluded.updated_at;

        get diagnostics record_count = row_count;
    else
        record_count := 0;
    end if;
    restored_counts := restored_counts || jsonb_build_object('savings_goals', record_count);

    -- savings_contributions
    records := backup_data->'tables'->'savings_contributions';
    if records is not null and jsonb_array_length(records) > 0 then
        insert into savings_contributions
        select *
        from jsonb_populate_recordset(null::savings_contributions, records)
        on conflict (id) do update set
            savings_goal_id = excluded.savings_goal_id,
            transaction_id = excluded.transaction_id,
            account_id = excluded.account_id,
            amount = excluded.amount,
            contribution_date = excluded.contribution_date,
            notes = excluded.notes;

        get diagnostics record_count = row_count;
    else
        record_count := 0;
    end if;
    restored_counts := restored_counts || jsonb_build_object('savings_contributions', record_count);

    -- recurring_transactions
    records := backup_data->'tables'->'recurring_transactions';
    if records is not null and jsonb_array_length(records) > 0 then
        insert into recurring_transactions
        select *
        from jsonb_populate_recordset(null::recurring_transactions, records)
        on conflict (id) do update set
            transaction_name = excluded.transaction_name,
            transaction_type = excluded.transaction_type,
            amount = excluded.amount,
            account_id = excluded.account_id,
            destination_account_id = excluded.destination_account_id,
            category_id = excluded.category_id,
            payment_method = excluded.payment_method,
            frequency = excluded.frequency,
            start_date = excluded.start_date,
            next_due_date = excluded.next_due_date,
            auto_create = excluded.auto_create,
            is_active = excluded.is_active,
            notes = excluded.notes,
            updated_at = excluded.updated_at;

        get diagnostics record_count = row_count;
    else
        record_count := 0;
    end if;
    restored_counts := restored_counts || jsonb_build_object('recurring_transactions', record_count);

    -- backup_history
    records := backup_data->'tables'->'backup_history';
    if records is not null and jsonb_array_length(records) > 0 then
        insert into backup_history
        select *
        from jsonb_populate_recordset(null::backup_history, records)
        on conflict (id) do update set
            backup_type = excluded.backup_type,
            backup_filename = excluded.backup_filename,
            backup_version = excluded.backup_version,
            record_count = excluded.record_count,
            created_at = excluded.created_at;

        get diagnostics record_count = row_count;
    else
        record_count := 0;
    end if;
    restored_counts := restored_counts || jsonb_build_object('backup_history', record_count);

    -- app_settings
    records := backup_data->'tables'->'app_settings';
    if records is not null and jsonb_array_length(records) > 0 then
        insert into app_settings
        select *
        from jsonb_populate_recordset(null::app_settings, records)
        on conflict (id) do update set
            setting_key = excluded.setting_key,
            setting_value = excluded.setting_value,
            updated_at = excluded.updated_at;

        get diagnostics record_count = row_count;
    else
        record_count := 0;
    end if;
    restored_counts := restored_counts || jsonb_build_object('app_settings', record_count);

    return jsonb_build_object(
        'backup_version', backup_data->>'backup_version',
        'restored_counts', restored_counts,
        'total_records',
        (
            select sum((value)::integer)
            from jsonb_each_text(restored_counts)
        )
    );
end;
$$;

-- ============================================================
-- 7B. MONEY LENT TO FRIENDS
-- ============================================================

CREATE TABLE IF NOT EXISTS money_lent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

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
        FOREIGN KEY (person_id)
        REFERENCES people(id)
        ON DELETE RESTRICT,

    CONSTRAINT money_lent_transaction_fk
        FOREIGN KEY (transaction_id)
        REFERENCES transactions(id)
        ON DELETE RESTRICT,

    CONSTRAINT money_lent_account_fk
        FOREIGN KEY (account_id)
        REFERENCES accounts(id)
        ON DELETE RESTRICT
);
-- ============================================================
-- INDEXES FOR MONEY LENT
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_money_lent_person
    ON money_lent(person_id);

CREATE INDEX IF NOT EXISTS idx_money_lent_account
    ON money_lent(account_id);

CREATE INDEX IF NOT EXISTS idx_money_lent_status
    ON money_lent(status);

CREATE INDEX IF NOT EXISTS idx_money_lent_lent_date
    ON money_lent(lent_date);
