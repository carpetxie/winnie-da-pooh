"""
backtest/track_a.py

Phase 2: Universal Calibration Model Training

Trains a logistic regression model to calibrate market prices using metadata.

Run with: uv run python -m backtest.track_a
"""

import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV

PROCESSED_DIR = "data/processed"
MODELS_DIR = "data/models"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load universal_features.csv and split by 'split' column.

    Returns:
        (train_df, test_df)
    """
    df = pd.read_csv(
        os.path.join(PROCESSED_DIR, "universal_features.csv"),
        parse_dates=['open_time', 'close_time', 'midpoint']
    )

    train_df = df[df['split'] == 'train'].copy()
    test_df = df[df['split'] == 'test'].copy()

    print(f"Loaded data: {len(train_df)} train, {len(test_df)} test")

    return train_df, test_df


def train_model(X_train: np.ndarray, y_train: np.ndarray) -> LogisticRegression:
    """
    Train Universal Calibration model.

    Uses LogisticRegression with L2 penalty (not L1 Lasso).
    Optional: Wrap with CalibratedClassifierCV for extra calibration.

    Args:
        X_train: Feature matrix [feature_price, feature_volatility, feature_days_remaining]
        y_train: Binary outcomes (0 or 1)

    Returns:
        Fitted model
    """
    # Option 1: Standard Logistic Regression
    model = LogisticRegression(
        penalty='l2',
        C=1.0,  # Regularization strength (lower = more regularization)
        max_iter=1000,
        random_state=42
    )

    # Option 2: Calibrated Classifier (uncomment to use)
    # base_model = LogisticRegression(penalty='l2', C=1.0, max_iter=1000, random_state=42)
    # model = CalibratedClassifierCV(base_model, cv=5, method='sigmoid')

    model.fit(X_train, y_train)

    print(f"✓ Model trained")
    if hasattr(model, 'coef_'):
        print(f"  Coefficients: {model.coef_[0]}")
        print(f"  Intercept: {model.intercept_[0]}")

    return model


def predict(model: LogisticRegression, X_test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate calibrated probabilities and log-odds.

    Returns:
        (P_stat, L_stat)
    """
    P_stat = model.predict_proba(X_test)[:, 1]
    P_stat = np.clip(P_stat, 1e-6, 1 - 1e-6)
    L_stat = np.log(P_stat / (1 - P_stat))

    return P_stat, L_stat


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Load
    train_df, test_df = load_data()

    # Drop rows with missing features
    feature_cols = ['feature_price', 'feature_volatility', 'feature_days_remaining']
    train_df = train_df.dropna(subset=feature_cols)
    test_df = test_df.dropna(subset=feature_cols)

    X_train = train_df[feature_cols].values
    y_train = train_df['y_true'].values
    X_test = test_df[feature_cols].values
    y_test = test_df['y_true'].values
    test_tickers = test_df['ticker'].values

    print(f"After dropping NaN: {len(train_df)} train, {len(test_df)} test")

    # Train
    print("\nTraining Universal Calibration Model...")
    model = train_model(X_train, y_train)

    # Predict
    P_stat, L_stat = predict(model, X_test)

    # Save predictions
    results = pd.DataFrame({
        'ticker': test_tickers,
        'P_stat': P_stat,
        'L_stat': L_stat,
        'y_true': y_test,
    })
    results.to_csv(os.path.join(PROCESSED_DIR, "track_a_predictions.csv"), index=False)

    # Save model coefficients
    if hasattr(model, 'coef_'):
        coefs = pd.DataFrame({
            'feature': feature_cols,
            'coefficient': model.coef_[0],
        })
        coefs.to_csv(os.path.join(MODELS_DIR, "track_a_coefficients.csv"), index=False)

    print(f"\n✅ Track A complete")
    print(f"   {len(results)} test predictions saved")
    print(f"   Mean P_stat: {P_stat.mean():.3f}")
    print(f"   Mean y_true: {y_test.mean():.3f}")


if __name__ == "__main__":
    main()
