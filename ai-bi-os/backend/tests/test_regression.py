import pytest
from app.services.regression.model_registry import model_registry
from app.services.regression.regression_validator import regression_validator
from app.services.regression.prediction_engine import prediction_engine

def test_model_registry_supported_models():
    """Ensure registry correctly identifies supported regression algorithms."""
    assert model_registry.is_supported("LINEAR_REGRESSION") == True
    assert model_registry.is_supported("RIDGE_REGRESSION") == True
    assert model_registry.is_supported("LOGISTIC_REGRESSION") == True
    assert model_registry.is_supported("NEURAL_NETWORK") == False

def test_regression_validator_sample_size():
    """Ensure validation catches insufficient sample size for features."""
    
    # Valid: 10 rows, 3 features (n >= p + 2)
    valid_stats = {"total_rows": 10}
    features = ["f1", "f2", "f3"]
    assert regression_validator.validate_training_data(valid_stats, features) == True
    
    # Invalid: 4 rows, 3 features (n < p + 2)
    invalid_stats = {"total_rows": 4}
    with pytest.raises(ValueError) as e_info:
        regression_validator.validate_training_data(invalid_stats, features)
    assert "Insufficient sample size" in str(e_info.value)

def test_prediction_engine():
    """Ensure prediction engine calculates y = mx + b deterministically."""
    
    intercept = 10.0
    coefficients = {"feature_1": 2.0, "feature_2": -1.5}
    
    inputs = [
        {"feature_1": 5.0, "feature_2": 2.0}, # y = 10 + (5*2) + (2*-1.5) = 10 + 10 - 3 = 17
        {"feature_1": 0.0, "feature_2": 0.0}  # y = 10
    ]
    
    predictions = prediction_engine.predict(intercept, coefficients, inputs)
    
    assert len(predictions) == 2
    assert predictions[0]["predicted_value"] == 17.0
    assert predictions[1]["predicted_value"] == 10.0
