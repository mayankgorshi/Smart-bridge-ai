from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.pkl"
RANDOM_STATE = 42


def generate_synthetic_dataset(sample_size=4200):
    rng = np.random.default_rng(RANDOM_STATE)

    age = rng.uniform(1, 120, sample_size).round(2)
    load = rng.uniform(15, 165, sample_size).round(2)
    vibration = rng.uniform(0.4, 12.5, sample_size).round(2)
    cracks = rng.uniform(0, 10, sample_size).round(2)
    stress = rng.uniform(18, 100, sample_size).round(2)

    weighted_score = (
        (load / 165) * 24
        + (vibration / 12.5) * 19
        + (cracks / 10) * 22
        + (stress / 100) * 23
        + (age / 120) * 12
    )

    weighted_score += np.where((load > 120) & (vibration > 8), 10, 0)
    weighted_score += np.where((cracks > 6) & (stress > 72), 14, 0)
    weighted_score += np.where((age > 75) & (stress > 68), 9, 0)
    weighted_score -= np.where(
        (load < 55)
        & (vibration < 3.2)
        & (cracks < 2.2)
        & (stress < 45)
        & (age < 30),
        8,
        0,
    )

    risk = []
    for score, current_load, current_vibration, current_cracks, current_stress, current_age in zip(
        weighted_score, load, vibration, cracks, stress, age
    ):
        if (
            score >= 69
            or (current_cracks > 7.5 and current_stress > 80)
            or (current_load > 135 and current_vibration > 9 and current_age > 60)
        ):
            risk.append("CRITICAL")
        elif (
            score >= 44
            or current_vibration > 6.8
            or current_cracks > 4.2
            or (current_age > 55 and current_stress > 60)
        ):
            risk.append("WARNING")
        else:
            risk.append("SAFE")

    dataset = pd.DataFrame(
        {
            "load": load,
            "vibration": vibration,
            "cracks": cracks,
            "stress": stress,
            "age": age,
            "risk": risk,
        }
    )
    return dataset


def train_and_save_model():
    dataset = generate_synthetic_dataset()

    X = dataset[["load", "vibration", "cracks", "stress", "age"]]
    y = dataset["risk"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=250,
        max_depth=12,
        min_samples_split=4,
        random_state=RANDOM_STATE,
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    matrix = confusion_matrix(
        y_test, predictions, labels=["SAFE", "WARNING", "CRITICAL"]
    )

    joblib.dump(model, MODEL_PATH)

    print("Smart bridge risk model training complete.")
    print(f"Accuracy Score: {accuracy:.4f}")
    print("Confusion Matrix:")
    print(matrix)


if __name__ == "__main__":
    train_and_save_model()
