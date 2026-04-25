# used by:
import numpy as np


def _gauss_pdf(x, mu_k, sigma_k):
    d = x.shape[0]
    sigma_k_inv = np.linalg.inv(sigma_k)
    sigma_k_det = np.linalg.det(sigma_k)
    diff = x - mu_k
    mah_dist = np.dot(diff.T, np.dot(sigma_k_inv, diff))
    coeff = 1 / (np.sqrt((2 * np.pi) ** d * sigma_k_det))

    return coeff * np.exp(-0.5 * mah_dist)


def k_means(X, K=2, steps=20):
    rng = np.random.default_rng()
    centroids = rng.uniform(np.min(X, axis=0), np.max(X, axis=0), size=(K, X.shape[1]))
    X_c = np.column_stack((X, np.zeros(X.shape[0], dtype=int)))

    def step():
        for i, point in enumerate(X_c):
            smallest_distance = np.inf
            centroid_id = -1

            for ii, centroid in enumerate(centroids):
                d = np.sqrt(np.sum((point[:-1] - centroid) ** 2))
                if d < smallest_distance:
                    smallest_distance = d
                    centroid_id = ii

            X_c[i, -1] = centroid_id

        for iii in range(K):
            points_assigned = X_c[X_c[:, -1] == iii, :-1]
            if points_assigned.shape[0] > 0:
                centroids[iii] = np.mean(points_assigned, axis=0)

    for i in range(steps):
        step()
        yield X_c, centroids

    return X_c, centroids


def expect_max(X, K=2, steps=20):
    X = np.asarray(X, dtype=float)

    n_samples, n_features = X.shape

    rng = np.random.default_rng()
    replace = n_samples < K
    mean_indices = rng.choice(n_samples, size=K, replace=replace)
    means = X[mean_indices].copy()
    # theta is irrelevant, nur repr

    reg_eps = 1e-6
    base_covar = np.identity(n_features)
    covars = np.array([base_covar.copy() for _ in range(K)])
    weights = np.full(K, 1.0 / K)

    responsibilities = np.zeros((n_samples, K))

    for _ in range(steps):
        for i, x in enumerate(X):
            for k in range(K):
                responsibilities[i, k] = weights[k] * _gauss_pdf(x, means[k], covars[k])

        normalizer = responsibilities.sum(axis=1, keepdims=True)
        zero_mask = normalizer.squeeze() == 0
        if np.any(zero_mask):
            responsibilities[zero_mask] = 1.0 / K
            normalizer[zero_mask] = 1.0
        responsibilities /= normalizer

        n_k = responsibilities.sum(axis=0)
        n_k = np.maximum(n_k, reg_eps)
        weights = n_k / n_samples
        means = (responsibilities.T @ X) / n_k[:, None]

        for k in range(K):
            diff = X - means[k]
            weighted_diff = responsibilities[:, k][:, None] * diff
            covars[k] = (weighted_diff.T @ diff) / n_k[k] + reg_eps * np.eye(n_features)

        labels = np.argmax(responsibilities, axis=1).astype(int)
        X_c = np.column_stack((X, labels))
        theta = (means.copy(), covars.copy(), weights.copy())
        yield X_c, theta

    return X_c, theta
