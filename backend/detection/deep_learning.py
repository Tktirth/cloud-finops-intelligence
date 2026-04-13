"""
Deep Learning Anomaly Detection — LSTM Autoencoder (PyTorch)
Detects temporal cost anomalies by reconstructing sequences.
High reconstruction error → anomaly.
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings("ignore")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SEQ_LEN = 14  # 2-week lookback window


class LSTMAutoencoder(nn.Module):
    def __init__(self, input_size: int = 1, hidden_size: int = 32, num_layers: int = 2):
        super().__init__()
        self.encoder = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.1)
        self.decoder = nn.LSTM(hidden_size, hidden_size, num_layers, batch_first=True, dropout=0.1)
        self.output_layer = nn.Linear(hidden_size, input_size)

    def forward(self, x):
        # Encode
        _, (h, c) = self.encoder(x)
        # Repeat the last hidden state as decoder input
        decoder_input = h[-1].unsqueeze(1).repeat(1, x.size(1), 1)
        decoded, _ = self.decoder(decoder_input)
        out = self.output_layer(decoded)
        return out


def make_sequences(values: np.ndarray, seq_len: int) -> np.ndarray:
    """Sliding window sequences."""
    seqs = []
    for i in range(len(values) - seq_len + 1):
        seqs.append(values[i:i + seq_len])
    return np.array(seqs)


def train_lstm_autoencoder(series: np.ndarray, epochs: int = 30, batch_size: int = 16, lr: float = 1e-3) -> tuple:
    """Train LSTM Autoencoder on a cost time series. Returns (model, scaler, threshold)."""
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(series.reshape(-1, 1)).flatten()

    seqs = make_sequences(scaled, SEQ_LEN)
    if len(seqs) < 8:
        return None, scaler, 1.0

    X = torch.FloatTensor(seqs).unsqueeze(-1).to(DEVICE)  # (N, SEQ_LEN, 1)
    dataset = TensorDataset(X, X)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model = LSTMAutoencoder(input_size=1, hidden_size=32, num_layers=2).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    model.train()
    for epoch in range(epochs):
        for batch_x, batch_y in loader:
            optimizer.zero_grad()
            out = model(batch_x)
            loss = criterion(out, batch_y)
            loss.backward()
            optimizer.step()

    # Compute reconstruction errors for threshold
    model.eval()
    with torch.no_grad():
        rec = model(X)
        errors = torch.mean((X - rec) ** 2, dim=(1, 2)).cpu().numpy()

    threshold = np.mean(errors) + 2.5 * np.std(errors)
    return model, scaler, threshold


def detect_lstm_anomalies(series: np.ndarray, model, scaler, threshold: float) -> tuple:
    """Return per-timestep reconstruction error and anomaly flags."""
    scaled = scaler.transform(series.reshape(-1, 1)).flatten()
    seqs = make_sequences(scaled, SEQ_LEN)

    if len(seqs) == 0 or model is None:
        return np.zeros(len(series)), np.zeros(len(series), dtype=bool)

    X = torch.FloatTensor(seqs).unsqueeze(-1).to(DEVICE)
    model.eval()
    with torch.no_grad():
        rec = model(X)
        errors = torch.mean((X - rec) ** 2, dim=(1, 2)).cpu().numpy()

    # Map errors back to original timesteps (last position of each window)
    full_errors = np.zeros(len(series))
    for i, err in enumerate(errors):
        full_errors[i + SEQ_LEN - 1] = err

    # Fill early positions with mean
    full_errors[:SEQ_LEN - 1] = np.mean(errors[:5]) if len(errors) >= 5 else threshold / 2

    flags = full_errors > threshold
    return full_errors, flags


def run_dl_detection(daily_df: pd.DataFrame, epochs: int = 20) -> pd.DataFrame:
    """
    Run LSTM Autoencoder detection per resource_key.
    Returns DataFrame with dl_anomaly flags and dl_score.
    """
    results = []

    for key, group in daily_df.groupby("resource_key"):
        group = group.sort_values("date").copy()
        series = group["cost_usd"].values

        if len(series) < SEQ_LEN + 4:
            for _, row in group.iterrows():
                results.append({**row.to_dict(), "is_dl_anomaly": False, "dl_score": 0.0})
            continue

        try:
            model, scaler, threshold = train_lstm_autoencoder(series, epochs=epochs)
            dl_errors, dl_flags = detect_lstm_anomalies(series, model, scaler, threshold)
        except Exception as e:
            dl_errors = np.zeros(len(series))
            dl_flags = np.zeros(len(series), dtype=bool)

        for i, (_, row) in enumerate(group.iterrows()):
            results.append({
                **row.to_dict(),
                "is_dl_anomaly": bool(dl_flags[i]),
                "dl_score": float(dl_errors[i]),
            })

    return pd.DataFrame(results)
