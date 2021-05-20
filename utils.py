import pathlib
from datetime import datetime, timedelta

BLAISE_DST_SLACK_TAG = "<!subteam^S01QV7ZHSBG>"


def instrument_name(file_name):
    file_prefix = pathlib.Path(file_name).stem
    parsed_prefix = file_prefix.split("_")[1:]
    instrument_name = [
        instrument_name_part
        for instrument_name_part in parsed_prefix
        if not instrument_name_part.isnumeric()
    ]
    return "_".join(instrument_name).upper()


def parse_batch_date(batch_name):
    try:
        batch_without_prefix = "_".join(batch_name.split("_")[1:])
        return datetime.strptime(batch_without_prefix, "%d%m%Y_%H%M%S")
    except Exception:
        return datetime(1970, 1, 1)


def filter_batched_for_last_x(batches, time_filter):
    oldest_date = datetime.now() - time_filter
    return [batch for batch in batches if parse_batch_date(batch) >= oldest_date]


def filter_batched_for_last_24_hours(batches):
    return filter_batched_for_last_x(batches, timedelta(hours=24))


def format_line(text, indent=0):
    return f"{'    ' * indent}{text}\n"


def format_state(state_record, indent=0):
    formatted_state = format_line(
        f"{instrument_name(state_record['dd_filename']):}", indent
    )
    formatted_state += format_line(f"Alerted: {state_record['alerted']}", indent + 1)
    formatted_state += format_line(f"State: {state_record['state']}", indent + 1)
    formatted_state += format_line(
        f"Last updated: {state_record['updated_at']}", indent + 1
    )
    if "error_message" in state_record:
        formatted_state += format_line(
            f"Error: {state_record['error_message']}", indent + 1
        )
    return formatted_state


def batch_markdown(batch, count, ddm_link):
    return (
        f"*Batch*: {batch}\n"
        + f"*DDM*: {ddm_link}\n\n"
        + f"*Date*: {parse_batch_date(batch).isoformat()}\n"
        + f"*Error count*: {str(count)}"
    )


def file_markdown(file):
    return (
        f"*Instrument*: {instrument_name(file['dd_filename'])}\n"
        + f"*Batch*: {file['batch']}\n\n"
        + f"*State*: {file['state']}\n"
        + f"*Last updated*: {file['updated_at']}\n"
        + f"*Error*: {file['error_message']}"
    )


def slack_md_section(text):
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": text,
        },
    }


def build_slack_blocks(batches, ddm_batch_url, concourse_build_url):
    blocks = {"blocks": []}
    attachments = {"blocks": [], "color": "#900002"}

    header = {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": f"Data delivery error",
        },
    }
    concourse_section = slack_md_section(
        f"{BLAISE_DST_SLACK_TAG}\n", f"Concourse Build URL: <{concourse_build_url}>"
    )
    blocks["blocks"].append(header)
    blocks["blocks"].append(concourse_section)
    for batch, files in batches.items():
        section = slack_md_section(
            batch_markdown(batch, len(files), f"{ddm_batch_url}/{batch}")
        )
        blocks["blocks"].append(section)
        for file in files:
            section = slack_md_section(file_markdown(file))
            attachments["blocks"].append(section)
        blocks["blocks"].append({"type": "divider"})

    # blocks can be a maximum of 50, if its over
    # show the first 49 and a catch all error
    if len(attachments["blocks"]) >= 50:
        attachments["blocks"] = attachments["blocks"][:49]
        attachments["blocks"].append(
            slack_md_section(
                "Too many errors to display, "
                + "look in concourse build to see full details"
            )
        )

    blocks["blocks"].append(slack_md_section("*Additional Instrument Info*:"))
    blocks["attachments"] = [attachments]
    return blocks
