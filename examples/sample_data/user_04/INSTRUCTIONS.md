# USER 04 - RESEARCH & ACADEMIC DATA
## Sample Data Overview
This folder contains academic research data including clinical study results, experimental data, and literature review.

### Files:
- `research_data.csv` - Clinical study participant data with treatment outcomes
- `experiment_results.json` - Statistical analysis and research findings
- `literature_review.txt` - Comprehensive academic literature review

## API Testing Instructions

### 1. FILE UPLOAD (Sub-Layer 1)
Upload each file to test research data:

```python
# Upload CSV file
api.upload_file(client_id, user_id, "research_data.csv", "Clinical Study Data")

# Upload JSON file
api.upload_json(client_id, user_id, experiment_data, "Experiment Results")

# Upload text file
api.upload_file(client_id, user_id, "literature_review.txt", "Literature Review")
```

### 2. SQL QUERIES (Sub-Layer 2)
Test research data analysis:

```sql
-- Treatment group comparison
SELECT treatment_group, 
       AVG(baseline_score) as avg_baseline,
       AVG(week_12_score) as avg_final,
       AVG(week_12_score - baseline_score) as avg_improvement
FROM structured_data.resource_[RESOURCE_ID]
GROUP BY treatment_group
ORDER BY avg_improvement DESC;

-- Gender-based analysis
SELECT gender, treatment_group, 
       COUNT(*) as participants,
       AVG(week_12_score - baseline_score) as avg_improvement
FROM structured_data.resource_[RESOURCE_ID]
GROUP BY gender, treatment_group;

-- Age group analysis
SELECT 
    CASE 
        WHEN age < 30 THEN 'Under 30'
        WHEN age BETWEEN 30 AND 40 THEN '30-40'
        ELSE 'Over 40'
    END as age_group,
    treatment_group,
    AVG(week_12_score - baseline_score) as improvement
FROM structured_data.resource_[RESOURCE_ID]
GROUP BY age_group, treatment_group;

-- Completion rate analysis
SELECT treatment_group, 
       COUNT(*) as total_participants,
       SUM(CASE WHEN completion_status = 'Completed' THEN 1 ELSE 0 END) as completed,
       ROUND(100.0 * SUM(CASE WHEN completion_status = 'Completed' THEN 1 ELSE 0 END) / COUNT(*), 2) as completion_rate
FROM structured_data.resource_[RESOURCE_ID]
GROUP BY treatment_group;

-- Top performers identification
SELECT participant_id, age, gender, treatment_group, 
       baseline_score, week_12_score,
       (week_12_score - baseline_score) as improvement
FROM structured_data.resource_[RESOURCE_ID]
WHERE completion_status = 'Completed'
ORDER BY improvement DESC
LIMIT 5;
```

### 3. NATURAL LANGUAGE QUERIES
Test research and statistical questions:

```
"Which treatment group showed the best improvement?"
"What's the average age of participants in each group?"
"How many participants completed the study?"
"Show me the baseline scores by treatment group"
"Which gender responded better to Treatment A?"
"What's the completion rate for each treatment?"
"List participants with the highest improvement scores"
"Compare week 4 vs week 12 scores across groups"
"What's the age distribution of participants?"
"Show me all female participants in the control group"
```

### 4. SEMANTIC SEARCH (Unstructured Data)
Search through experiment results and literature:

```
"statistical significance and p-values"
"cognitive enhancement treatment effects"
"randomized controlled trial methodology"
"effect size and clinical significance"
"literature review findings and conclusions"
"pharmacological vs non-pharmacological interventions"
"modafinil and cognitive performance"
"transcranial stimulation research"
"study limitations and future directions"
"ethical considerations in enhancement research"
```

### 5. AI DATA ANALYST QUERIES
Ask complex research analysis questions:

```
"Analyze the effectiveness of different treatments and provide statistical insights"
"What can you conclude about the clinical significance of the results?"
"Evaluate the study design and identify potential confounding factors"
"Compare the effect sizes across different treatment modalities"
"Assess the demographic factors that influence treatment response"
"What are the implications of these findings for clinical practice?"
"Identify patterns in participant response over the 12-week period"
"Analyze the relationship between baseline scores and treatment outcomes"
"What recommendations would you make for future research studies?"
"Evaluate the statistical power and validity of the study conclusions"
```

### 6. EXPECTED RESULTS
- **CSV Upload**: Should create participant table with 15 research subjects
- **JSON Upload**: Should store experimental results with statistical analysis
- **Text Upload**: Should create searchable literature review chunks
- **SQL Queries**: Should return research analytics and treatment comparisons
- **Natural Language**: Should answer research questions with statistical data
- **Semantic Search**: Should find relevant research methodology and findings
- **AI Analysis**: Should provide research insights and statistical interpretations

### 7. CLIENT/USER IDs FOR TESTING
```
client_id = "client-research-004"
user_id = "user-researcher-004"
```

### 8. SAMPLE RESEARCH METRICS
After uploading, you can analyze:
- **Study Design**: Randomized controlled trial with 3 groups (n=15)
- **Treatment Effects**: Treatment A (+20.8 points), Treatment B (+17.0 points), Control (+3.2 points)
- **Statistical Significance**: p < 0.001 for both treatments vs control
- **Effect Sizes**: Large effect for Treatment A (1.85), moderate for Treatment B (1.42)
- **Demographics**: Balanced age (26-52) and gender distribution

### 9. KEY RESEARCH AREAS
- **Efficacy Analysis**: Compare treatment outcomes across groups
- **Statistical Testing**: Evaluate significance and effect sizes
- **Demographic Factors**: Analyze age and gender influences
- **Longitudinal Trends**: Track improvement over 12 weeks
- **Clinical Significance**: Assess real-world impact of findings

### 10. RESEARCH ETHICS NOTE
This is simulated research data for testing purposes only. In real research, ensure proper IRB approval, informed consent, and data privacy protections.

Use these IDs consistently to maintain research data integrity and access control.