# 📚 Semantic Book Recommender

A smart book recommendation system that leverages a Vector Database to provide personalized, context-driven recommendations.

## Newest Version 2.0.0

🌐 **[Try the Latest Demo!](https://tuanqpham0921.com/book-recommender)**
📖 **[Read the Blog](https://medium.com/@tuanqpham0921/book-recommender-v2-blog-d1f57fdc2fcf)**

---

## 🚀 Overview
This project uses **Semantic Search** to recommend books based on user descriptions like:
> *“A heartwarming story about overcoming adversity”*

---

## 🛠 Tech Stack
- **Frontend**: Vite + React (deployed on Firebase Hosting)
- **Backend API**: FastAPI + PostgreSQL with pgvector (Vector Search)
- **LLM Integration**:
  - LangChain for chaining LLM workflows
  - OpenAI API for embeddings and language understanding
  - HuggingFace Transformers for preprocessing
- **Infrastructure**: 
  - Dockerized backend
  - Google Cloud Run (for API deployment)
  - Google Cloud Build (CI/CD pipeline)
- **Data Format**: Parquet files for optimized storage and retrieval
- **Data Models & Validation**: Pydantic for schema validation and API request handling
- **Unit Tests**: uses PyTest to make sure functions are working correctly

---

## 📊 Data Processing & Embedding
- **Data Preprocessing**: Jupyter Notebook in `/data_processing_folder/` handles:
  - Text cleaning
  - Emotion tagging
  - Formatting into Parquet files.
- **Embeddings**: Vector representations stored in **PostgreSQL with pgvector** for fast similarity search.

---

## ☁️ Deployment
- Backend is containerized using **Docker** and deployed on **Google Cloud Run**.
- CI/CD pipeline is automated using **Google Cloud Build**.
- Frontend hosted via **Firebase Hosting**.

---
