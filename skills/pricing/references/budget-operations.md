# Budget Operations

## get_budget_balance
Returns remaining budget for a currency.

**Parameters:**
- `currency` (required): IDR, THB, VND, MYR, SGD, PHP

**Response fields:**
- `totalBudget`: allocated amount
- `usedBudget`: spent amount  
- `remainingBudget`: totalBudget - usedBudget
- `utilizationRate`: percentage used

## list_active_budgets
Lists all active budgets filtered by currency.

## get_budget_levels
Returns budget hierarchy levels (GLOBAL → COUNTRY → AIRLINE → ROUTE).

## get_budget_user_balance
Per-user budget allocation and spend.
