import pandas as pd
import numpy as np
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import pickle
import os

DATA_FILE = "ml/gesture_data.csv"
MODEL_FILE = "ml/gesture_model.pkl"

def train():
    print("Loading data...")
    df = pd.read_csv(DATA_FILE)

        # Drop redundant wrist features (always 0)
    X = df.drop(columns=["label"]).values
    y = df["label"].values

    print(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"Classes: {list(set(y))}\n")

    # Split — 80% train, 20% test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale features — SVM is sensitive to feature magnitude
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    print("Training SVM...")
    model = SVC(kernel='rbf', C=10, gamma='scale', probability=True)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = (y_pred == y_test).mean()

    print(f"\nTest Accuracy: {accuracy * 100:.1f}%\n")
    print("Per-gesture breakdown:")
    print(classification_report(y_test, y_pred))

    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred, labels=list(set(y))))

    # Cross validation — more reliable than single split
    X_all = scaler.transform(df.drop(columns=["label"]).values)
    cv_scores = cross_val_score(model, X_all, y, cv=5)
    print(f"\n5-Fold Cross Validation: {cv_scores.mean()*100:.1f}% ± {cv_scores.std()*100:.1f}%")

    # Save model + scaler together
    bundle = {"model": model, "scaler": scaler}
    with open(MODEL_FILE, "wb") as f:
        pickle.dump(bundle, f)

    print(f"\nModel saved to {MODEL_FILE}")

if __name__ == "__main__":
    train()