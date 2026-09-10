from pathlib import Path
import sqlite3
import json
import pickle

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

from sklearn.metrics import (
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)


ROOT = Path(__file__).resolve().parents[1]

# ============================================================
# LOAD
# ============================================================

conn = sqlite3.connect(ROOT / "supportpulse.db")

df = pd.read_sql(
    "SELECT * FROM ticket_analytics",
    conn
)

conn.close()

features = [
    "product",
    "channel",
    "priority",
    "customer_plan",
    "previous_tickets_30d",
    "message_length",
    "agent_experience_months",
    "monthly_spend",
    "months_active"
]

X = df[features]
y = df["sla_breach"]

categorical = [
    "product",
    "channel",
    "priority",
    "customer_plan"
]

numeric = [
    "previous_tickets_30d",
    "message_length",
    "agent_experience_months",
    "monthly_spend",
    "months_active"
]

# Dense output lets us compare tree models too
preprocessor = ColumnTransformer([
    (
        "categorical",
        OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False
        ),
        categorical
    ),
    (
        "numeric",
        StandardScaler(),
        numeric
    )
])

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# ============================================================
# MODELS
# ============================================================

models = {
    "Logistic Regression": LogisticRegression(
        max_iter=1000,
        class_weight="balanced"
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=250,
        max_depth=10,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    ),

    "Gradient Boosting": GradientBoostingClassifier(
        n_estimators=150,
        learning_rate=0.05,
        max_depth=3,
        random_state=42
    )
}

results = []
trained_models = {}

# ============================================================
# TRAIN + COMPARE
# ============================================================

for name, classifier in models.items():

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", classifier)
    ])

    pipeline.fit(X_train, y_train)

    probabilities = pipeline.predict_proba(X_test)[:, 1]

    # Use 0.50 only for model comparison
    predictions = (probabilities >= 0.50).astype(int)

    results.append({
        "model": name,
        "roc_auc": roc_auc_score(y_test, probabilities),
        "precision": precision_score(
            y_test,
            predictions,
            zero_division=0
        ),
        "recall": recall_score(
            y_test,
            predictions,
            zero_division=0
        ),
        "f1": f1_score(
            y_test,
            predictions,
            zero_division=0
        )
    })

    trained_models[name] = pipeline


comparison = pd.DataFrame(results)

comparison = comparison.sort_values(
    "roc_auc",
    ascending=False
)

# ============================================================
# SELECT BEST MODEL
# ============================================================

best_name = comparison.iloc[0]["model"]

best_model = trained_models[best_name]

# Save comparison
comparison.to_csv(
    ROOT / "model_comparison.csv",
    index=False
)

# Save selected model
(ROOT / "model.pkl").write_bytes(
    pickle.dumps(best_model)
)

# ============================================================
# FINAL MODEL METRICS
# ============================================================

test_probabilities = best_model.predict_proba(X_test)[:, 1]

test_predictions = (
    test_probabilities >= 0.50
).astype(int)

final_metrics = {
    "selected_model": best_name,

    "roc_auc": float(
        roc_auc_score(
            y_test,
            test_probabilities
        )
    ),

    "precision": float(
        precision_score(
            y_test,
            test_predictions,
            zero_division=0
        )
    ),

    "recall": float(
        recall_score(
            y_test,
            test_predictions,
            zero_division=0
        )
    ),

    "f1": float(
        f1_score(
            y_test,
            test_predictions,
            zero_division=0
        )
    ),

    "confusion_matrix":
        confusion_matrix(
            y_test,
            test_predictions
        ).tolist()
}

(ROOT / "metrics.json").write_text(
    json.dumps(
        final_metrics,
        indent=2
    )
)

# ============================================================
# SCORE ALL TICKETS
# ============================================================

df["breach_probability"] = (
    best_model.predict_proba(X)[:, 1]
)

# ============================================================
# BUSINESS PRIORITY
# ============================================================

priority_weight = df["priority"].map({
    "Low": 0,
    "Medium": 10,
    "High": 20,
    "Urgent": 30
})

customer_weight = df["customer_plan"].map({
    "Free": 0,
    "Starter": 3,
    "Business": 7,
    "Enterprise": 12
})

df["priority_score"] = (
    df["breach_probability"] * 100
    + priority_weight
    + customer_weight
)

# ============================================================
# ACTION
# ============================================================

def recommend_action(row):

    p = row["breach_probability"]
    priority = row["priority"]

    if p >= 0.75 and priority in ["Urgent", "High"]:
        return "ESCALATE"

    if p >= 0.55:
        return "PRIORITIZE"

    if p >= 0.35:
        return "MONITOR"

    return "NORMAL QUEUE"


df["recommended_action"] = df.apply(
    recommend_action,
    axis=1
)

# ============================================================
# EXPLANATION
# ============================================================

def explain_ticket(row):

    reasons = []

    if row["priority"] == "Urgent":
        reasons.append("Urgent priority")

    elif row["priority"] == "High":
        reasons.append("High priority")

    if row["previous_tickets_30d"] >= 4:
        reasons.append("Frequent recent contact")

    if row["message_length"] >= 600:
        reasons.append("Long customer message")

    if row["product"] == "Payments API":
        reasons.append("Payments product")

    if row["channel"] == "Phone":
        reasons.append("Phone support")

    if row["agent_experience_months"] <= 12:
        reasons.append("Less-experienced agent")

    if row["customer_plan"] == "Enterprise":
        reasons.append("Enterprise customer")

    if not reasons:
        reasons.append("No major risk drivers")

    return " • ".join(reasons[:4])


df["risk_reasons"] = df.apply(
    explain_ticket,
    axis=1
)

# ============================================================
# SAVE SCORES
# ============================================================

columns = [
    "ticket_id",
    "customer_id",
    "created_date",
    "product",
    "channel",
    "priority",
    "customer_plan",
    "previous_tickets_30d",
    "message_length",
    "agent_experience_months",
    "monthly_spend",
    "months_active",
    "sla_breach",
    "breach_probability",
    "priority_score",
    "recommended_action",
    "risk_reasons"
]

df[columns].to_csv(
    ROOT / "data" / "scored_tickets.csv",
    index=False
)

# ============================================================
# OUTPUT
# ============================================================

print()
print("=" * 60)
print("SUPPORTPULSE — MODEL COMPARISON")
print("=" * 60)

print()

print(
    comparison[
        ["model", "roc_auc", "precision", "recall", "f1"]
    ].to_string(
        index=False,
        formatters={
            "roc_auc": "{:.3f}".format,
            "precision": "{:.3f}".format,
            "recall": "{:.3f}".format,
            "f1": "{:.3f}".format
        }
    )
)

print()
print(f"SELECTED MODEL: {best_name}")

print()
print("Final metrics:")
print(f"ROC-AUC : {final_metrics['roc_auc']:.3f}")
print(f"Precision: {final_metrics['precision']:.3f}")
print(f"Recall   : {final_metrics['recall']:.3f}")
print(f"F1       : {final_metrics['f1']:.3f}")

print()
print("Recommended actions:")

print(
    df["recommended_action"]
    .value_counts()
    .to_string()
)

print()
print("Files created:")
print("  model.pkl")
print("  metrics.json")
print("  model_comparison.csv")
print("  data/scored_tickets.csv")

print("=" * 60)