# AI-Based Smart Bridge Monitoring & Risk Prediction System

The AI-Based Smart Bridge Monitoring & Risk Prediction System is a production-style Flask web application that simulates a smart infrastructure monitoring platform. Users can search a global bridge catalog, open a bridge dashboard, generate live sensor data, and predict structural risk using a Machine Learning model trained on realistic synthetic inspection signals.

## Features

- Searchable bridge catalog with 25+ real bridges from India and around the world
- Dedicated dashboard for each bridge with metadata and estimated condition
- Live sensor simulation for load, vibration, crack severity, and structural stress
- AI risk prediction using a RandomForestClassifier
- Confidence score, system status, and risk meter visualization
- Futuristic dark dashboard UI with glassmorphism styling
- Responsive frontend with JavaScript-driven interactions
- Render-ready deployment using Gunicorn

## Screenshots

Add homepage and dashboard screenshots here.

## Project Structure

```text
smart-bridge-ai/
│
├── app.py
├── train_model.py
├── bridge_data.json
├── model.pkl
├── requirements.txt
├── Procfile
├── README.md
│
├── templates/
│   ├── index.html
│   └── dashboard.html
│
└── static/
    ├── style.css
    └── script.js
```

## Installation

1. Clone or download the repository.
2. Move into the project directory:

```bash
cd smart-bridge-ai
```

3. Create a virtual environment:

```bash
python -m venv venv
```

4. Activate the environment.

Windows:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

5. Install the dependencies:

```bash
pip install -r requirements.txt
```

## Running Locally

1. Train the machine learning model:

```bash
python train_model.py
```

2. Start the Flask development server:

```bash
python app.py
```

3. Open the application:

```text
http://127.0.0.1:5000
```

## Deployment on Render

1. Push the project to GitHub.
2. Sign in to Render and create a new Web Service.
3. Connect the repository.
4. Use the following settings:

- Build Command: `pip install -r requirements.txt && python train_model.py`
- Start Command: `gunicorn app:app`

5. Deploy the service.

## Future Improvements

- Add real IoT sensor ingestion instead of simulated values
- Store inspection history in a database
- Add GIS map integration for bridge visualization
- Introduce anomaly detection for time-series sensor streams
- Add authentication for infrastructure teams and inspectors
