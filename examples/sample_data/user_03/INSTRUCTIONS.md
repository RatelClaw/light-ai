# USER 03 - PERSONAL FINANCE DATA
## Sample Data Overview
This folder contains personal financial data including transactions, investment portfolio, and budget analysis.

### Files:
- `financial_data.csv` - Personal transaction history with categories and balances
- `investment_portfolio.json` - Stock portfolio with performance metrics
- `budget_analysis.txt` - Detailed budget breakdown and financial planning

## API Testing Instructions

### 1. FILE UPLOAD (Sub-Layer 1)
Upload each file to test personal finance data:

```python
# Upload CSV file
api.upload_file(client_id, user_id, "financial_data.csv", "Transaction History")

# Upload JSON file
api.upload_json(client_id, user_id, portfolio_data, "Investment Portfolio")

# Upload text file
api.upload_file(client_id, user_id, "budget_analysis.txt", "Budget Analysis")
```

### 2. SQL QUERIES (Sub-Layer 2)
Test financial data analysis:

```sql
-- Spending by category
SELECT category, SUM(ABS(amount)) as total_spent, COUNT(*) as transactions
FROM structured_data.resource_[RESOURCE_ID]
WHERE type = 'Debit'
GROUP BY category
ORDER BY total_spent DESC;

-- Income vs expenses
SELECT type, SUM(amount) as total_amount, COUNT(*) as count
FROM structured_data.resource_[RESOURCE_ID]
GROUP BY type;

-- Daily balance tracking
SELECT date, balance, amount, description
FROM structured_data.resource_[RESOURCE_ID]
ORDER BY date;

-- Account-wise summary
SELECT account, SUM(amount) as net_change, COUNT(*) as transactions
FROM structured_data.resource_[RESOURCE_ID]
GROUP BY account;

-- Large transactions analysis
SELECT date, description, amount, category
FROM structured_data.resource_[RESOURCE_ID]
WHERE ABS(amount) > 500
ORDER BY ABS(amount) DESC;
```

### 3. NATURAL LANGUAGE QUERIES
Test personal finance questions:

```
"How much did I spend on food this month?"
"What's my total income for January?"
"Show me all transactions over $100"
"Which category do I spend the most money on?"
"What's my current checking account balance?"
"How much did I save this month?"
"List all my investment transactions"
"What are my monthly recurring expenses?"
"Show me my largest expenses"
"How much did I spend on utilities?"
```

### 4. SEMANTIC SEARCH (Unstructured Data)
Search through budget analysis and financial planning:

```
"budget recommendations and financial advice"
"investment strategy and portfolio diversification"
"emergency fund and savings goals"
"debt reduction and payment strategies"
"retirement planning and 401k contributions"
"expense tracking and spending patterns"
"financial goals and progress tracking"
"tax planning and preparation"
"insurance coverage and risk management"
"income optimization and side hustles"
```

### 5. AI DATA ANALYST QUERIES
Ask complex financial analysis questions:

```
"Analyze my spending patterns and identify areas for improvement"
"What insights can you provide about my investment portfolio performance?"
"Evaluate my budget allocation and suggest optimizations"
"Assess my financial health and progress toward goals"
"Identify trends in my income and expense patterns"
"What are the biggest risks in my current financial situation?"
"Provide recommendations for better money management"
"Analyze my investment diversification and risk exposure"
"What opportunities exist to increase my savings rate?"
"Compare my spending to recommended budget percentages"
```

### 6. EXPECTED RESULTS
- **CSV Upload**: Should create transaction table with 15 financial records
- **JSON Upload**: Should store investment portfolio with stock holdings
- **Text Upload**: Should create searchable budget analysis chunks
- **SQL Queries**: Should return spending analytics and financial summaries
- **Natural Language**: Should answer personal finance questions with data
- **Semantic Search**: Should find relevant budget and investment information
- **AI Analysis**: Should provide financial insights and recommendations

### 7. CLIENT/USER IDs FOR TESTING
```
client_id = "client-personal-003"
user_id = "user-individual-003"
```

### 8. SAMPLE FINANCIAL METRICS
After uploading, you can analyze:
- **Monthly Income**: $6,425 (salary + freelance + dividends)
- **Total Expenses**: $3,680 (fixed + variable costs)
- **Savings Rate**: 31.1% ($2,000 monthly savings)
- **Investment Portfolio**: $45,750 total value with 9.71% return
- **Budget Categories**: Housing (18.7%), Food (6.2%), Transportation (3.9%)

### 9. KEY ANALYSIS AREAS
- **Cash Flow**: Track income vs expenses over time
- **Spending Categories**: Identify highest expense areas
- **Investment Performance**: Monitor portfolio gains/losses
- **Budget Adherence**: Compare actual vs planned spending
- **Financial Goals**: Track progress on savings and debt reduction

Use these IDs consistently to maintain financial data privacy and security.