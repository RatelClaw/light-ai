# USER 02 - HR & PROJECT MANAGEMENT DATA
## Sample Data Overview
This folder contains HR and project management data including employee information, project reports, and meeting documentation.

### Files:
- `employee_data.xlsx` - Employee records with performance and salary data
- `project_reports.json` - Project status, budgets, and team information
- `meeting_notes.txt` - Weekly team meeting notes and action items

## API Testing Instructions

### 1. FILE UPLOAD (Sub-Layer 1)
Upload each file to test different data types:

```python
# Upload Excel file
api.upload_file(client_id, user_id, "employee_data.xlsx", "Employee Database")

# Upload JSON file
api.upload_json(client_id, user_id, project_data, "Project Reports")

# Upload text file
api.upload_file(client_id, user_id, "meeting_notes.txt", "Meeting Minutes")
```

### 2. SQL QUERIES (Sub-Layer 2)
Test HR and project analytics:

```sql
-- Employee performance analysis
SELECT department, AVG(salary) as avg_salary, AVG(performance_score) as avg_performance
FROM structured_data.resource_[RESOURCE_ID]
GROUP BY department
ORDER BY avg_performance DESC;

-- Salary distribution by position
SELECT position, MIN(salary) as min_salary, MAX(salary) as max_salary, AVG(salary) as avg_salary
FROM structured_data.resource_[RESOURCE_ID]
GROUP BY position;

-- High performers identification
SELECT name, department, position, salary, performance_score
FROM structured_data.resource_[RESOURCE_ID]
WHERE performance_score >= 4.5
ORDER BY performance_score DESC;

-- Department headcount and costs
SELECT department, COUNT(*) as headcount, SUM(salary) as total_cost
FROM structured_data.resource_[RESOURCE_ID]
GROUP BY department;

-- Recent hires analysis
SELECT name, department, hire_date, salary
FROM structured_data.resource_[RESOURCE_ID]
WHERE hire_date >= '2023-01-01'
ORDER BY hire_date DESC;
```

### 3. NATURAL LANGUAGE QUERIES
Test HR and project management questions:

```
"Who are the highest performing employees?"
"What's the average salary by department?"
"Show me all employees hired in 2023"
"Which department has the most employees?"
"Who are the engineering team members?"
"What's the salary range for developers?"
"List employees with performance scores above 4.5"
"How much does the company spend on salaries by department?"
"Who reports to manager MGR001?"
"What positions exist in the marketing department?"
```

### 4. SEMANTIC SEARCH (Unstructured Data)
Search through project reports and meeting notes:

```
"project budget and spending analysis"
"team performance and productivity metrics"
"upcoming milestones and deadlines"
"resource allocation and hiring needs"
"technical infrastructure and tools"
"client feedback and satisfaction"
"action items and follow-ups"
"meeting decisions and outcomes"
"project risks and challenges"
"team morale and development"
```

### 5. AI DATA ANALYST QUERIES
Ask complex HR and project analytics questions:

```
"Analyze employee performance across departments and identify patterns"
"What insights can you provide about salary equity and compensation?"
"Evaluate project performance and budget utilization"
"Identify potential retention risks based on performance and tenure"
"Analyze team productivity and resource allocation efficiency"
"What are the key factors for project success based on the data?"
"Provide recommendations for talent development and promotion"
"Assess departmental performance and growth opportunities"
"What hiring patterns and needs can you identify?"
"Analyze the relationship between performance scores and compensation"
```

### 6. EXPECTED RESULTS
- **Excel Upload**: Should create structured table with 10 employee records
- **JSON Upload**: Should store project data with nested team information
- **Text Upload**: Should create searchable meeting notes chunks
- **SQL Queries**: Should return HR metrics and employee analytics
- **Natural Language**: Should answer HR-related questions with data
- **Semantic Search**: Should find relevant project and meeting information
- **AI Analysis**: Should provide HR insights and organizational recommendations

### 7. CLIENT/USER IDs FOR TESTING
```
client_id = "client-techcorp-002"
user_id = "user-hr-manager-002"
```

### 8. SAMPLE RESOURCE ANALYSIS
After uploading, you can analyze:
- **Employee Performance**: 10 employees across 5 departments
- **Salary Analysis**: Range from $58K to $95K with performance correlation
- **Project Portfolio**: 3 projects with different statuses and budgets
- **Team Dynamics**: Meeting notes reveal collaboration patterns and challenges

Use these IDs consistently to maintain proper data segregation and access control.