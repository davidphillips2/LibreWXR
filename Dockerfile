FROM python:3.12-slim

WORKDIR /app

# FFTW3 shared libraries that pyfftw binds to.  pysteps S-PROG uses
# pyfftw for the spectral cascade FFTs when available and falls back
# to numpy FFT otherwise (~2-3× slower).  Debian 13 (trixie, which
# python:3.12-slim now tracks) replaced the meta-package libfftw3-3
# with per-precision packages — double-precision is the one S-PROG
# actually uses; single-precision is installed too so pyfftw's import
# probe for ``libfftw3f.so.3`` succeeds cleanly.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libfftw3-double3 libfftw3-single3 \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir .

EXPOSE 8080

CMD ["python", "-m", "librewxr.main"]
