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

The service supports both "VERIFY" actions, like when a pull request is created,
as well as "COMMIT" actions, which are when the change actually needs to take
place. For VERIFY actions, these will be represented in the PR status.

## How?

Please open a pull request to the `service-config.yaml` file. In it, provide a
mapping of the filenames/globs you care about alongside the url you wish us to call.

Example:

```
- name: Alarm creation
  filePattern: alarms.yaml
  url: my-alarm-service.example.org/create-from-yaml

- name: Creation of group permissions
  filePattern: **/*/OWNERS.(json|yaml)
  includeOld: true
  url: identity-control.example.org/
```


When a given repository updates their `alarms.yaml` file, we get the newest
version of that file sent to the relevant url.

In the group permissions, we send over the old file in addition to the new one
and match `OWNERS.yaml` or `OWNERS.json` files in any folder.

## Config API

This is the format of the config in this repository to get the functionality to
work.

```
name: A human-readable name for what the service does
owner: An infohub id for your application so we can track down the relevant owners.
url: The URL that will receive the request for processing the event.
filePatterns: (list of strings) files you're hoping to find. This supports both exact matches as well as glob patterns (including globstar support)
includeOld: boolean, default=false. Whether to send the old file contents in addition to the new file contents in the payload.
```

### Example:

```yaml
name: alarms
owner: sherlockio
url: https://example.org/sherlock-metrics-bot/
filePatterns:
  - alarms.yaml
  - alarms.yml
```

## Service Provider API

This is the data format we send to the upstream systems.

```
appId: name of app according to infohub
eventTimestamp: when the event source happened
source: Object
  author: the person who performed the action
  uri: a URI to the resource in question
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
    "appId": "jabrahms_henrybot",
    "eventTimestamp": "2021-12-28T11:14:37Z",
    "source": {
        "author": "jabrahms",
        "uri": "https://github.corp.ebay.com/..."
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
