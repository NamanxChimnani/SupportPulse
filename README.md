
# 🚦 SupportPulse — Customer Support Intelligence

A fast, portfolio-ready **Data Engineering + Data Science** project using only:
**Python, pandas, scikit-learn, SQLite, and Streamlit**.

## Business problem
A SaaS company receives thousands of support tickets. Leadership wants to know:
1. Which tickets are likely to breach the SLA?
2. Which customers are at risk?
3. Which products/categories create the most operational pain?
4. How should the support team prioritize work?

## End-to-end pipeline

Raw CSV
  ↓
Python ingestion + validation
  ↓
SQLite analytical database
  ↓
Feature engineering
  ↓
ML model: SLA-breach prediction
  ↓
Customer risk scoring
  ↓
Streamlit decision dashboard

## Why this is better for a fresher portfolio
It is relatable to almost every company with software customers, while demonstrating:
- Python / pandas
- SQL
- ETL
- database fundamentals
- data cleaning
- feature engineering
- classification
- model evaluation
- business metrics
- dashboarding
- reproducibility

## Run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt

python src/generate_data.py
python src/pipeline.py
python src/train_model.py

streamlit run dashboard/app.py
```

No DuckDB, Spark, Kafka or cloud account required.

## Resume bullet

> Built **SupportPulse**, an end-to-end customer-support intelligence system using Python, SQL, pandas and scikit-learn; engineered ticket/customer features, trained an SLA-breach classifier, created customer-risk scores and deployed an interactive Streamlit prioritization dashboard.

## Production upgrade path

SQLite → PostgreSQL  
CSV → API/event ingestion  
Python scripts → Airflow  
pandas transformations → dbt  
local model → MLflow/model registry  
Streamlit → cloud app
