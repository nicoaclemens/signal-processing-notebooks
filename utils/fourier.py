import numpy as np
from scipy import ndimage


def extract_contour(grid):
    grid = np.asarray(grid, dtype=bool)
    if not grid.any():
        return None

    padded = np.pad(grid, 1, constant_values=0)

    labeled, n_features = ndimage.label(padded)
    if n_features == 0:
        return None
    if n_features > 1:
        sizes = ndimage.sum(padded, labeled, range(1, n_features + 1))
        padded = labeled == (np.argmax(sizes) + 1)

    # Boundary = filled pixels with at least one empty 4-neighbour
    cross = ndimage.generate_binary_structure(2, 1)
    eroded = ndimage.binary_erosion(padded, structure=cross)
    boundary = padded & ~eroded
    if not boundary.any():
        boundary = padded.copy()

    # If multiple boundary loops exist keep the largest
    bl, bn = ndimage.label(boundary)
    if bn > 1:
        bsizes = ndimage.sum(boundary, bl, range(1, bn + 1))
        boundary = bl == (np.argmax(bsizes) + 1)

    ys, xs = np.where(boundary)
    xs = xs.astype(float) - 1
    ys = ys.astype(float) - 1

    if len(xs) < 3:
        return None

    ordered = _order_nearest_neighbour(np.column_stack([xs, ys]))

    N = grid.shape[0]

    z = ordered[:, 0] + 1j * (N - 1 - ordered[:, 1])  # convention
    z -= z.mean()
    scale = np.max(np.abs(z))
    if scale > 0:
        z /= scale
    return z


def _order_nearest_neighbour(points):
    n = len(points)
    visited = np.zeros(n, dtype=bool)
    order = np.empty(n, dtype=int)

    order[0] = np.lexsort((points[:, 0], points[:, 1]))[0]
    visited[order[0]] = True

    for i in range(1, n):
        curr = points[order[i - 1]]
        dists = np.sum((points - curr) ** 2, axis=1)
        dists[visited] = np.inf
        order[i] = np.argmin(dists)
        visited[order[i]] = True

    return points[order]


def compute_dft(path):
    """
    complex DFT coefficients of a closed path sorted by magnitude.
    """
    N = len(path)
    raw = np.fft.fft(path) / N
    freqs = np.fft.fftfreq(N, d=1.0 / N).astype(int)

    dc_mask = freqs == 0
    other = ~dc_mask
    mag_order = np.argsort(-np.abs(raw[other]))

    return (
        np.concatenate([freqs[dc_mask], freqs[other][mag_order]]),
        np.concatenate([raw[dc_mask], raw[other][mag_order]]),
    )


def reconstruct_path(freqs, coeffs, n_components, n_points=500):
    t = np.linspace(0, 1, n_points, endpoint=False)
    z = np.zeros(n_points, dtype=complex)
    for i in range(min(n_components, len(freqs))):
        z += coeffs[i] * np.exp(2j * np.pi * freqs[i] * t)
    return z
