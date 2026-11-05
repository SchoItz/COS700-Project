"""CNN-RNN and autoencoder-RNN hybrids."""
from __future__ import annotations

import numpy as np
import torch.nn as nn

from models.base import DetectorFactory
from models.deep.torch_models import _posWeight, _toTensor, _TorchDetectorBase


class CNNRNNHybrid(nn.Module):
    """Conv1d features into an LSTM classifier."""

    def __init__(self, inDim: int, convHidden: int = 16, lstmHidden: int = 32):
        super().__init__()
        self.conv = nn.Sequential(nn.Conv1d(1, convHidden, kernel_size=3, padding=1), nn.ReLU())
        self.lstm = nn.LSTM(convHidden, lstmHidden, batch_first=True)
        self.head = nn.Linear(lstmHidden, 1)

    def forward(self, x):
        z = self.conv(x.unsqueeze(1))
        z = z.permute(0, 2, 1)
        out, _ = self.lstm(z)
        return self.head(out[:, -1, :]).squeeze(-1)


class CNNRNNHybridDetector(_TorchDetectorBase):
    def __init__(self, inDim: int, **kwargs):
        super().__init__("cnnRnnHybrid", **kwargs)
        self.inDim = inDim

    def fit(self, X: np.ndarray, y: np.ndarray) -> CNNRNNHybridDetector:
        self.model = CNNRNNHybrid(self.inDim)
        lossFn = nn.BCEWithLogitsLoss(pos_weight=_posWeight(y))
        self._trainLoop(
            self.model, _toTensor(X), _toTensor(y), lambda m, xb, yb: lossFn(m(xb), yb)
        )
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self._scoresInBatches(X)


class AutoencoderRNNHybrid(nn.Module):
    """Autoencoder latent into an LSTM classifier."""

    def __init__(self, inDim: int, latent: int = 16, lstmHidden: int = 32):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(inDim, 32), nn.ReLU(), nn.Linear(32, latent))
        self.decoder = nn.Sequential(nn.Linear(latent, 32), nn.ReLU(), nn.Linear(32, inDim))
        self.lstm = nn.LSTM(latent, lstmHidden, batch_first=True)
        self.head = nn.Linear(lstmHidden, 1)

    def forward(self, x):
        z = self.encoder(x)
        out, _ = self.lstm(z.unsqueeze(1))
        return self.head(out[:, -1, :]).squeeze(-1)

    def reconstruct(self, x):
        return self.decoder(self.encoder(x))


class AutoencoderRNNHybridDetector(_TorchDetectorBase):
    def __init__(self, inDim: int, recWeight: float = 0.3, **kwargs):
        super().__init__("autoRnnHybrid", **kwargs)
        self.inDim = inDim
        self.recWeight = recWeight

    def fit(self, X: np.ndarray, y: np.ndarray) -> AutoencoderRNNHybridDetector:
        self.model = AutoencoderRNNHybrid(self.inDim)
        bce = nn.BCEWithLogitsLoss(pos_weight=_posWeight(y))
        mse = nn.MSELoss()

        def lossFn(model: AutoencoderRNNHybrid, xb, yb):
            return bce(model(xb), yb) + self.recWeight * mse(model.reconstruct(xb), xb)

        self._trainLoop(self.model, _toTensor(X), _toTensor(y), lossFn)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self._scoresInBatches(X)


def hybridFactories(inDim: int, epochs: int = 15) -> dict[str, DetectorFactory]:
    return {
        "cnnRnnHybrid": lambda: CNNRNNHybridDetector(inDim, epochs=epochs),
        "autoRnnHybrid": lambda: AutoencoderRNNHybridDetector(inDim, epochs=epochs),
    }
