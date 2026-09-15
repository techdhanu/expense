# ============================================================
# APPLICATION CONSTANTS
# ============================================================

# Default accounts required by the application
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


# Supported transaction types
TRANSACTION_TYPES = [
    "income",
    "expense",
    "internal_transfer",
    "friend_money_received",
    "friend_money_returned",
    "balance_adjustment",
    "savings_goal_contribution",
]


# Supported payment methods
PAYMENT_METHODS = [
    "upi",
    "debit_card",
    "bank_transfer",
    "cash",
    "auto_debit",
    "other",
]


# Supported account types
ACCOUNT_TYPES = [
    "bank",
    "cash",
    "other",
]


# Supported recurring frequencies
RECURRING_FREQUENCIES = [
    "weekly",
    "monthly",
    "quarterly",
    "yearly",
]


# Application backup version
BACKUP_VERSION = "1.0"