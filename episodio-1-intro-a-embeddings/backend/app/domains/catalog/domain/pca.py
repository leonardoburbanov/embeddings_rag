"""Cosine similarity and a three-component PCA projection."""

import numpy as np


def cosine(left: list[float], right: list[float]) -> float:
    """Return the cosine similarity of two vectors."""
    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def project(vectors: list[list[float]]) -> list[tuple[float, float, float]]:
    """Project each row onto the first three principal components.

    Fewer than four rows cannot span three axes, so missing components stay at zero.
    """
    matrix = np.asarray(vectors, dtype=np.float64)
    centered = matrix - matrix.mean(axis=0)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    width = min(3, vt.shape[0])
    coords = centered @ vt[:width].T
    if width < 3:
        coords = np.pad(coords, ((0, 0), (0, 3 - width)))
    return [(float(row[0]), float(row[1]), float(row[2])) for row in coords]
