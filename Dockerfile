FROM alpine:3.7 as base

# TODO: Fix this. I can't use this hardened image due to SSL issues, it seems
# FROM hub.tess.io/tess/alpine:hardened

WORKDIR /usr/src/app

RUN apk add --no-cache python3 git
RUN pip3 install \
    --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org \
    --upgrade pip

COPY . .
RUN pip3 install \
    --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org \
    --no-cache-dir -r requirements.txt

FROM base as test
RUN pip3 install \
    --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org \
    --no-cache-dir -r requirements.dev.txt
CMD ["pytest", "-v", \
    "--cov=.", "--cov-branch", "--cov-report=term-missing", "--cov-fail-under=100", "--durations=0", \
    "."]

FROM base as production
EXPOSE 3001

CMD ["hypercorn", \
    "--bind", "0.0.0.0:3001", \
    # "--error-log", "-", \
    # "--access-log", "-", \
    "--debug", \
    "web_service:app"]
