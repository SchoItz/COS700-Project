"""Autoencoder, LSTM, CNN and GNN, all with the same training budget."""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
from sklearn.neighbors import kneighbors_graph
from torch.utils.data import DataLoader, TensorDataset

from models.base import DetectorFactory, ScoreThresholdMixin

SEED = 42


def _toTensor(X: np.ndarray) -> torch.Tensor:
    return torch.as_tensor(np.asarray(X), dtype=torch.float32)


def _posWeight(y: np.ndarray) -> torch.Tensor:
    """neg/pos ratio for BCEWithLogitsLoss, so the minority class is not ignored."""
    y = np.asarray(y)
    nPos = max(int((y == 1).sum()), 1)
    nNeg = max(int((y == 0).sum()), 1)
    return torch.tensor(nNeg / nPos, dtype=torch.float32)


class _TorchDetectorBase(ScoreThresholdMixin):
    def __init__(self, name: str, epochs: int = 15, lr: float = 1e-3, batchSize: int = 256):
        self.name = name
        self.epochs = epochs
        self.lr = lr
        self.batchSize = batchSize
        self.model: nn.Module | None = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _trainLoop(self, model: nn.Module, X: torch.Tensor, y: torch.Tensor, lossFn):
        torch.manual_seed(SEED)
        model.to(self.device)
        opt = torch.optim.Adam(model.parameters(), lr=self.lr)
        loader = DataLoader(TensorDataset(X, y), batch_size=self.batchSize, shuffle=True)
        model.train()
        for _ in range(self.epochs):
            for xb, yb in loader:
                xb, yb = xb.to(self.device), yb.to(self.device)
                opt.zero_grad()
                loss = lossFn(model, xb, yb)
                loss.backward()
                opt.step()
        model.eval()

    def _scoresInBatches(self, X: np.ndarray, batch: int = 8192) -> np.ndarray:
        """Scores in chunks to limit memory."""
        out = []
        with torch.no_grad():
            for start in range(0, len(X), batch):
                xb = _toTensor(X[start : start + batch]).to(self.device)
                out.append(torch.sigmoid(self.model(xb)).cpu().numpy())
        return np.concatenate(out) if out else np.zeros(0)


class Autoencoder(nn.Module):
    def __init__(self, inDim: int, latent: int = 16):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(inDim, 32), nn.ReLU(), nn.Linear(32, latent))
        self.decoder = nn.Sequential(nn.Linear(latent, 32), nn.ReLU(), nn.Linear(32, inDim))

    def forward(self, x):
        return self.decoder(self.encoder(x))


class AutoencoderDetector(_TorchDetectorBase):
    """Trained on benign rows; score is reconstruction error, calibrated on training data."""

    def __init__(self, inDim: int, **kwargs):
        super().__init__("autoencoder", **kwargs)
        self.inDim = inDim
        self._scoreRange = (0.0, 1.0)

    def _errors(self, X: np.ndarray) -> np.ndarray:
        out = []
        with torch.no_grad():
            for start in range(0, len(X), 8192):
                xb = _toTensor(X[start : start + 8192]).to(self.device)
                recon = self.model(xb)
                out.append(((recon - xb) ** 2).mean(dim=1).cpu().numpy())
        return np.concatenate(out) if out else np.zeros(0)

    def fit(self, X: np.ndarray, y: np.ndarray) -> AutoencoderDetector:
        torch.manual_seed(SEED)
        X = np.asarray(X, dtype=float)
        normal = X[np.asarray(y) == 0]
        if len(normal) == 0:
            normal = X
        self.model = Autoencoder(self.inDim).to(self.device)
        opt = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        loader = DataLoader(
            TensorDataset(_toTensor(normal)), batch_size=self.batchSize, shuffle=True
        )
        lossFn = nn.MSELoss()
        self.model.train()
        for _ in range(self.epochs):
            for (xb,) in loader:
                xb = xb.to(self.device)
                opt.zero_grad()
                loss = lossFn(self.model(xb), xb)
                loss.backward()
                opt.step()
        self.model.eval()

        errors = self._errors(normal)
        lo = float(np.percentile(errors, 5))
        hi = float(np.percentile(errors, 99))
        self._scoreRange = (lo, max(hi, lo + 1e-9))
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        lo, hi = self._scoreRange
        return np.clip((self._errors(np.asarray(X, dtype=float)) - lo) / (hi - lo), 0.0, 1.0)


class LSTMClassifier(nn.Module):
    def __init__(self, inDim: int, hidden: int = 32):
        super().__init__()
        self.lstm = nn.LSTM(inDim, hidden, batch_first=True)
        self.head = nn.Linear(hidden, 1)

    def forward(self, x):
        if x.dim() == 2:
            x = x.unsqueeze(1)
        out, _ = self.lstm(x)
        return self.head(out[:, -1, :]).squeeze(-1)


class LSTMDetector(_TorchDetectorBase):
    """LSTM over each row's feature vector."""

    def __init__(self, inDim: int, **kwargs):
        super().__init__("lstm", **kwargs)
        self.inDim = inDim

    def fit(self, X: np.ndarray, y: np.ndarray) -> LSTMDetector:
        self.model = LSTMClassifier(self.inDim)
        lossFn = nn.BCEWithLogitsLoss(pos_weight=_posWeight(y))
        self._trainLoop(
            self.model, _toTensor(X), _toTensor(y), lambda m, xb, yb: lossFn(m(xb), yb)
        )
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self._scoresInBatches(X)


class CNN1DClassifier(nn.Module):
    def __init__(self, inDim: int, hidden: int = 32):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(1, hidden, kernel_size=3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool1d(1)
        )
        self.head = nn.Linear(hidden, 1)
        self.inDim = inDim

    def forward(self, x):
        z = self.conv(x.unsqueeze(1)).squeeze(-1)
        return self.head(z).squeeze(-1)


