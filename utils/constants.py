# ============================================================
# APPLICATION CONSTANTS
# ============================================================


# ============================================================
# DEFAULT ACCOUNTS
# ============================================================

DEFAULT_ACCOUNTS = [
    {
        "name": "Salary Account",
        "account_type": "bank",
    },
    {
        "name": "General Account",
        "account_type": "bank",
    },
    {
        "name": "Savings / Money Held Account",
        "account_type": "bank",
    },
]


# ============================================================
# TRANSACTION TYPES
# ============================================================

TRANSACTION_TYPES = [
    "income",
    "expense",
    "internal_transfer",

    # Money received from friends temporarily
    "friend_money_received",

    # Money returned to friends
    "friend_money_returned",

    # Money lent to friends
    "friend_money_lent",

    # Money received back from friends
    "friend_money_lent_returned",

    # Manual balance correction
    "balance_adjustment",

    # Contribution toward a savings goal
    "savings_goal_contribution",
]


# ============================================================
# PAYMENT METHODS
# ============================================================

PAYMENT_METHODS = [
    "upi",
    "debit_card",
    "bank_transfer",
    "cash",
    "auto_debit",
    "other",
]


# ============================================================
# ACCOUNT TYPES
# ============================================================

ACCOUNT_TYPES = [
    "bank",
    "cash",
    "other",
]


# ============================================================
# RECURRING TRANSACTION FREQUENCIES
# ============================================================

RECURRING_FREQUENCIES = [
    "weekly",
    "monthly",
    "quarterly",
    "yearly",
]


# ============================================================
# BACKUP
# ============================================================

BACKUP_VERSION = "1.0"