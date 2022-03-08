FROM hub.tess.io/tess/alpine:hardened as base

WORKDIR /usr/src/app
RUN echo "@edge http://nl.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories
RUN apk add --no-cache python3 git@edge py3-pip

RUN pip3 install \
    --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org \
    --upgrade pip

COPY . .
RUN git log --pretty=oneline --max-count 1 > git-info.txt
RUN rm -rf .git/

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
    "goose.web_service:app"]
