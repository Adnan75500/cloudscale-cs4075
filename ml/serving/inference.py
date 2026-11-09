
import json
import os

import joblib


def model_fn(model_dir):
    return joblib.load(os.path.join(model_dir, "model.joblib"))


def input_fn(request_body, content_type="application/json"):
    if content_type != "application/json":
        raise ValueError("Unsupported content type: " + content_type)

    payload = json.loads(request_body)
    text = payload.get("text", "")

    if not isinstance(text, str) or not text.strip():
        raise ValueError("A non-empty text field is required")

    return [text[:500]]


def predict_fn(data, model):
    probabilities = model.predict_proba(data)[0]
    best = int(probabilities.argmax())

    return {
        "category": str(model.classes_[best]),
        "confidence": round(float(probabilities[best]), 3)
    }


def output_fn(prediction, accept="application/json"):
    return json.dumps(prediction), "application/json"
