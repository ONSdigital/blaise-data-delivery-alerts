# Blaise Data Delivery Alerts

Queries the Data Delivery Status (DDS) API to fetch the status of all data delivery files from the last 24 hours. It then processes each file against a set of rules to identify errors or significant delays. If an issue is found, a formatted alert is sent to a configured Slack channel.

## Alerting Rules

An alert is triggered for a data delivery file if any of the following conditions are met:

- **The file is in an `errored` state.** The specific error information from DDS will be included in the alert.
- **The file processing is running slow.** A file is considered slow if it remains in a specific state for longer than the configured threshold.

The following files are **ignored** and will not trigger an alert:
- Files that have already been alerted for.
- Files in a complete state (`inactive`, `in_arc`).

### Slow Run Thresholds

The time allowed for a file to be in a given state before it is considered "slow" is defined as follows:

| State         | Allowed Time |
|---------------|--------------|
| `started`     | 35 minutes   |
| `nifi_notified` | 120 minutes  |
| (any other)   | 5 minutes    |

## Configuration

The application is configured via the following environment variables:

| Variable            | Description                                                       |
|---------------------|-------------------------------------------------------------------|
| `CONCOURSE_BUILD_URL` | A link to the concourse build, included in the Slack alert.       |
| `DDM_URL`             | The base URL for the Data Delivery Manager (DDM) UI.              |
| `SLACK_WEBHOOK`       | The Slack webhook URL to which alerts will be sent.               |
| `DDS_URL`             | The URL of the Data Delivery Status (DDS) API.                    |
| `CLIENT_ID`           | The Client ID for authenticating with the DDS API.                |
