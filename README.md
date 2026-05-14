# Signal Processing Notebooks

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg?style=flat-square)](https://github.com/prettier/prettier) [![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)

## How to use

```bash
git clone https://github.com/NicoaClemens/Signal-Processing-Notebooks.git
cd Signal-Processing-Notebooks
python -m venv venv
# win
.\venv\Scripts\activate
.\run
# linux macos
source venv/bin/activate
./run.sh
```

## Read-only Web Mode (Uberspace)

```bash
source venv/bin/activate
./run-web-readonly.sh
```

Notes:
- This launcher is Uberspace-targeted and intentionally has no fallback mode.
- It requires `bwrap` to already be available on the host.
- The host filesystem is mounted read-only for the Jupyter process.
- Jupyter runtime/config/cache paths are redirected to tmpfs, so session changes are not persisted to disk.


## Contributing

no

## LICENSE

All rights reserved
