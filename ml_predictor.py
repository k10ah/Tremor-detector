# ml_predictor.py
"""
Real-time ML prediction module for tremor classification.
Integrates trained Random Forest model with live sensor data.
"""

import numpy as np
import pandas as pd
import joblib
from collections import deque
from typing import Dict, List, Optional, Tuple
import asyncio
from pathlib import Path


class TremorPredictor:
    """
    Real-time tremor classification using sliding window feature extraction
    and trained Random Forest model.
    """
    
    def __init__(
        self,
        model_path: str = "rf_model.pkl",
        window_size: int = 200,
        stride: int = 100,
        prediction_threshold: float = 0.5
    ):
        """
        Initialize the predictor with trained model and parameters.
        
        Args:
            model_path: Path to trained Random Forest model (.pkl file)
            window_size: Number of samples for feature extraction (matches training)
            stride: Number of samples to slide window (matches training)
            prediction_threshold: Confidence threshold for tremor detection
        """
        self.window_size = window_size
        self.stride = stride
        self.threshold = prediction_threshold
        
        # Load trained model
        self.model = joblib.load(model_path)
        print(f"✓ Loaded trained model from {model_path}")
        
        # Initialize data buffers for each axis
        self.buffers = {
            'ax': deque(maxlen=window_size),
            'ay': deque(maxlen=window_size),
            'az': deque(maxlen=window_size),
            'gx': deque(maxlen=window_size),
            'gy': deque(maxlen=window_size),
            'gz': deque(maxlen=window_size)
        }
        
        # Track samples since last prediction
        self.sample_count = 0
        
        # Store last prediction
        self.last_prediction = {
            'label': 'Initializing',
            'probability': 0.0,
            'timestamp': None
        }
    
    def add_sample(self, raw_data: Dict[str, float]) -> bool:
        """
        Add a new sensor sample to the buffers.
        
        Args:
            raw_data: Dict with keys 'ax', 'ay', 'az', 'gx', 'gy', 'gz'
        
        Returns:
            True if window is ready for prediction, False otherwise
        """
        # Add raw sensor values to buffers
        for axis in ['ax', 'ay', 'az', 'gx', 'gy', 'gz']:
            if axis in raw_data:
                self.buffers[axis].append(raw_data[axis])
        
        self.sample_count += 1
        
        # Check if we have enough data and it's time to predict
        window_full = all(len(buf) == self.window_size for buf in self.buffers.values())
        stride_reached = self.sample_count >= self.stride
        
        if window_full and stride_reached:
            self.sample_count = 0  # Reset counter
            return True
        
        return False
    
    def extract_features(self) -> Dict[str, float]:
        """
        Extract statistical features from current window.
        Matches feature extraction used during training.
        
        Returns:
            Dict of feature names to values
        """
        features = {}
        
        # Extract features for each axis
        for axis, buffer in self.buffers.items():
            data = np.array(buffer)
            
            features[f'{axis}_mean'] = np.mean(data)
            features[f'{axis}_std'] = np.std(data)
            features[f'{axis}_min'] = np.min(data)
            features[f'{axis}_max'] = np.max(data)
            features[f'{axis}_energy'] = np.sum(data**2) / len(data)
        
        # Calculate Signal Magnitude Area (SMA) for accelerometer
        ax_data = np.array(self.buffers['ax'])
        ay_data = np.array(self.buffers['ay'])
        az_data = np.array(self.buffers['az'])
        
        sma = np.mean(np.abs(ax_data)) + np.mean(np.abs(ay_data)) + np.mean(np.abs(az_data))
        features['sma'] = sma
        
        return features
    
    def predict(self) -> Tuple[str, float]:
        """
        Make prediction on current window.
        
        Returns:
            Tuple of (label, probability)
            - label: "Normal" or "Hypoglycemia Tremor"
            - probability: Confidence score (0-1)
        """
        # Extract features from current window
        features = self.extract_features()
        
        # Convert to DataFrame (model expects this format)
        feature_df = pd.DataFrame([features])
        
        # Ensure feature order matches training
        # This is critical for correct predictions
        expected_features = [
            'ax_mean', 'ax_std', 'ax_min', 'ax_max', 'ax_energy',
            'ay_mean', 'ay_std', 'ay_min', 'ay_max', 'ay_energy',
            'az_mean', 'az_std', 'az_min', 'az_max', 'az_energy',
            'gx_mean', 'gx_std', 'gx_min', 'gx_max', 'gx_energy',
            'gy_mean', 'gy_std', 'gy_min', 'gy_max', 'gy_energy',
            'gz_mean', 'gz_std', 'gz_min', 'gz_max', 'gz_energy',
            'sma'
        ]
        feature_df = feature_df[expected_features]
        
        # Get prediction and probability
        prediction = self.model.predict(feature_df)[0]
        probabilities = self.model.predict_proba(feature_df)[0]
        
        # Convert prediction to label
        label = "Hypoglycemia Tremor" if prediction == 1 else "Normal"
        probability = probabilities[1] if prediction == 1 else probabilities[0]
        
        # Update last prediction
        self.last_prediction = {
            'label': label,
            'probability': float(probability),
            'timestamp': None  # Will be set by caller
        }
        
        return label, float(probability)
    
    def get_status(self) -> Dict:
        """
        Get current predictor status.
        
        Returns:
            Dict with buffer fill status and last prediction
        """
        buffer_fill = min(len(buf) for buf in self.buffers.values())
        
        return {
            'buffer_fill': buffer_fill,
            'window_size': self.window_size,
            'ready_for_prediction': buffer_fill == self.window_size,
            'samples_until_next': self.stride - self.sample_count,
            'last_prediction': self.last_prediction
        }


# Example usage in your app.py
async def example_integration():
    """
    Example of how to integrate predictor into your FastAPI app.
    """
    
    # Initialize predictor
    predictor = TremorPredictor(
        model_path="rf_model.pkl",
        window_size=200,
        stride=100,
        prediction_threshold=0.7
    )
    
    # Simulate receiving sensor data
    for i in range(250):  # Simulate 250 samples
        # This would come from your serial reader in real implementation
        sample = {
            'ax': np.random.randn() * 1000,
            'ay': np.random.randn() * 1000,
            'az': np.random.randn() * 1000,
            'gx': np.random.randn() * 100,
            'gy': np.random.randn() * 100,
            'gz': np.random.randn() * 100
        }
        
        # Add sample and check if prediction is ready
        if predictor.add_sample(sample):
            label, probability = predictor.predict()
            print(f"Prediction: {label} (confidence: {probability:.2%})")
            
            # This is where you'd emit to Socket.IO
            # await sio.emit('prediction', {
            #     'label': label,
            #     'probability': probability,
            #     'timestamp': datetime.utcnow().isoformat()
            # })


if __name__ == "__main__":
    # Run example
    asyncio.run(example_integration())