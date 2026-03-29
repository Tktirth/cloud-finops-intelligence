# 🚀 Cloud FinOps Intelligence 

[![React](https://img.shields.io/badge/React-18.0-blue.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3-orange.svg)](https://scikit-learn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Real-time AI-powered multi-cloud cost anomaly detection, forecasting, and budget intelligence platform.**

Organizations operating across AWS, Azure, and Google Cloud face an escalating challenge: cloud spend grows 20-30% year-over-year, yet engineering teams lack the predictive intelligence to detect cost anomalies before they snowball. 

**Cloud FinOps Intelligence** is a state-of-the-art solution that synthesizes robust Machine Learning models (Isolation Forests, One-Class SVMs, and Deep Learning Autoencoders) to detect subtle financial discrepancies, generating accurate spend forecasts across high-dimensional architectural features. 

---

## 🔥 Features
* **Real-time Ist Data:** Seamless rendering and calculation of current IST timestamps across AWS, Azure, and GCP tracking.
* **Unified ML Ensemble Engine:** Detects both sudden spikes and gradual cost drift via a weighted voting system utilizing STL Decomposition, `sklearn` Isolation Forests, and PyTorch/Keras LSTMs.
* **Causal Attribution Graph:** Leverages SHAP values to attribute detected anomalies back to specific root causes (e.g. EC2 scaling events, S3 backup loops).
* **Live Notifications & Alerts:** Interactive notification bell mapping top priority `CRITICAL` warnings directly to user view context.
* **Quantile Predictive Forecasting:** Employs Prophet and LightGBM to yield exact budget breach probabilities with P50-P90 bounding boxes.

---

## 🏗️ Architecture

The system operates on a modernized client-server structure via a single monorepo:

### 1. `backend/` (FastAPI + Python ML)
- **Data Generator Layer**: Continuously generates large-scale structural schemas modeled around standard multi-cloud billing formats (Parquet) anchored to Real-Time. 
- **Inference Pipeline**: A decoupled, high-performance execution of 6 ML stages built dynamically on application boot. 
- **RESTful Endpoints**: Extremely fast routing using `uvicorn` and FastAPI definitions, natively serializing multidimensional pandas targets (and strictly filtering `NaN/inf` via custom parsers).

### 2. `frontend/` (React 18 + Vite)
- **Glassmorphism Design System**: Built strictly with CSS Modules and inline styles, eliminating Tailwind dependencies to achieve maximum aesthetic control.
- **Dynamic Polling Hook**: Incorporates custom `usePolling` behavior handling asynchronous updates every interval.
- **Recharts Integration**: Multi-series, responsive graphing capabilities mapping live time sequences without hydration bottlenecks. 

---

## 🛠️ Quick Start (Local Deployment)

### Prerequisites:
- Python 3.10+
- Node.js 18+

### Step 1: Start the AI Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Boot the uvicorn server (Will run the 3-minute ML pipeline startup)
uvicorn main:app --host 0.0.0.0 --port 8000
```
*Note: Generating the synthetic model data and training the LSTM autoencoders sequentially will take roughly ~3 minutes. Ensure `uvicorn` finishes its startup before using the front-end.*

### Step 2: Start the React Dashboard
```bash
# Open a new terminal instance
cd frontend
npm install
npm run dev
```

Navigate to **http://localhost:5173** to view your running FinOps Intelligence Platform!

---

## 📈 ML Pipeline Execution Flow
The orchestrator specifically executes in the following sequence at `main.py` initiation:
1. **Billing Data Injection** — Instantiates `generator.py` anchoring output up to exact current dates (IST).
2. **Statistical Scanning** — STL / GESD filtering bounds.
3. **ML Density Identification** — Isolation forests + One-Class SVM to single out distinct multivariate anomalies.
4. **DL Sequence Recognition** — Feedforward LSTM Autoencoders resolving temporal/seasonal drifting deviations. 
5. **Attribution & Alerts** — Unifies via Ensemble logic; triggers severity classification matching monthly spend thresholds.
6. **Live Forecasting** — Gradient boosted Prophet models executing budget P90 predictions for alert polling.

---

## 🛡️ License
Released under the [MIT License](LICENSE). 
