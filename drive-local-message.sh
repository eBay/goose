#!/usr/bin/env bash
# Assumes you pass in an event type and a payload. Sends it to localhost.
EVENT=$1
PAYLOAD=$2

cat $PAYLOAD | http -v POST http://localhost:5000/webhook X-GitHub-Event:$EVENT