class CNNDetector(_TorchDetectorBase):
    def __init__(self, inDim: int, **kwargs):
        super().__init__("cnn", **kwargs)
        self.inDim = inDim

    def fit(self, X: np.ndarray, y: np.ndarray) -> CNNDetector:
        self.model = CNN1DClassifier(self.inDim)
        lossFn = nn.BCEWithLogitsLoss(pos_weight=_posWeight(y))
        self._trainLoop(
            self.model, _toTensor(X), _toTensor(y), lambda m, xb, yb: lossFn(m(xb), yb)
        )
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self._scoresInBatches(X)


class SimpleGCNLayer(nn.Module):
    """Graph convolution with normalised adjacency."""

    def __init__(self, inDim: int, outDim: int):
        super().__init__()
        self.linear = nn.Linear(inDim, outDim)

    def forward(self, x, adjNorm):
        return torch.relu(torch.sparse.mm(adjNorm, self.linear(x)))


class GNNClassifier(nn.Module):
    """Two-layer GCN node classifier."""

    def __init__(self, inDim: int, hidden: int = 32):
        super().__init__()
        self.gc1 = SimpleGCNLayer(inDim, hidden)
        self.gc2 = SimpleGCNLayer(hidden, hidden)
        self.dropout = nn.Dropout(0.2)
        self.head = nn.Linear(hidden, 1)

    def forward(self, x, adjNorm):
        h = self.dropout(self.gc1(x, adjNorm))
        h = self.gc2(h, adjNorm)
        return self.head(h).squeeze(-1)


def _sparse(indices: torch.Tensor, values: torch.Tensor, n: int) -> torch.Tensor:
    """Coalesced sparse square tensor."""
    return torch.sparse_coo_tensor(
        indices, values, (n, n), check_invariants=False
    ).coalesce()


def knnAdjacency(X: np.ndarray, k: int) -> torch.Tensor:
    """Normalised k-nearest-neighbour adjacency with self-loops, as a sparse tensor."""
    n = len(X)
    if n == 1:
        idx = torch.zeros((2, 1), dtype=torch.long)
        return _sparse(idx, torch.ones(1), 1)

    k = max(1, min(k, n - 1))
    adj = kneighbors_graph(X, n_neighbors=k, mode="connectivity", include_self=True, n_jobs=-1)
    adj = adj.maximum(adj.T).tocoo()

    deg = np.asarray(adj.sum(axis=1)).ravel()
    dInvSqrt = 1.0 / np.sqrt(np.maximum(deg, 1e-12))
    values = adj.data * dInvSqrt[adj.row] * dInvSqrt[adj.col]

    indices = torch.as_tensor(np.vstack([adj.row, adj.col]), dtype=torch.long)
    return _sparse(indices, torch.as_tensor(values, dtype=torch.float32), n)


class GNNDetector(ScoreThresholdMixin):
    """GNN over a kNN graph of the rows. Graphs are capped at `maxNodes`."""

    name = "gnn"

    def __init__(
        self,
        inDim: int,
        epochs: int = 200,
        lr: float = 1e-2,
        hidden: int = 32,
        k: int = 10,
        maxNodes: int = 20000,
    ):
        self.inDim = inDim
        self.epochs = epochs
        self.lr = lr
        self.hidden = hidden
        self.k = k
        self.maxNodes = maxNodes
        self.model: GNNClassifier | None = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _subsample(self, X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if len(X) <= self.maxNodes:
            return X, y
        rng = np.random.default_rng(SEED)
        pos = np.flatnonzero(y == 1)
        neg = np.flatnonzero(y == 0)
        nPos = min(len(pos), max(1, self.maxNodes // 4))
        nNeg = min(len(neg), self.maxNodes - nPos)
        keep = np.concatenate(
            [rng.choice(pos, nPos, replace=False), rng.choice(neg, nNeg, replace=False)]
        )
        keep.sort()
        return X[keep], y[keep]

    def fit(self, X: np.ndarray, y: np.ndarray) -> GNNDetector:
        torch.manual_seed(SEED)
        X, y = self._subsample(np.asarray(X, dtype=float), np.asarray(y))
        adj = knnAdjacency(X, self.k).to(self.device)
        Xt, yt = _toTensor(X).to(self.device), _toTensor(y).to(self.device)

        self.model = GNNClassifier(self.inDim, self.hidden).to(self.device)
        opt = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        lossFn = nn.BCEWithLogitsLoss(pos_weight=_posWeight(y).to(self.device))
        self.model.train()
        for _ in range(self.epochs):
            opt.zero_grad()
            loss = lossFn(self.model(Xt, adj), yt)
            loss.backward()
            opt.step()
        self.model.eval()
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=float)
        out = []
        with torch.no_grad():
            for start in range(0, len(X), self.maxNodes):
                block = X[start : start + self.maxNodes]
                adj = knnAdjacency(block, self.k).to(self.device)
                logits = self.model(_toTensor(block).to(self.device), adj)
                out.append(torch.sigmoid(logits).cpu().numpy())
        return np.concatenate(out) if out else np.zeros(0)


def deepFactories(inDim: int, epochs: int = 15) -> dict[str, DetectorFactory]:
    return {
        "autoencoder": lambda: AutoencoderDetector(inDim, epochs=epochs),
        "lstm": lambda: LSTMDetector(inDim, epochs=epochs),
        "cnn": lambda: CNNDetector(inDim, epochs=epochs),
        "gnn": lambda: GNNDetector(inDim),
    }
