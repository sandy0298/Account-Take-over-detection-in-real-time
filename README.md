# Account Takeover (ATO) Attack Detection on Google Cloud

## 📌 Overview

This repository describes an **end-to-end, real-time Account Takeover (ATO) Attack Detection system** built on **Google Cloud Platform (GCP)**. The solution leverages **streaming data pipelines, Vertex AI (LSTM model), BigQuery, Bigtable, Cloud Functions, Pub/Sub, and Gemini (GenAI)** to detect suspicious login and transaction behavior, trigger fraud responses, and continuously improve fraud intelligence.

The architecture is designed for **banking and financial services** use cases where low-latency fraud detection, explainability, scalability, and governance are critical.

---

## 🧠 Key Capabilities

* Real-time user activity ingestion
* Behavioral fraud detection using **LSTM models**
* Streaming inference with **Vertex AI**
* Automated ATO response workflows (OTP, IVR, account blocking)
* Feedback loop for continuous model improvement
* Built-in **data governance & data quality** controls
* **Gemini-powered GenAI** for pattern discovery and natural language data access

---

## 🏗️ High-Level Architecture

![ATO Architecture](ATO_detection_v1.jpg)

---

## 🔄 End-to-End Data Flow

### 1️⃣ User Activity Ingestion

* Customer login and transaction events from **Internet Banking / Mobile Banking**
* Events are streamed in **real time to Pub/Sub**

**Component:**

* `Customer Account Activities – Pub/Sub`

---

### 2️⃣ Streaming Fraud Detection Pipeline

* **Dataflow (Streaming)** reads events from Pub/Sub
* Session and behavioral features are enriched
* Data is:

  * Stored in **Cloud Bigtable** (low-latency session storage)
  * Sent to **Vertex AI hosted LSTM model** for inference

**Component:**

* `Dataflow Streaming Pipeline`

---

### 3️⃣ ML Model – ATO LSTM (Vertex AI)

* Custom **LSTM model** trained on:

  * Historical customer footprint data (BigQuery)
  * Demographic data (BigQuery)
* Model is deployed to a **Vertex AI Endpoint**
* Detects:

  * Unusual login behavior
  * Device / location anomalies
  * Session hijacking patterns

**Component:**

* `ATO_LSTM – Vertex AI`

---

### 4️⃣ Suspicious Activity Publishing

* Predictions marked as suspicious are:

  * Written to **BigQuery** for analytics
  * Published to **Fraud Transaction Pub/Sub** for downstream action

---

### 5️⃣ ATO Triggers & Fraud Response

* **Cloud Functions** subscribe to Fraud Pub/Sub
* Secure secrets retrieved from **Secret Manager**
* Automated actions:

  * OTP verification
  * IVR call to customer
  * User confirmation (Yes / No)

**Outcomes:**

* ✅ Non-suspicious → stored for reporting
* ❌ Confirmed fraud → immediate action

---

### 6️⃣ Incident Management & Enforcement

* Confirmed fraud cases:

  * Logged in **ServiceNow**
  * User account blocked immediately
  * Fraud activity stored in BigQuery

**Component:**

* `ServiceNow Integration`

---

### 7️⃣ Analytics & Reporting

* Data stored in BigQuery:

  * User footprint data
  * Attack patterns
  * Fraud confirmation results
* Dashboards built using **Looker Studio**

---

## 🤖 Gemini (GenAI) Integration

Gemini enhances the platform by:

* Discovering **new fraud patterns** automatically
* Assisting in **feature engineering** for model retraining
* Enabling **"Talk to Database"** capabilities:

  * Natural language queries for business & risk teams
  * No SQL expertise required

---

## 🛡️ Data Governance & Quality

### Data Governance

* Integrated governance rules across pipelines
* Ensures compliance with banking regulations

### Data Quality

* Rules enforced using **Great Expectations**
* Schema drift and data anomalies handled proactively

---

## 🧱 Technology Stack

| Layer         | Services           |
| ------------- | ------------------ |
| Ingestion     | Pub/Sub            |
| Streaming     | Dataflow           |
| Storage       | BigQuery, Bigtable |
| ML            | Vertex AI (LSTM)   |
| GenAI         | Gemini             |
| Orchestration | Cloud Functions    |
| Security      | Secret Manager     |
| ITSM          | ServiceNow         |
| Visualization | Looker Studio      |

---

## 🚀 Use Cases

* Account Takeover detection
* Fraudulent login prevention
* Behavioral biometrics
* Risk-based authentication
* Real-time fraud alerting

---

## 📈 Benefits

* Near real-time fraud detection
* Highly scalable & cloud-native
* Explainable ML with feedback loops
* Reduced false positives
* Strong governance & compliance

---

## 📌 Future Enhancements

* Graph-based fraud detection
* Adaptive risk scoring
* Cross-channel fraud correlation
* Multi-region active-active deployment

---

## 📄 License

This project is provided for **reference architecture and educational purposes**.

---

## 🙌 Acknowledgements

Built using **Google Cloud Platform**, **Vertex AI**, and **Gemini Generative AI** to demonstrate next-generation fraud detection systems.
