FROM alpine:3.7

# TODO: Fix this. I can't use this hardened image due to SSL issues, it seems
# FROM hub.tess.io/tess/alpine:hardened


EXPOSE 3001
WORKDIR /usr/src/app


RUN apk add --no-cache python3 git
RUN pip3 install \
    --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org \
    --upgrade pip

COPY . .
RUN pip3 install \
    --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org \
    --no-cache-dir -r requirements.txt

CMD ["hypercorn", \
    "--bind", "0.0.0.0:3001", \
    # "--error-log", "-", \
    # "--access-log", "-", \
    "--debug", \
    "web_service:app"]
