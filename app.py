from datetime import datetime
import json
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, abort, jsonify, render_template, request


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.pkl"
BRIDGE_DATA_PATH = BASE_DIR / "bridge_data.json"
CURRENT_YEAR = datetime.now().year
ASSET_VERSION = "20260425"

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
    static_url_path="/static",
)


RISK_CONTENT = {
    "SAFE": {
        "badge_class": "safe",
        "icon": "&#9989;",
        "status_text": "Structural behavior remains within safe operating limits.",
        "recommended_action": "Continue scheduled inspections and passive monitoring.",
        "system_status": "Nominal",
    },
    "WARNING": {
        "badge_class": "warning",
        "icon": "&#9888;&#65039;",
        "status_text": "Early warning indicators suggest elevated stress on the structure.",
        "recommended_action": "Increase inspection frequency and validate sensor readings.",
        "system_status": "Elevated Surveillance",
    },
    "CRITICAL": {
        "badge_class": "critical",
        "icon": "&#128680;",
        "status_text": "Critical anomalies detected. Immediate engineering response is advised.",
        "recommended_action": "Trigger priority inspection and evaluate traffic restrictions.",
        "system_status": "Emergency Review",
    },
}


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "model.pkl is missing. Run train_model.py before starting the application."
        )
    return joblib.load(MODEL_PATH)


def estimate_condition(age, traffic_level):
    traffic_penalty = {
        "Low": 4,
        "Medium": 8,
        "High": 12,
        "Very High": 16,
        "Extreme": 20,
    }.get(traffic_level, 10)

    health_score = max(12, 100 - (age * 0.62) - traffic_penalty)

    if health_score >= 75:
        return "Good"
    if health_score >= 58:
        return "Stable - Monitor"
    if health_score >= 40:
        return "Preventive Maintenance Recommended"
    return "Priority Inspection Needed"


def build_bridge_record(bridge):
    age = max(0, CURRENT_YEAR - int(bridge["built_year"]))
    bridge_copy = dict(bridge)
    bridge_copy["age"] = age
    bridge_copy["estimated_condition"] = estimate_condition(age, bridge["traffic_level"])
    bridge_copy["region_group"] = (
        "India" if "India" in bridge_copy["location"] else "International"
    )
    return bridge_copy


def load_bridge_catalog():
    with BRIDGE_DATA_PATH.open(encoding="utf-8") as file:
        raw_bridges = json.load(file)

    return [build_bridge_record(bridge) for bridge in raw_bridges]


def load_bridge_map():
    bridges = load_bridge_catalog()
    return bridges, {bridge["id"]: bridge for bridge in bridges}


def validate_numeric_input(raw_value, field_name, minimum_value, maximum_value):
    try:
        numeric_value = float(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid number.") from exc

    if numeric_value < minimum_value or numeric_value > maximum_value:
        raise ValueError(
            f"{field_name} must be between {minimum_value} and {maximum_value}."
        )

    return round(numeric_value, 2)


def calculate_risk_meter(label, confidence):
    base_value = {
        "SAFE": 28,
        "WARNING": 64,
        "CRITICAL": 91,
    }[label]
    adjustment = round((confidence - 50) * 0.18)
    return max(8, min(100, base_value + adjustment))


def build_overview_stats(bridges):
    return {
        "total_bridges": len(bridges),
        "india_count": sum(1 for bridge in bridges if bridge["region_group"] == "India"),
        "global_count": sum(
            1 for bridge in bridges if bridge["region_group"] == "International"
        ),
        "avg_age": round(sum(bridge["age"] for bridge in bridges) / len(bridges)),
    }


BRIDGES, BRIDGE_MAP = load_bridge_map()
MODEL = load_model()


@app.context_processor
def inject_asset_version():
    return {"asset_version": ASSET_VERSION}


@app.route("/")
def index():
    stats = build_overview_stats(BRIDGES)
    return render_template("index.html", bridges=BRIDGES, stats=stats, error=None)


@app.route("/bridge/<bridge_id>")
def dashboard(bridge_id):
    bridge = BRIDGE_MAP.get(bridge_id)
    if not bridge:
        abort(404)

    dashboard_metrics = [
        {"label": "Bridge Age", "value": f"{bridge['age']} years"},
        {"label": "Traffic Level", "value": bridge["traffic_level"]},
        {"label": "Bridge Type", "value": bridge["bridge_type"]},
        {"label": "Estimated Condition", "value": bridge["estimated_condition"]},
    ]

    return render_template(
        "dashboard.html",
        bridge=bridge,
        metrics=dashboard_metrics,
        model_name="RandomForest Risk Classifier",
    )


@app.route("/predict", methods=["POST"])
def predict():
    request_data = request.get_json(silent=True) or request.form.to_dict()
    bridge_id = (request_data.get("bridge_id") or "").strip()
    bridge = BRIDGE_MAP.get(bridge_id)

    if not bridge:
        return jsonify({"error": "Please select a valid bridge before prediction."}), 400

    try:
        load = validate_numeric_input(
            request_data.get("load"), "Bridge load", 0, 200
        )
        vibration = validate_numeric_input(
            request_data.get("vibration"), "Vibration level", 0, 15
        )
        cracks = validate_numeric_input(
            request_data.get("cracks"), "Crack severity", 0, 10
        )
        stress = validate_numeric_input(
            request_data.get("stress"), "Structural stress", 0, 100
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    features = pd.DataFrame(
        [
            {
                "load": load,
                "vibration": vibration,
                "cracks": cracks,
                "stress": stress,
                "age": bridge["age"],
            }
        ]
    )

    prediction = MODEL.predict(features)[0]
    probabilities = MODEL.predict_proba(features)[0]
    confidence = round(max(probabilities) * 100, 2)
    risk_meter = calculate_risk_meter(prediction, confidence)

    response = {
        "bridge_name": bridge["name"],
        "bridge_age": bridge["age"],
        "prediction": prediction,
        "confidence": confidence,
        "risk_meter": risk_meter,
        "traffic_level": bridge["traffic_level"],
        "estimated_condition": bridge["estimated_condition"],
        "sensor_snapshot": {
            "Bridge Load": f"{load:.2f} tons",
            "Vibration Level": f"{vibration:.2f} mm/s",
            "Crack Severity": f"{cracks:.2f} / 10",
            "Structural Stress": f"{stress:.2f} %",
        },
        **RISK_CONTENT[prediction],
    }
    return jsonify(response)


@app.errorhandler(404)
def page_not_found(_error):
    stats = build_overview_stats(BRIDGES)
    return (
        render_template(
            "index.html",
            bridges=BRIDGES,
            stats=stats,
            error="The requested bridge dashboard was not found. Please choose a bridge from the catalog.",
        ),
        404,
    )


if __name__ == "__main__":
    app.run(debug=True)
