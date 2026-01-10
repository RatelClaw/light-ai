# API Testing Examples with Dynamic JSON Data

This directory contains comprehensive API testing examples for the Intelligent AI Data Analyst System. The examples demonstrate the system's capabilities across different sectors and user personas using dynamic JSONB data.

## Directory Structure

```
api_testing/
├── README.md                          # This file - Testing instructions and API documentation
├── sectors/                           # Sector-specific test data and scenarios
│   ├── healthcare/                    # Healthcare sector examples
│   │   └── patient_analytics.json    # Hospital patient and clinical metrics
│   ├── finance/                       # Financial services examples
│   │   └── risk_assessment.json      # Banking risk and portfolio analysis
│   ├── retail/                        # Retail and e-commerce examples
│   │   └── customer_behavior.json    # Customer segmentation and sales analytics
│   ├── manufacturing/                 # Manufacturing and supply chain examples
│   │   └── supply_chain.json         # Production, suppliers, and logistics data
│   ├── education/                     # Educational institution examples
│   │   └── student_performance.json  # Academic performance and learning outcomes
│   ├── real_estate/                   # Real estate and property examples
│   │   └── market_analysis.json      # Property listings and market trends
│   └── technology/                    # Technology and software examples
│       └── user_analytics.json       # SaaS platform metrics and user behavior
└── personas/                          # User persona definitions and test data
    ├── data_analyst.json             # Technical analyst persona with statistical focus
    ├── business_executive.json       # Executive persona with strategic focus
    ├── researcher.json               # Academic researcher persona with rigorous methods
    ├── operations_manager.json       # Operations persona with process optimization
    └── marketing_specialist.json     # Marketing persona with campaign analytics
```

## API Endpoints for Testing

### 1. Data Upload Endpoints (Sub-Layer 1)

#### Upload JSON Data
**Endpoint:** `POST /api/v1/upload/json`
**Purpose:** Upload sector-specific JSON data for analysis

**Request Body:**
```json
{
  "client_id": "your-client-uuid",
  "user_id": "your-user-uuid", 
  "json_data": {}, // Use data from sectors/ directory
  "resource_name": "healthcare_analytics", // Descriptive name
  "flatten": false // Keep nested structure for complex analysis
}
```

**Test with Swagger:**
1. Go to `/docs` endpoint in your browser
2. Find `POST /api/v1/upload/json` endpoint
3. Click "Try it out"
4. Copy JSON data from any `sectors/` file into `json_data` field
5. Generate UUIDs for `client_id` and `user_id` using `/api/v1/demo/ids`
6. Execute and note the `resource_id` returned

### 2. AI Analysis Endpoints (Sub-Layer 2)

#### Natural Language Analysis
**Endpoint:** `POST /api/v2/analysis`
**Purpose:** Perform AI-powered analysis using natural language queries

**Request Body:**
```json
{
  "client_id": "your-client-uuid",
  "user_id": "your-user-uuid",
  "query": "What are the key factors driving patient readmission rates?",
  "desired_fields": {
    "readmission_rate": "30-day readmission percentage",
    "risk_factors": "Primary and secondary diagnoses"
  },
  "include_visualizations": true,
  "access_level": "user"
}
```

#### Streaming Analysis
**Endpoint:** `POST /api/v2/analysis/streaming`
**Purpose:** Stream large analysis results in real-time

**Request Body:**
```json
{
  "client_id": "your-client-uuid", 
  "user_id": "your-user-uuid",
  "query": "Analyze all customer segments and their profitability patterns",
  "chunk_size": 100,
  "include_metadata": true
}
```

#### Continue Conversation
**Endpoint:** `POST /api/v2/analysis/continue`
**Purpose:** Follow-up questions maintaining conversation context

**Request Body:**
```json
{
  "client_id": "your-client-uuid",
  "user_id": "your-user-uuid", 
  "query": "What specific interventions could reduce the readmission rate?",
  "conversation_id": "conversation-uuid-from-previous-response",
  "include_visualizations": true
}
```

### 3. Legacy Analysis Endpoints (Sub-Layer 2 Integration)

#### AI Data Analyst
**Endpoint:** `POST /api/v1/analyst`
**Purpose:** Comprehensive AI analysis with cross-resource synthesis

**Request Body:**
```json
{
  "client_id": "your-client-uuid",
  "user_id": "your-user-uuid",
  "question": "Provide a comprehensive analysis of our operational efficiency compared to industry benchmarks",
  "include_visualizations": true
}
```

#### Smart SQL Query
**Endpoint:** `POST /api/v1/query/smart`
**Purpose:** Natural language to SQL conversion and execution

**Query Parameters:**
- `client_id`: Your client UUID
- `user_id`: Your user UUID  
- `question`: "What is the average length of stay for emergency admissions?"
- `output_format`: "json"

### 4. WebSocket Real-time Analysis

#### WebSocket Connection
**Endpoint:** `ws://localhost:8001/api/v2/ws/{client_id}/{user_id}`
**Purpose:** Real-time interactive analysis

