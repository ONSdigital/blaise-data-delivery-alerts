# Blaise data delivery status alerts

An alert processor for data delivery status.

At the moment this tool is configured to find any issues with data delivery based on its status in the last 24 hours.

The rules are:

- Ignore any data delivery file that has already been alerted.
- Alert for any explicit errors
- Alert for "slow" runs - when a data delivery file has been stuck in a particular state for longer than expected.

## Config

| Key                 | Description                                                       |
|---------------------|-------------------------------------------------------------------|
| CONCOURSE_BUILD_URL | Used to provide a link to the concourse build in the slack alerts |
| DDM_URL             | Used to provide a link to DDM for any batches that contain errors |
| SLACK_WEBHOOK       | The slack webhook to send errors too                              |
| DDS_URL             | URL of DDS to get the status information from                     |
| CLIENT_ID           | DDS Client ID for authentication                                  |
