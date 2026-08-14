<div align="center">

<img src="logo.svg" alt="VibeAR Logo" width="120" />

# VibeAR — Arabic Sentiment Analysis 

**A lightweight, production-ready sentiment analysis service for Arabic text, built with FastAPI and scikit-learn.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6.1-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-Validation-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Uvicorn](https://img.shields.io/badge/Server-Uvicorn-2E7D32?logo=gunicorn&logoColor=white)](https://www.uvicorn.org/)

</div>

---

## 🔗 Live Demo

> ⚠️ **Security note:** the key below is a **demo key** shared for evaluation only. If this repository is public, rotate it immediately (set a new `SECRET_KEY_TOKEN` in your Hugging Face Space secrets) — never rely on a key that has appeared in a public README for anything beyond a quick demo.

```
Demo X-API-Key: c0c2d9d05029aed5d5174ff5ff8e6d88
```

---


## What is VibeAR?

VibeAR is a REST API that classifies Arabic text (tweets, reviews, feedback...) as **Positive** or **Negative** in real time. It ships with a **default pre-trained model** ready to use out of the box, and also lets you **train your own model from scratch** on your own data through a single endpoint — no need to touch the code.

- **Default model** — a `TfidfVectorizer` + `LogisticRegression` pipeline, pre-trained on ~58,000 labeled Arabic tweets, ready to use immediately.
- **Custom training** — send your own `texts` + `labels` to `/train` and get a freshly trained model, without redeploying the app.
- **Switch back anytime** — `/use-default-model` restores the original pre-trained model without retraining, in case your custom model doesn't work out.

---

## Features

| Feature | Detail |
|---|---|
| 🚀 **Async FastAPI backend** | Production-grade, non-blocking request handling via Uvicorn |
| 🧠 **Pre-trained default model** | TF-IDF + Logistic Regression, trained on ~58K Arabic tweets |
| 🔁 **Train your own model** | `/train` retrains in a background thread — the API stays responsive |
| ↩️ **Reset to default** | `/use-default-model` restores the original model instantly |
| 🔐 **API key authentication** | Every endpoint requires `X-API-Key` in the request header |
| 📊 **Live training status** | `/status` reports training progress and a full evaluation report |
| 🗂️ **Single & batch prediction** | Predict one sentence or a whole list in one request |
| 🌍 **CORS enabled** | Ready for cross-origin frontends out of the box |

---

## Model Details

The default model is a scikit-learn `Pipeline` combining:

```
TfidfVectorizer(min_df=2, max_df=0.9, ngram_range=(1, 2))
        ↓
LogisticRegression()
```

**Training data:** ~58,000 Arabic tweets, balanced between Positive and Negative classes.

**Evaluation (held-out test split):**

| Metric | Negative | Positive |
|---|---|---|
| Precision | 0.77 | 0.80 |
| Recall | 0.81 | 0.77 |
| F1-score | 0.79 | 0.78 |

**Overall accuracy:** **~78.7%**

See [`notebook/text_classification.ipynb`](./notebook/text_classification.ipynb) for the exploratory experiments (including a character-level TF-IDF + LinearSVC variant) that led to this configuration.

---

## Project Structure

```
.
├── main.py                          # FastAPI app — routes, auth, CORS
├── requirements.txt                 # Pinned dependencies
├── .env.example                     # Environment variable template
├── notebook/
│   └── text_classification.ipynb    # Exploratory training notebook
└── src/
    ├── assets/
    │   └── storage/
    │       ├── model_pickle.joblib          # Currently active model (not tracked by Git)
    │       ├── model_status.json            # Active model status/report
    │       ├── default_model_pickle.joblib  # Original pre-trained model (never overwritten)
    │       └── default_model_status.json    # Default model status/report
    ├── controlers/
    │   └── NLPTrainer.py            # Core training/prediction logic
    ├── helpers/
    │   └── config.py                # Env loading, storage path setup
    └── models/
        ├── request.py               # Pydantic request schemas
        └── response.py              # Pydantic response schemas
```

---

## Requirements

- Python 3.12
- See `requirements.txt` for pinned versions — key packages:
  - `fastapi==0.139.0`
  - `uvicorn==0.49.0`
  - `scikit-learn==1.6.1`
  - `python-dotenv==1.2.2`
  - `python-multipart==0.0.32`

---

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
APP_NAME="VibeAR"
VERSION="1.0"
SECRET_KEY_TOKEN="your-strong-secret-key"
```

### 5. Add the default model

Place the pre-trained model files at:

```
src/assets/storage/default_model_pickle.joblib
src/assets/storage/default_model_status.json
```

> If these files are missing, the API still runs — it'll just start with no active model until you call `/train`.

---

## Running the Service

```bash
uvicorn main:app --reload
```

Available at: `http://127.0.0.1:8000`
Swagger UI: `http://127.0.0.1:8000/docs`

---

## API Reference

### `GET /`
Health check. Requires `X-API-Key` header.

**Response**
```json
{ "App_Name": "VibeAR", "Version": "1.0" }
```

---

### `GET /status`
Returns the current model status, class list, and evaluation report.

**Response**
```json
{
  "status": "Model Ready",
  "timestamp": "2026-08-14T00:55:55.356349",
  "classes": ["neg", "pos"],
  "evaluation": {
    "neg": { "precision": 0.77, "recall": 0.81, "f1-score": 0.79, "support": 7261 },
    "pos": { "precision": 0.80, "recall": 0.77, "f1-score": 0.78, "support": 7427 },
    "accuracy": 0.787
  }
}
```

---

### `POST /train`
Trains a new model on your own data. Training runs in a background thread — the response returns immediately with `"status": "Training"`. Poll `/status` to know when it's done.

**Body**
```json
{
  "texts": ["جملة أولى", "جملة تانية", "..."],
  "labels": ["pos", "neg", "..."]
}
```

---

### `POST /use-default-model`
Switches the active model back to the original pre-trained default, without retraining.

**Response** — same shape as `/status`.

---

### `POST /predict`
Predicts the sentiment of a single sentence.

**Body**
```json
{ "text": "الخدمة كانت ممتازة جدا" }
```

**Response**
```json
{
  "text": "الخدمة كانت ممتازة جدا",
  "predictions": { "neg": 0.13, "pos": 0.87 }
}
```

---

### `POST /predict-batch`
Predicts the sentiment of a list of sentences in one request.

**Body**
```json
{ "texts": ["جملة أولى", "جملة تانية"] }
```

**Response**
```json
{
  "predictions": [
    { "text": "جملة أولى", "predictions": { "neg": 0.2, "pos": 0.8 } },
    { "text": "جملة تانية", "predictions": { "neg": 0.9, "pos": 0.1 } }
  ]
}
```

**Error responses (all endpoints)**

| Status | Reason |
|---|---|
| `403` | Missing or invalid `X-API-Key` |
| `503` | No trained model found, or an error occurred during training/prediction |

---

## Security Notes

- Every endpoint (except none — all are protected) requires a valid `X-API-Key` header.
- Never commit your `.env` file — it is excluded by `.gitignore`.
- CORS is currently open (`allow_origins=["*"]`). Restrict this in production.

---

<div align="center">
<sub>VibeAR · built with FastAPI &amp; scikit-learn</sub>
</div>