**Message Format:**
```json
{
  "type": "analysis_request",
  "data": {
    "query": "Monitor real-time changes in customer behavior patterns",
    "conversation_id": "optional-conversation-uuid",
    "include_visualizations": true
  }
}
```

## Testing Scenarios by Sector

### Healthcare Sector Testing
**Data File:** `sectors/healthcare/patient_analytics.json`
**Test Queries:**
1. "What factors contribute most to patient readmission rates?"
2. "Compare treatment costs across different diagnosis categories"
3. "Identify opportunities to improve patient satisfaction scores"
4. "Analyze the relationship between length of stay and patient outcomes"

### Finance Sector Testing  
**Data File:** `sectors/finance/risk_assessment.json`
**Test Queries:**
1. "Calculate the portfolio's risk-adjusted returns and VaR metrics"
2. "Identify the highest risk loans and recommend mitigation strategies"
3. "Analyze stress test scenarios and their impact on capital ratios"
4. "Compare default probabilities across different industry sectors"

### Retail Sector Testing
**Data File:** `sectors/retail/customer_behavior.json`
**Test Queries:**
1. "Which customer segments provide the highest lifetime value?"
2. "Analyze the effectiveness of different marketing campaigns"
3. "Identify products with the best profit margins and turnover rates"
4. "Recommend inventory optimization strategies based on sales patterns"

### Manufacturing Sector Testing
**Data File:** `sectors/manufacturing/supply_chain.json`
**Test Queries:**
1. "Identify bottlenecks in the supply chain and their cost impact"
2. "Analyze supplier performance and risk assessment"
3. "Optimize inventory levels across raw materials and finished goods"
4. "Evaluate predictive maintenance opportunities and ROI"

### Education Sector Testing
**Data File:** `sectors/education/student_performance.json`
**Test Queries:**
1. "What factors most strongly predict student success?"
2. "Analyze resource utilization and its impact on learning outcomes"
3. "Identify at-risk students and recommend intervention strategies"
4. "Compare course effectiveness across different teaching methods"

### Real Estate Sector Testing
**Data File:** `sectors/real_estate/market_analysis.json`
**Test Queries:**
1. "Analyze market trends and price appreciation forecasts"
2. "Identify the most attractive investment opportunities"
3. "Compare neighborhood performance and risk factors"
4. "Evaluate rental yield potential across different property types"

### Technology Sector Testing
**Data File:** `sectors/technology/user_analytics.json`
**Test Queries:**
1. "Analyze user engagement patterns and churn prediction"
2. "Identify features driving the highest user satisfaction"
3. "Optimize pricing strategies based on user behavior"
4. "Evaluate the effectiveness of different acquisition channels"

## Testing Scenarios by Persona

### Data Analyst Persona Testing
**Persona File:** `personas/data_analyst.json`
**Expected Behavior:**
- Detailed statistical analysis with p-values and confidence intervals
- Advanced visualizations with statistical overlays
- Comprehensive methodology explanations
- Code snippets for reproducibility
- Technical terminology and rigorous analysis

**Sample Test Flow:**
1. Upload healthcare data
2. Query: "Perform a comprehensive statistical analysis of patient readmission patterns"
3. Expect: Correlation matrices, hypothesis tests, predictive modeling recommendations

### Business Executive Persona Testing
**Persona File:** `personas/business_executive.json`
**Expected Behavior:**
- High-level strategic insights
- Clear KPI focus and ROI analysis
- Simple, impactful visualizations
- Actionable recommendations with timelines
- Business-focused language

**Sample Test Flow:**
1. Upload retail data
2. Query: "What are our key performance drivers for quarterly revenue growth?"
3. Expect: Executive summary with prioritized action items and financial impact

### Academic Researcher Persona Testing
**Persona File:** `personas/researcher.json`
**Expected Behavior:**
- Publication-quality analysis
- Rigorous statistical methods
- Detailed methodology documentation
- Peer-review ready outputs
- Research integrity considerations

**Sample Test Flow:**
1. Upload education data
2. Query: "Conduct a power analysis for comparing student performance across teaching methods"
3. Expect: Sample size calculations, effect sizes, statistical power curves

### Operations Manager Persona Testing
**Persona File:** `personas/operations_manager.json`
**Expected Behavior:**
- Process optimization focus
- Operational efficiency metrics
- Real-time monitoring capabilities
- Cost-benefit analysis
- Implementation-focused recommendations

**Sample Test Flow:**
1. Upload manufacturing data
2. Query: "Identify bottlenecks in our production process and calculate improvement potential"
3. Expect: Process analysis with throughput calculations and implementation timelines

### Marketing Specialist Persona Testing
**Persona File:** `personas/marketing_specialist.json`
**Expected Behavior:**
- Customer-centric analysis
- Campaign performance metrics
- Segmentation and targeting insights
- ROI and attribution analysis
- Marketing-specific visualizations

**Sample Test Flow:**
1. Upload retail data
2. Query: "Analyze customer lifetime value across acquisition channels"
3. Expect: Channel performance analysis with budget allocation recommendations

## Step-by-Step Testing Instructions

