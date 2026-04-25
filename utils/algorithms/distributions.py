# used by:
import numpy as np


def _normalize_counts(n_samples: int, n_clusters: int) -> np.ndarray:
    counts = np.full(n_clusters, n_samples // n_clusters, dtype=int)
    counts[: n_samples % n_clusters] += 1
    return counts


def sample_gaussian_blobs(
    n_samples: int = 300,
    centers: int | np.ndarray = 3,
    cluster_std=1.0,
    center_box=(-10.0, 10.0),
    random_state: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(random_state)

    if isinstance(centers, int):
        n_centers = centers
        centers_arr = rng.uniform(center_box[0], center_box[1], size=(n_centers, 2))
    else:
        centers_arr = np.asarray(centers, dtype=float)
        if centers_arr.ndim != 2 or centers_arr.shape[1] != 2:
            raise ValueError("centers must be an int or an array of shape (k, 2)")
        n_centers = centers_arr.shape[0]

    std_arr = np.asarray(cluster_std, dtype=float)
    if std_arr.ndim == 0:
        std_arr = np.full(n_centers, float(std_arr))
    elif std_arr.shape[0] != n_centers:
        raise ValueError("cluster_std length must match number of centers")

    counts = _normalize_counts(n_samples, n_centers)

    X_parts = []
    y_parts = []
    for k, (center, std, count) in enumerate(zip(centers_arr, std_arr, counts)):
        points = rng.normal(loc=center, scale=std, size=(count, 2))
        X_parts.append(points)
        y_parts.append(np.full(count, k, dtype=int))

    X = np.vstack(X_parts)
    y = np.concatenate(y_parts)

    perm = rng.permutation(n_samples)
    return X[perm], y[perm]


def two_moons(
    n_samples: int = 300,
    noise: float = 0.05,
    distance: float = 0.5,
    random_state: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    if distance <= 0:
        raise ValueError("distance must be > 0")

    rng = np.random.default_rng(random_state)
    counts = _normalize_counts(n_samples, 2)

    theta_outer = rng.uniform(0.0, np.pi, counts[0])
    theta_inner = rng.uniform(0.0, np.pi, counts[1])

    outer = np.column_stack([np.cos(theta_outer), np.sin(theta_outer)])
    inner = np.column_stack(
        [1.0 - np.cos(theta_inner), -np.sin(theta_inner) + distance]
    )

    X = np.vstack([outer, inner])
    y = np.concatenate([np.zeros(counts[0], dtype=int), np.ones(counts[1], dtype=int)])

    if noise > 0:
        X += rng.normal(0.0, noise, size=X.shape)

    perm = rng.permutation(n_samples)
    return X[perm], y[perm]


def sample_concentric_circles(
    n_samples: int = 300,
    noise: float = 0.05,
    factor: float = 0.5,
    random_state: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    if not (0.0 < factor < 1.0):
        raise ValueError("factor must be in (0, 1)")

    rng = np.random.default_rng(random_state)
    counts = _normalize_counts(n_samples, 2)

    t_outer = rng.uniform(0.0, 2.0 * np.pi, counts[0])
    t_inner = rng.uniform(0.0, 2.0 * np.pi, counts[1])

    outer = np.column_stack([np.cos(t_outer), np.sin(t_outer)])
    inner = factor * np.column_stack([np.cos(t_inner), np.sin(t_inner)])

    X = np.vstack([outer, inner])
    y = np.concatenate([np.zeros(counts[0], dtype=int), np.ones(counts[1], dtype=int)])

    if noise > 0:
        X += rng.normal(0.0, noise, size=X.shape)

    perm = rng.permutation(n_samples)
    return X[perm], y[perm]


def sample_anisotropic_blobs(
    n_samples: int = 300,
    centers: int | np.ndarray = 3,
    cluster_std: float | list[float] | tuple[float, ...] | np.ndarray = 1.0,
    linear_transform: np.ndarray | None = None,
    random_state: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    X, y = sample_gaussian_blobs(
        n_samples=n_samples,
        centers=centers,
        cluster_std=cluster_std,
        random_state=random_state,
    )

    if linear_transform is None:
        linear_transform = np.array([[0.6, -0.6], [-0.4, 0.8]], dtype=float)
    else:
        linear_transform = np.asarray(linear_transform, dtype=float)

    if linear_transform.shape != (2, 2):
        raise ValueError("linear_transform must have shape (2, 2)")

    return X @ linear_transform, y


def sample_varied_density_blobs(
    n_samples_per_cluster=(80, 160, 320),
    centers: np.ndarray | None = None,
    cluster_std=(0.35, 0.65, 1.2),
    random_state: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(random_state)
    counts = np.asarray(n_samples_per_cluster, dtype=int)
    if np.any(counts <= 0):
        raise ValueError("all n_samples_per_cluster values must be positive")

    k = len(counts)
    if len(cluster_std) != k:
        raise ValueError("cluster_std length must match n_samples_per_cluster length")

    if centers is None:
        centers = np.array([[-4.0, -1.0], [0.0, 3.0], [4.0, -2.0]], dtype=float)
    centers = np.asarray(centers, dtype=float)
    if centers.shape != (k, 2):
        raise ValueError("centers must have shape (k, 2)")

    X_parts = []
    y_parts = []
    for i in range(k):
        points = rng.normal(loc=centers[i], scale=cluster_std[i], size=(counts[i], 2))
        X_parts.append(points)
        y_parts.append(np.full(counts[i], i, dtype=int))

    X = np.vstack(X_parts)
    y = np.concatenate(y_parts)
    perm = rng.permutation(X.shape[0])
    return X[perm], y[perm]


def add_uniform_outliers(
    X: np.ndarray,
    y: np.ndarray,
    n_outliers: int = 30,
    padding: float = 0.5,
    random_state: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    if n_outliers <= 0:
        return X.copy(), y.copy()

    rng = np.random.default_rng(random_state)
    mins = X.min(axis=0)
    maxs = X.max(axis=0)
    span = maxs - mins
    low = mins - padding * span
    high = maxs + padding * span

    outliers = rng.uniform(low=low, high=high, size=(n_outliers, 2))
    X_aug = np.vstack([X, outliers])
    y_aug = np.concatenate([y, np.full(n_outliers, -1, dtype=int)])
    return X_aug, y_aug


def clustering_benchmark_suite(
    n_samples: int = 400,
    random_state: int | None = 42,
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    suite: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    suite["gaussian_blobs"] = sample_gaussian_blobs(
        n_samples=n_samples,
        centers=4,
        cluster_std=[0.4, 0.6, 0.8, 1.0],
        random_state=random_state,
    )
    suite["anisotropic_blobs"] = sample_anisotropic_blobs(
        n_samples=n_samples,
        centers=4,
        cluster_std=[0.5, 0.7, 0.8, 1.0],
        random_state=random_state,
    )
    suite["two_moons"] = two_moons(
        n_samples=n_samples,
        noise=0.06,
        random_state=random_state,
    )
    suite["concentric_circles"] = sample_concentric_circles(
        n_samples=n_samples,
        noise=0.04,
        factor=0.45,
        random_state=random_state,
    )

    varied = sample_varied_density_blobs(
        n_samples_per_cluster=(80, 120, 200),
        random_state=random_state,
    )
    suite["varied_density_blobs"] = add_uniform_outliers(
        varied[0],
        varied[1],
        n_outliers=max(10, n_samples // 20),
        random_state=random_state,
    )

    return suite
