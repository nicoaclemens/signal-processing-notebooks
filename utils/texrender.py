# used by: cells\filter_chain\helpers.py
import re


def parse_poly(text):
    try:
        return [float(x.strip()) for x in text.split(",") if x.strip()]
    except ValueError:
        return [1.0]


def poly_to_latex(text, var="k"):
    coeffs = parse_poly(text)
    n = len(coeffs) - 1
    if not coeffs:
        return "0"
    terms = []
    for i, c in enumerate(coeffs):
        deg = n - i
        if c == 0:
            continue
        abs_c = abs(c)
        sign = "-" if c < 0 else "+"
        if deg == 0:
            coeff_str = f"{abs_c:g}"
        elif deg == 1:
            coeff_str = var if abs_c == 1 else f"{abs_c:g}{var}"
        else:
            coeff_str = (
                f"{var}^{{{deg}}}" if abs_c == 1 else f"{abs_c:g}{var}^{{{deg}}}"
            )
        terms.append((sign, coeff_str))
    if not terms:
        return "0"
    parts = []
    for j, (sign, coeff_str) in enumerate(terms):
        if j == 0:
            parts.append(f"-{coeff_str}" if sign == "-" else coeff_str)
        else:
            parts.append(f" {sign} {coeff_str}")
    return "".join(parts)


def expr_to_latex(expr):
    s = expr.strip()
    s = s.replace("np.", "")
    s = re.sub(r"\*\*(\d+)", r"^{\1}", s)
    s = re.sub(r"\*\*\(([^)]+)\)", r"^{(\1)}", s)
    s = s.replace("*", r" \cdot ")
    s = re.sub(r"\brect\b", r"\\operatorname{rect}", s)
    s = re.sub(r"\bsign\b", r"\\operatorname{sign}", s)
    s = re.sub(r"\bclip\b", r"\\operatorname{clip}", s)
    s = re.sub(r"\babs\b", r"\\operatorname{abs}", s)
    s = re.sub(r"\bexp\b", r"\\exp", s)
    s = re.sub(r"\bsin\b", r"\\sin", s)
    s = re.sub(r"\bcos\b", r"\\cos", s)
    s = re.sub(r"\bsqrt\b", r"\\sqrt", s)
    s = re.sub(r"\blog\b", r"\\ln", s)
    s = re.sub(r"\bpi\b", r"\\pi", s)
    return s
