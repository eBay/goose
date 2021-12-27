# Henrybot, the github event dispatcher

![](./henrybot.png)

Henrybot is a tool which simplifies gitops by using offering a mapping between
"file globs I care about" and "service to call with those files".

## Why?
Internally, there are several places where we need to configure resources by
clicking around UIs, such as alarms. This suffers from an inability to review
the work that's done before it happens, making rollbacks more difficult and an
inability to add automated tooling around
it. [GitOps](https://about.gitlab.com/topics/gitops/) solves this.

There are some natural struggles for adopting a gitops-oriented approach. First,
services like our alarm service would need to listen to repository webhooks
(which are a bit of a pain to setup, especially for every repository). They'd
also need to build functionality around checking out git repositories, which
significantly changes the scope of their existing APIs.

To provide an easier experience for both application developers and framework
teams, we're building an intermediary layer between the hooks that GitHub
provides and the services which want to know about the changes.

The end goal is you simply:
1. Add our gitops user to your org
2. Check in the relevant files
3. Profit!

## How?

Please open a pull request to the `service-config.yaml` file. In it, provide a
mapping of the filenames/globs you care about alongside the url you wish us to call.

Example:

```
- name: Alarm creation
  filename: alarms.yaml
  url: my-alarm-service.example.org/create-from-yaml

- name: Creation of group permissions
  glob: **/*/OWNERS.yaml
  includeOld: true
  url: identity-control.example.org/
```


When a given repository updates their `alarms.yaml` file, we get the newest
version of that file sent to the relevant url.

In the group permissions, we send over the old file in addition to the new one
and match `OWNERS.yaml` files in any folder.

## Config API

@@@ TODO

## Service Provider API

This is the data format we send to the upstream systems.

@@@ TODO
