# used by: cells\filter_chain\helpers.py, cells\filter_chain\plotting.py, cells\filter_chain\processing.py
import numpy as np


def apply_fourier_filter(samples, H_func):
    N = len(samples)
    spectrum = np.fft.rfft(samples)
    k = np.arange(len(spectrum))
    H = np.asarray(H_func(k), dtype=complex)
    return np.real(np.fft.irfft(spectrum * H, n=N))


def poly_ratio_H(p_coeffs, q_coeffs):
    def H(k):
        P = np.polyval(p_coeffs, k.astype(float))
        Q = np.polyval(q_coeffs, k.astype(float))
        Q = np.where(np.abs(Q) < 1e-12, 1e-12, Q)
        return P / Q

    return H


def rect_H(low, high):
    def H(k):
        return ((k >= low) & (k <= high)).astype(float)

    return H


def apply_convolution(samples, kernel):
    N = len(samples)
    kernel_padded = np.zeros(N)
    n = min(len(kernel), N)
    kernel_padded[:n] = kernel[:n]
    return np.real(np.fft.ifft(np.fft.fft(samples) * np.fft.fft(kernel_padded)))


def apply_transform(samples, expr):
    N = len(samples)
    ns = {
        "s": samples.copy(),
        "t": np.linspace(0, 1, N, endpoint=False),
        "np": np,
        "pi": np.pi,
        "sin": np.sin,
        "cos": np.cos,
        "abs": np.abs,
        "exp": np.exp,
        "log": np.log,
        "sqrt": np.sqrt,
        "sign": np.sign,
        "clip": np.clip,
    }
    result = eval(expr, {"__builtins__": {}}, ns)
    return np.asarray(result, dtype=float)


def eval_kernel(expr, N):
    t = np.linspace(0, 1, N, endpoint=False)
    n = np.arange(N)
    ns = {
        "t": t,
        "n": n,
        "N": N,
        "np": np,
        "pi": np.pi,
        "sin": np.sin,
        "cos": np.cos,
        "abs": np.abs,
        "exp": np.exp,
        "log": np.log,
        "sqrt": np.sqrt,
        "sign": np.sign,
    }
    kernel = eval(expr, {"__builtins__": {}}, ns)
    return np.asarray(kernel, dtype=float)


def eval_H_expr(expr, k):
    ns = {
        "k": k.astype(float),
        "np": np,
        "pi": np.pi,
        "sin": np.sin,
        "cos": np.cos,
        "abs": np.abs,
        "exp": np.exp,
        "log": np.log,
        "sqrt": np.sqrt,
        "sign": np.sign,
        "rect": lambda x: (np.abs(x) <= 0.5).astype(float),
    }
    return eval(expr, {"__builtins__": {}}, ns)
