from datetime import datetime, timedelta

import pytz

ALLOWED_AGE_PER_STATUS = {
    "default": 5 * 60,
    # LMS instruments can take a very long time to generate when the SPS is not cached
    "started": 35 * 60,
    "nifi_notified": 120 * 60,
}

COMPLETE_STATES = ["inactive", "in_arc"]


def slow_process(state_record, slow_seconds):
    oldest_time = datetime.now(pytz.UTC) - timedelta(seconds=slow_seconds)
    return datetime.fromisoformat(state_record["updated_at"]) < oldest_time


def slow_process_error(state_record):
    total_seconds = int(
        (
            datetime.now(pytz.UTC) - datetime.fromisoformat(state_record["updated_at"])
        ).total_seconds()
    )
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return (
        f"Instrument has been in state '{state_record['state']}' for {hours:d}h:{minutes:02d}m:{seconds:02d}s - {total_seconds} "
        + f"seconds total. Slow error configuration is {slow_seconds(state_record)} seconds"
    )


def running_slow(state_record):
    return slow_process(state_record, slow_seconds(state_record))


def slow_seconds(state_record):
    current_state = state_record["state"]
    if current_state in ALLOWED_AGE_PER_STATUS:
        return ALLOWED_AGE_PER_STATUS[current_state]
    return ALLOWED_AGE_PER_STATUS["default"]


def state_error(state_record):
    if "error_info" in state_record:
        return state_record["error_info"]
    return "An unknown error occured"


def should_alert(state_record):
    if state_record["alerted"]:
        return False, None
    if state_record["state"] in COMPLETE_STATES:
        return False, None
    if state_record["state"] == "errored":
        return True, state_error(state_record)
    if running_slow(state_record):
        return True, slow_process_error(state_record)
    return False, None
