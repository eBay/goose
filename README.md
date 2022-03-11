<p align="center">
  <img src="./goose.png" width="200" />
</p>

# Goose, the git ops service.

[![Build Status](https://app.travis-ci.com/eBay/goose.svg?token=z1Gk7JJrpVngapauqquH&branch=main)](https://app.travis-ci.com/eBay/goose)

> ⚠ This repository is not "done" and is shared in the spirit of developing in
> the open. Provide feedback & get involved so we can shape this into something
> awesome.

Goose is a tool which simplifies gitops by mapping between "files/file patterns
I care about" and "services that need to know about those changes".

## Why?
We have found examples of services which require us to configure resources by
clicking around UIs. This suffers from an inability to review the work that's
done before it happens, making rollbacks more difficult and an inability to add
automated tooling around it. [GitOps](https://about.gitlab.com/topics/gitops/)
solves this.

There are some natural struggles for adopting a gitops-oriented approach. First,
services who want to offer gitops functionality would need to listen to
repository webhooks (which are a bit of a pain to setup, especially for every
repository). They'd also need to build functionality around checking out git
repositories, which significantly changes the scope of their existing APIs.

To provide an easier experience for both application developers and framework
teams, we're building an intermediary layer between the hooks that GitHub
provides and the services which want to know about the changes.

The end goal is you simply:
1. Add our webhook & github user to your org
2. Check in the relevant files
3. Profit!

The service sends events for both "VERIFY" actions, like when a pull request is
created, as well as "COMMIT" actions, which are when the change actually needs
to take place. For VERIFY actions, these will be represented in the PR status.

## How?

To get started, we need to build a config for when to call services and which
services those are. We'll also need some GitHub credentials to operate.

GitHub credentials can be either specified from environment variables
(`GITHUB_USERNAME`, `GITHUB_PASSWORD`), or goose will look in the contents of
`/etc/secrets/GITHUB_USERNAME` and `/etc/secrets/GITHUB_PASSWORD` for use with
k8s-oriented volume mounts.

To pass in a config file, goose looks at `GOOSE_CONFIG` for a file location,
defaulting to `/etc/goose.yml`.

A simple, example Dockerfile might look like:

```dockerfile
FROM hub.docker.io/ebay/goose:latest
COPY ./service-config.yml /etc/goose.yml
ENV GOOSE_CONFIG /etc/goose.yml
ENV GITHUB_USERNAME myusername
ENV GITHUB_PASSWORD very-secret
```

## Config File

The config file holds the mapping of the filenames/globs you care about
alongside the url you wish us to call. It also holds information so we can track
down who a particular endpoint belongs to.

Example:

```
- name: Alarm creation
  owner: vjay
  filePattern: alarms.yaml
  url: my-alarm-service.example.org/create-from-yaml

- name: Creation of group permissions
  owner: jabrahms
  filePattern: **/*/OWNERS.(json|yaml)
  includeOld: true
  url: identity-control.example.org/
```

When a given repository updates their `alarms.yaml` file, we get the newest
version of that file sent to the relevant url.

In the group permissions, we send over the old file in addition to the new one
and match `OWNERS.yaml` or `OWNERS.json` files in any folder.

This is the format of the config in this repository to get the functionality to
work.

```
name: A human-readable name for what the service does
owner: Contact information so we can track down the relevant owners.
url: The URL that will receive the request for processing the event.
filePatterns: (list of strings) files you're hoping to find. This supports both exact matches as well as glob patterns (including globstar support)
includeOld: boolean, default=false. Whether to send the old file contents in addition to the new file contents in the payload.
```

## Service Provider API

This is the data format we send to the upstream systems.

```
appId: name of app according to infohub
eventTimestamp: when the event source happened
source: Object
  uri: a URI to the resource in question
  sha: the commit id for this change for use as a unique identifier
type: enum of either VERIFY or COMMIT. Verify is for pre-flight checks like pull request validations
files: []File

File:
  filepath: full path to the file, relative to the repository root
  matchType: enum of EXACT_MATCH or GLOB_MATCH
  contents:
    new: (optional) string of file contents after change
    old: (optional) string of file contents before change
```

### Example
```json
{
    "appId": "jabrahms_goose",
    "eventTimestamp": "2021-12-28T11:14:37Z",
    "source": {
        "uri": "https://github-enterprise.example.com/...",
        "sha": "039282900a938e020c08320"
    },
    "type": "VERIFY",
    "files": [{
        "filepath": "alarms.yaml",
        "matchType": "EXACT_MATCH",
        "contents": {
            "new": "...contents here..."
        }
    }]
}
```

# FAQ

## Why goose?

It stands for GitOpsSErvice (or git oops service, if you prefer).
