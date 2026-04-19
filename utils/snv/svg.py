# used by: utils\snv\layout.py
SVG = {
    "R": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '  <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '    <line x1="0" y1="50" x2="20" y2="50"/>'
        '    <polyline points="20,50 25,38 35,62 45,38 55,62 65,38 75,62 80,50"/>'
        '    <line x1="80" y1="50" x2="100" y2="50"/>'
        "  </g>"
        "</svg>"
    ),
    "C": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '  <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '    <line x1="0" y1="50" x2="44" y2="50"/>'
        '    <line x1="44" y1="36" x2="44" y2="64"/>'
        '    <line x1="56" y1="36" x2="56" y2="64"/>'
        '    <line x1="56" y1="50" x2="100" y2="50"/>'
        "  </g>"
        "</svg>"
    ),
    "L": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '  <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '    <line x1="0" y1="50" x2="20" y2="50"/>'
        '    <path d="M20,50 C20,38 32,38 32,50 C32,38 44,38 44,50 C44,38 56,38 56,50 C56,38 68,38 68,50 C68,38 80,38 80,50"/>'
        '    <line x1="80" y1="50" x2="100" y2="50"/>'
        "  </g>"
        "</svg>"
    ),
    "D": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '  <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '    <line x1="0" y1="50" x2="33" y2="50"/>'
        '    <polygon points="33,38 67,50 33,62" fill="currentColor" stroke="none"/>'
        '    <line x1="67" y1="38" x2="67" y2="62"/>'
        '    <line x1="67" y1="50" x2="100" y2="50"/>'
        "  </g>"
        "</svg>"
    ),
    "VC": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '  <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '    <line x1="0" y1="50" x2="30" y2="50"/>'
        '    <circle cx="50" cy="50" r="16"/>'
        '    <line x1="70" y1="50" x2="100" y2="50"/>'
        '    <line x1="40" y1="50" x2="48" y2="50"/>'
        '    <line x1="44" y1="46" x2="44" y2="54"/>'
        '    <line x1="52" y1="50" x2="60" y2="50"/>'
        "  </g>"
        "</svg>"
    ),
    "CC": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '  <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '    <line x1="0" y1="50" x2="30" y2="50"/>'
        '    <circle cx="50" cy="50" r="16"/>'
        '    <line x1="70" y1="50" x2="100" y2="50"/>'
        '    <line x1="42" y1="50" x2="58" y2="50"/>'
        '    <polyline points="54,45 58,50 54,55"/>'
        "  </g>"
        "</svg>"
    ),
    "wire_straight": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '  <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
        '    <line x1="0" y1="50" x2="100" y2="50"/>'
        "  </g>"
        "</svg>"
    ),
    "wire_corner": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '  <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '    <polyline points="0,50 50,50 50,100"/>'
        "  </g>"
        "</svg>"
    ),
    "wire_tee": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '  <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
        '    <line x1="0" y1="50" x2="100" y2="50"/>'
        '    <line x1="50" y1="50" x2="50" y2="100"/>'
        "  </g>"
        "</svg>"
    ),
    "wire_cross": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '  <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
        '    <line x1="0" y1="50" x2="100" y2="50"/>'
        '    <line x1="50" y1="0" x2="50" y2="42"/>'
        '    <path d="M50,42 C56,42 56,58 50,58"/>'
        '    <line x1="50" y1="58" x2="50" y2="100"/>'
        "  </g>"
        "</svg>"
    ),
    "wire_cross_dot": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '  <g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
        '    <line x1="0" y1="50" x2="100" y2="50"/>'
        '    <line x1="50" y1="0" x2="50" y2="100"/>'
        '    <circle cx="50" cy="50" r="4" fill="currentColor" stroke="none"/>'
        "  </g>"
        "</svg>"
    ),
}
