<p align="center">
  <img src="./goose.png" width="200" />
</p>

# Goose, the git ops service.

[![Build Status](https://app.travis-ci.com/eBay/goose.svg?token=z1Gk7JJrpVngapauqquH&branch=main)](https://app.travis-ci.com/eBay/goose)
[![Known Vulnerabilities](https://snyk.io/test/github/ebay/goose/badge.svg)]

Goose is a tool which simplifies gitops by mapping between "files/file patterns
I care about" and "services that need to know about those changes".

- [Known Limitations](#known-limitations-currently)
- [Why?](#why)
- [How to use it](#how)
- [How to configure it](#config-file)
- [Backing service API contract](#service-provider-api)
- [FAQ](#faq)

## Known limitations currently

> ⚠ This repository is not "done" and is shared in the spirit of developing in
> the open. Provide feedback & get involved so we can shape this into something
> awesome.

Big things you probably care about:

1. [There is no auth mechanism between goose & the backing services.](https://github.com/eBay/goose/issues/1)
2. [The auth mechanism ^^ should ideally be pluggable to handle your systems' special auth requirements.](https://github.com/eBay/goose/issues/2)
3. [Support for regex matching](https://github.com/eBay/goose/issues/3)
4. [No way to limit which repositories a given hook runs for. It's either everyone or no one.](https://github.com/eBay/goose/issues/4)


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

The service sends events for both `VERIFY` actions, like when a pull request is
created, as well as `COMMIT` actions, which are when the change actually needs
to take place. For `VERIFY` actions, these will be represented in the PR status.

## How?

To get started, we need github credentials and a config file to tell goose what
it should do.

GitHub credentials can be either specified from environment variables
(`GITHUB_USERNAME`, `GITHUB_PASSWORD`), or goose will look in the contents of
`/etc/secrets/GITHUB_USERNAME` and `/etc/secrets/GITHUB_PASSWORD` for use with
kubernetes-oriented volume mounts.

Goose is built to run inside a docker container (or kubernetes pod), so it uses
Dockerfiles for setup & running. To pass in [a config file](#config-file), goose
looks at the `GOOSE_CONFIG` environment variable for a file location, defaulting
to `/etc/goose.yml`.

A simple, example Dockerfile might look like:

```dockerfile
FROM docker.io/ebay/goose:latest
COPY path/to/my/config.yml /etc/goose.yml
ENV GOOSE_CONFIG /etc/goose.yml # technically redundant since this is the default.
ENV GITHUB_USERNAME myusername
ENV GITHUB_PASSWORD very-secret
```


You can deploy that Dockerfile with your hosting provider and get honkin'.


For local setup instructions, check out [the contributing guide](./contributing.md)

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

When one of our repositories updates their `alarms.yaml` file, goose will fetch
the newest version of that file sent to the relevant url.

In the group permissions, goose sends over the old file (e.g. before the change
was made) in addition to the new one, if any `OWNERS.yaml` or `OWNERS.json`
files match in any folder.

This is the format of the config in this repository to get the functionality to
work.

```
name: A human-readable name for what the service does
owner: Contact information so we can track down the relevant owners.
url: The URL that will receive the request for processing the event.
filePatterns: (list of strings) files you're hoping to find. This supports both exact matches as well as glob patterns (including globstar support)
includeOld: boolean, default=false. Whether to send the previous version's file contents
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
  matchType: enum of EXACT_MATCH or GLOB_M`ATCH
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

## Does this help me get slack notifications or something?

Sorta! This really serves as an intermediate layer between git and the systems
you may have internally to accomplish such things. Goose needs a webservice on
the other side to talk with. The value proposition to those web services is that
they don't have to learn what a git repository is or convince developers to
setup yet another git hook.

So your alarms system team would integrate with goose. They would define a file
format that you should write and the file names that they'll pay attention
to. When you make those changes, goose will connect your commits with their
service.
