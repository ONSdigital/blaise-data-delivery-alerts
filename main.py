import os

import blaise_dds
from slack_sdk.webhook import WebhookClient
from termcolor import colored

from rules import should_alert
from utils import (
    build_slack_blocks,
    filter_batched_for_last_24_hours,
    format_line,
    format_state,
    parse_batch_date,
)


class DDAlerts:
    def __init__(self, dds_client, slack_webhook, concourse_build_url, ddm_base_url):
        self.client = dds_client
        self.slack_webhook = slack_webhook
        self.concourse_build_url = concourse_build_url
        self.ddm_base_url = ddm_base_url
        self.errors = {}
        self.successes = {}

    def get_details(self):
        successes = {}
        errors = {}
        batches = self.client.get_batches()

        filtered_batches = filter_batched_for_last_24_hours(batches)
        for batch in filtered_batches:
            batch_files = self.client.get_batch_states(batch)
            for batch_file in batch_files:
                errored_delivery, error_message = should_alert(batch_file)
                if errored_delivery:
                    if batch not in errors:
                        errors[batch] = []
                    error_files = errors[batch]
                    batch_file["error_message"] = error_message
                    error_files.append(batch_file)
                    errors[batch] = error_files
                else:
                    if batch not in successes:
                        successes[batch] = []
                    successful_files = successes[batch]
                    successful_files.append(batch_file)
                    successes[batch] = successful_files
        self.successes = successes
        self.errors = errors

    def print_report(self):
        report = format_line("Success report:")
        if len(self.successes) > 0:
            for batch, files in self.successes.items():
                report += format_line(f"{batch}:", 0)
                report += format_line(f"Date: {parse_batch_date(batch)}", 1)
                report += format_line(f"Count: {len(files)}", 1)
                report += format_line("Instruments:", 1)
                for file in files:
                    report += format_state(file, 2)
        else:
            report += format_line("Nothing to report", 1)
        print(colored(report, "green"))

        print("")
        error_report = format_line("Error report:")
        if len(self.errors) > 0:
            for batch, files in self.errors.items():
                error_report += format_line(f"{batch}:", 0)
                error_report += format_line(f"Date: {parse_batch_date(batch)}", 1)
                error_report += format_line(f"Count: {len(files)}", 1)
                error_report += format_line("Instruments:", 1)
                for file in files:
                    error_report += format_state(file, 2)
        else:
            error_report += format_line("Nothing to report", 1)
        print(colored(error_report, "red"))

    def backup_text(self):
        return (
            f"Data delivery errored, to see details go to: {self.concourse_build_url}"
        )

    def send_alert(self):
        if len(self.errors) == 0:
            return

        slack_blocks = build_slack_blocks(
            self.errors, f"{self.ddm_base_url}/batch", self.concourse_build_url
        )

        response = self.slack_webhook.send(
            text=self.backup_text(),
            blocks=slack_blocks["blocks"],
            attachments=slack_blocks["attachments"],
        )
        print(f"Slack webhook response status code: {response.status_code}")
        print(f"Slack webhook response body: {response.body}")

    def mark_alerted(self):
        for _, files in self.errors.items():
            for file in files:
                self.client.set_alerted(file["dd_filename"])

    def exit_code(self):
        if len(self.errors) >= 1:
            return 1
        return 0


webhook_url = os.getenv("SLACK_WEBHOOK")
ddm_base_url = os.getenv("DDM_URL")
concourse_build_url = os.getenv("CONCOURSE_BUILD_URL")

if None in [webhook_url, ddm_base_url, concourse_build_url]:
    print("Must provide SLACK_WEBHOOK, DDM_URL and CONCOURSE_BUILD_URL")
    exit(1)

assert webhook_url is not None
webhook = WebhookClient(webhook_url)


client = blaise_dds.Client(blaise_dds.Config.from_env())
dd_alerts = DDAlerts(client, webhook, concourse_build_url, ddm_base_url)  # type: ignore
dd_alerts.get_details()  # type: ignore
dd_alerts.print_report()  # type: ignore
dd_alerts.send_alert()  # type: ignore
dd_alerts.mark_alerted()  # type: ignore
exit(dd_alerts.exit_code())  # type: ignore