### Prerequisites
1. Start the API server: `python light_ai/fastapi_server.py --port 8000`
2. Start the v2 API server: `python light_ai/api_v2.py --port 8001`
3. Open Swagger UI: `http://localhost:8000/docs` and `http://localhost:8001/api/v2/docs`

### Basic Testing Workflow

#### Step 1: Generate Test IDs
1. Go to `GET /api/v1/demo/ids` in Swagger
2. Execute to get `client_id` and `user_id`
3. Save these UUIDs for all subsequent requests

#### Step 2: Upload Sector Data
1. Choose a sector JSON file (e.g., `healthcare/patient_analytics.json`)
2. Go to `POST /api/v1/upload/json` in Swagger
3. Fill in the request:
   ```json
   {
     "client_id": "your-generated-uuid",
     "user_id": "your-generated-uuid",
     "json_data": {/* paste entire JSON from sector file */},
     "resource_name": "healthcare_analytics_q1_2024",
     "flatten": false
   }
   ```
4. Execute and note the `resource_id` in response

#### Step 3: Test AI Analysis (v2 API)
1. Go to `http://localhost:8001/api/v2/docs`
2. Use `POST /api/v2/analysis` endpoint
3. Fill in analysis request:
   ```json
   {
     "client_id": "your-uuid",
     "user_id": "your-uuid", 
     "query": "What are the key factors driving patient readmission rates in our hospital?",
     "desired_fields": {
       "readmission_rate": "30-day readmission percentage",
       "primary_factors": "Main contributing factors"
     },
     "include_visualizations": true,
     "access_level": "user"
   }
   ```
4. Execute and analyze the AI response

#### Step 4: Test Conversation Continuity
1. Use the `conversation_id` from Step 3 response
2. Go to `POST /api/v2/analysis/continue`
3. Ask follow-up question:
   ```json
   {
     "client_id": "your-uuid",
     "user_id": "your-uuid",
     "query": "What specific interventions could reduce these readmission rates?",
     "conversation_id": "conversation-uuid-from-step-3",
     "include_visualizations": true
   }
   ```

#### Step 5: Test Legacy Integration
1. Go back to `http://localhost:8000/docs`
2. Use `POST /api/v1/analyst` endpoint
3. Test comprehensive analysis:
   ```json
   {
     "client_id": "your-uuid", 
     "user_id": "your-uuid",
     "question": "Provide a comprehensive analysis of our hospital's operational efficiency and patient outcomes",
     "include_visualizations": true
   }
   ```

### Advanced Testing Scenarios

#### Cross-Sector Analysis
1. Upload data from multiple sectors (healthcare + finance)
2. Query: "Compare risk management approaches between healthcare and financial services"
3. Expect: Cross-domain insights and best practice recommendations

#### Persona Adaptation Testing
1. Upload the same data multiple times with different user personas
2. Ask the same question with different persona contexts
3. Compare how responses adapt to different expertise levels and focus areas

#### Streaming Analysis Testing
1. Upload large dataset (manufacturing supply chain)
2. Use `POST /api/v2/analysis/streaming` endpoint
3. Monitor real-time streaming response chunks
4. Verify complete data delivery and metadata accuracy

#### WebSocket Real-time Testing
1. Connect to WebSocket endpoint: `ws://localhost:8001/api/v2/ws/{client_id}/{user_id}`
2. Send analysis requests via WebSocket messages
3. Monitor real-time responses and connection health
4. Test ping/pong for connection maintenance

## Expected Outcomes and Validation

### AI Intelligence Validation
- **Natural Language Understanding**: System correctly interprets domain-specific queries
- **Context Awareness**: Responses adapt to sector terminology and business context
- **Cross-Resource Synthesis**: Analysis combines data from multiple sources intelligently
- **Persona Adaptation**: Response style and depth match user expertise level

### Technical Validation
- **Data Isolation**: Each user only accesses their own data
- **ACID Compliance**: All operations maintain data consistency
- **Performance**: Response times under 30 seconds for complex analysis
- **Scalability**: System handles concurrent users without degradation

### Business Value Validation
- **Actionable Insights**: Recommendations are specific and implementable
- **ROI Quantification**: Financial impact is clearly calculated
- **Risk Assessment**: Potential risks and mitigation strategies identified
- **Strategic Alignment**: Analysis supports business objectives

## Troubleshooting Common Issues

### API Connection Issues
- Verify both servers are running on correct ports
- Check firewall settings and network connectivity
- Ensure UUIDs are properly formatted (36 characters with hyphens)

### Data Upload Issues
- Validate JSON syntax before uploading
- Check file size limits (10MB max)
- Ensure proper client_id and user_id format

### Analysis Quality Issues
- Use sector-appropriate terminology in queries
- Provide sufficient context for complex analysis
- Specify desired output format and detail level

### Performance Issues
- Use streaming endpoints for large datasets
- Enable chunking for complex multi-step analysis
- Monitor system resources during testing

This comprehensive testing framework validates the complete integration of Sub-Layer 1 (data ingestion) with the new Sub-Layer 2 (AI analysis) while maintaining backward compatibility with existing APIs.