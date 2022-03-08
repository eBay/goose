Ideally, this app will focus as a simple call & response style API. At a high
level, it looks like this.

[![](https://mermaid.ink/img/pako:eNqNkcFqwzAMhl9F-LqE3XMoBFqS41iuuai20hpiO5XlslD67rNLy0oP225G3_f7F-iidDCkGhXplMhr2lo8MLrRAyzIYrVd0At0gBE6K33av6K-oJ48r_sgr7AtsJ2RXRyIz1ZTMbp6s3nrG_j4hMCgg3P2luzzvMtj8sb6A0RBSRGm7Byf_v_besdbYx1_KkuobWDIIWCa6Vy2W3CdA5oK7AT0ZaPEorZZzcsNSWuKsWy4Yw78VP1A_6_-PfSw6qxtg88pVSlH7NCafJtL4aOSIzkaVZOfOUxRRjX6azbTYlBoZ6wEVs2Ec6RKYZIwrF6rRjjRQ7qf925dvwEUbq_R)](https://mermaid.live/edit#pako:eNqNkcFqwzAMhl9F-LqE3XMoBFqS41iuuai20hpiO5XlslD67rNLy0oP225G3_f7F-iidDCkGhXplMhr2lo8MLrRAyzIYrVd0At0gBE6K33av6K-oJ48r_sgr7AtsJ2RXRyIz1ZTMbp6s3nrG_j4hMCgg3P2luzzvMtj8sb6A0RBSRGm7Byf_v_besdbYx1_KkuobWDIIWCa6Vy2W3CdA5oK7AT0ZaPEorZZzcsNSWuKsWy4Yw78VP1A_6_-PfSw6qxtg88pVSlH7NCafJtL4aOSIzkaVZOfOUxRRjX6azbTYlBoZ6wEVs2Ec6RKYZIwrF6rRjjRQ7qf925dvwEUbq_R)

<!--
```mermaid
sequenceDiagram
  participant G as GitHub
  participant H as Goose
  participant A as AlarmsService
  G->>+H: PR or commit
  H->>G: Pending status for goose
  H->>G: Pending status for goose/alarms-service
  H->>A: Send relevant payload, if exists
  A->>H: Success or Error
  H->>G: Success status for goose/alarms-service
  H->>G: Success status for goose
  H->>-G: Done
```
-->

If there is an error, however, we need to be able to recover. Ideally, we'd do
this without having to maintain a database, because databases add a bunch of
infrastructure that's more difficult to maintain.

Errors may be:
1. Timeouts
2. Unable to get or parse GitHub's initial payload
3. Unexpected crash mid-process

For the timeout or crash case, the simplest solution is to allow users a
mechanism to retry. This means the first thing that should happen when we're
told about an event is to mark it as in-progress for the goose process using
the GitHub statuses API.

In order to retry, we can monitor comments to the pull request. If a user says
`retry $service`, then we can retry that particular service.

The failure to get the initial payload is a harder problem, however. One partial
solution is to monitor unhandled exceptions and manually (for now) redrive those
messages (eew). The solution to this problem is tracked in [#29](https://github.corp.ebay.com/jabrahms/goose/issues/29).
