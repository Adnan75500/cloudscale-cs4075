
import os
import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

DATA_PATH = os.path.join("ml", "data.csv")
MODEL_DIR = os.path.join("ml", "model")

os.makedirs(MODEL_DIR, exist_ok=True)

df = pd.read_csv(DATA_PATH)

x_train, x_test, y_train, y_test = train_test_split(
    df["text"],
    df["category"],
    test_size=0.2,
    random_state=42,
    stratify=df["category"]
)

model = make_pipeline(
    TfidfVectorizer(ngram_range=(1, 2), lowercase=True),
    LogisticRegression(max_iter=1000)
)

model.fit(x_train, y_train)

accuracy = model.score(x_test, y_test)
print(f"Holdout accuracy: {accuracy:.4f}")

# Retrain using all available data
model.fit(df["text"], df["category"])

joblib.dump(model, os.path.join(MODEL_DIR, "model.joblib"))

print("Model saved successfully.")
