from datetime import datetime, timedelta

from freezegun import freeze_time

from utils import (
    batch_markdown,
    file_markdown,
    filter_batched_for_last_24_hours,
    filter_batched_for_last_x,
    format_line,
    format_state,
    instrument_name,
    parse_batch_date,
    slack_md_section,
)


def test_instrument_name():
    dd_filename = "dd_OPN2101A_31032021_023139.zip"
    assert instrument_name(dd_filename) == "OPN2101A"


def test_parse_batch_date():
    assert parse_batch_date("OPN_31032021_023139") == datetime(2021, 3, 31, 2, 31, 39)


def test_parse_batch_date_invalid():
    assert parse_batch_date("foobar") == datetime(1970, 1, 1)


@freeze_time("2021-05-18 12:00:00")
def test_filter_batched_for_last_x():
    batches = [
        "OPN_31032021_023139",
        "OPN_09042021_113134",
        "LMS_06052021_043156",
        "OPN_01042021_113156",
        "OPN_30042021_023149",
        "OPN_29032021_113154",
        "OPN_07042021_023203",
        "OPN_26032021_093144",
        "OPN_18052021_113106",
    ]
    assert filter_batched_for_last_x(batches, timedelta(hours=24)) == [
        "OPN_18052021_113106"
    ]
    assert filter_batched_for_last_x(batches, timedelta(days=30)) == [
        "LMS_06052021_043156",
        "OPN_30042021_023149",
        "OPN_18052021_113106",
    ]
    assert filter_batched_for_last_x(batches, timedelta(seconds=30)) == []


@freeze_time("2021-05-18 12:00:00")
def test_filter_batched_for_last_24_hours():
    batches = [
        "OPN_31032021_023139",
        "OPN_09042021_113134",
        "LMS_06052021_043156",
        "OPN_01042021_113156",
        "OPN_30042021_023149",
        "OPN_29032021_113154",
        "OPN_07042021_023203",
        "OPN_26032021_093144",
        "OPN_18052021_113106",
    ]
    assert filter_batched_for_last_24_hours(batches) == ["OPN_18052021_113106"]


def test_format_line():
    assert format_line("foobar", 0) == "foobar\n"
    assert format_line("foobar", 1) == "    foobar\n"
    assert format_line("foobar", 2) == "        foobar\n"


def test_format_state_with_error():
    assert (
        format_state(
            {
                "alerted": False,
                "batch": "OPN_31032021_023139",
                "dd_filename": "dd_OPN2101A_31032021_023139.zip",
                "state": "generated",
                "updated_at": "2021-03-31T01:37:19+00:00",
                "error_message": "Test error",
            }
        )
        == """OPN2101A
    Alerted: False
    State: generated
    Last updated: 2021-03-31T01:37:19+00:00
    Error: Test error
"""
    )


def test_format_state_without_error():
    assert (
        format_state(
            {
                "alerted": False,
                "batch": "OPN_31032021_023139",
                "dd_filename": "dd_OPN2101A_31032021_023139.zip",
                "state": "generated",
                "updated_at": "2021-03-31T01:37:19+00:00",
            }
        )
        == """OPN2101A
    Alerted: False
    State: generated
    Last updated: 2021-03-31T01:37:19+00:00
"""
    )


def test_batch_markdown():
    ddm_link = "https://test_ddm_link.com"
    error_count = 2
    batch = "OPN_30042021_023149"
    assert (
        batch_markdown(batch, error_count, ddm_link)
        == """*Batch*: OPN_30042021_023149
*DDM*: https://test_ddm_link.com

*Date*: 2021-04-30T02:31:49
*Error count*: 2"""
    )


def test_file_markdown():
    assert (
        file_markdown(
            {
                "alerted": False,
                "batch": "OPN_31032021_023139",
                "dd_filename": "dd_OPN2101A_31032021_023139.zip",
                "state": "generated",
                "updated_at": "2021-03-31T01:37:19+00:00",
                "error_message": "Test error",
            }
        )
        == """*Instrument*: OPN2101A
*Batch*: OPN_31032021_023139

*State*: generated
*Last updated*: 2021-03-31T01:37:19+00:00
*Error*: Test error"""
    )


def test_slack_md_section():
    assert slack_md_section("foobar") == {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "foobar",
        },
    }
