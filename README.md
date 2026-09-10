# 🚦 SupportPulse — SaaS Support Intelligence & SLA Risk Platform

> An end-to-end customer support analytics platform that combines data engineering, SQL analytics, machine learning, and an interactive operational dashboard to identify SLA risk and prioritize support workload.

---

## 📌 Overview

Support teams handle thousands of customer tickets while trying to meet service-level agreements (SLAs).

SupportPulse transforms raw support-ticket data into actionable operational intelligence:

- Predict tickets at risk of SLA breach
- Identify high-risk customers
- Analyze product and priority-level support problems
- Recommend which tickets should be escalated or prioritized
- Explore customer-level support history
- Compare machine-learning models
- Provide an interactive dashboard for operational decision-making

The project uses synthetic SaaS support data designed to simulate a realistic support operation.

---

## 🎯 Business Problem

A SaaS company receives thousands of support tickets. Support leadership needs answers to questions such as:

1. Which tickets are most likely to breach their SLA?
2. Which customers are experiencing elevated support risk?
3. Which products generate the highest breach rates?
4. Which ticket priorities carry the greatest risk?
5. How should the support team allocate its workload?

SupportPulse addresses these questions through a complete data pipeline and decision-support dashboard.

---

## 🏗️ Architecture

```text
Raw CSV Data
     │
     ▼
Python Ingestion & Validation
     │
     ▼
SQLite Analytical Database
     │
     ▼
SQL Analytics / Data Preparation
     │
     ▼
Feature Engineering
     │
     ▼
ML Model Comparison
     │
     ▼
SLA-Breach Risk Prediction
     │
     ▼
Customer & Ticket Risk Scoring
     │
     ▼
Streamlit + Plotly Dashboard