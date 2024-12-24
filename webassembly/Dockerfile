FROM python:3 AS downloader

RUN pip download --no-deps mabwiser==2.7.0

ENV ITUP1203_VERSION_TAG=1.9.5

RUN wget https://github.com/itu-p1203/itu-p1203/archive/refs/tags/v${ITUP1203_VERSION_TAG}.tar.gz && \
    tar -xf v${ITUP1203_VERSION_TAG}.tar.gz && \
    cd itu-p1203-${ITUP1203_VERSION_TAG} && \
    python -m pip install build && \
    python -m build

FROM nginx:alpine

ENV ITUP1203_VERSION_TAG=1.9.5

WORKDIR /var/www

ENV PYODIDE_VERSION_TAG=0.23.4

RUN wget https://github.com/pyodide/pyodide/releases/download/${PYODIDE_VERSION_TAG}/pyodide-${PYODIDE_VERSION_TAG}.tar.bz2 && \
    tar -xf pyodide-${PYODIDE_VERSION_TAG}.tar.bz2 && \
    rm pyodide-${PYODIDE_VERSION_TAG}.tar.bz2

COPY --from=downloader /mabwiser-2.7.0-py3-none-any.whl /var/www/pyodide
COPY --from=downloader /itu-p1203-${ITUP1203_VERSION_TAG}/dist/itu_p1203-${ITUP1203_VERSION_TAG}-py3-none-any.whl /var/www/pyodide

COPY nginx.conf /etc/nginx/conf.d/default.conf
