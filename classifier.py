# 🤖 classifier.py

import re
import joblib
import streamlit as st


# ---------------------------------------------------
# LOAD MODEL + VECTORIZER
# ---------------------------------------------------
@st.cache_resource
def load_model_and_vectorizer(
    model_path="models/spam_model.pkl",
    vectorizer_path="models/vectorizer.pkl"
):

    try:

        model = joblib.load(model_path)

        vectorizer = joblib.load(vectorizer_path)

        return model, vectorizer

    except Exception as e:

        raise RuntimeError(
            f"Error loading model/vectorizer: {e}"
        )


# ---------------------------------------------------
# CLEAN TEXT
# ---------------------------------------------------
def clean(text):

    text = text.lower()

    text = re.sub(
        r"http\S+|www\S+",
        "",
        text
    )

    text = re.sub(
        r"[^a-z\s]",
        "",
        text
    )

    return text.strip()


# ---------------------------------------------------
# CLASSIFY MESSAGE
# ---------------------------------------------------
def classify_message(
    message,
    model=None,
    vectorizer=None
):

    if not message:

        return "No content", 0.0

    if not model or not vectorizer:

        raise ValueError(
            "Model and vectorizer required."
        )

    cleaned_text = clean(message)

    vector = vectorizer.transform(
        [cleaned_text]
    )

    pred = model.predict(vector)[0]

    prob = model.predict_proba(vector)[0]

    label = (
        "🚫 SPAM"
        if pred == 1
        else "✅ HAM"
    )

    confidence = round(
        max(prob) * 100,
        2
    )

    return label, confidence
