from unittest import mock

import pytest
from freezegun import freeze_time

from rules import (
    should_alert,
    slow_process,
    slow_process_error,
    slow_seconds,
    state_error,
)


@freeze_time("2021-03-31 01:37:45")
def test_slow_process():
    state_record = {
        "alerted": False,
        "batch": "OPN_31032021_023139",
        "dd_filename": "dd_OPN2101A_31032021_023139.zip",
        "state": "generated",
        "updated_at": "2021-03-31T01:37:19+00:00",
    }
    slow_seconds = 300
    assert slow_process(state_record, slow_seconds) is False


@freeze_time("2021-03-31 02:45:45")
def test_slow_process_slow():
    state_record = {
        "alerted": False,
        "batch": "OPN_31032021_023139",
        "dd_filename": "dd_OPN2101A_31032021_023139.zip",
        "state": "generated",
        "updated_at": "2021-03-31T01:37:19+00:00",
    }
    slow_seconds = 300
    assert slow_process(state_record, slow_seconds) is True


@freeze_time("2021-03-31 02:45:45")
def test_slow_process_error():
    state_record = {
        "alerted": False,
        "batch": "OPN_31032021_023139",
        "dd_filename": "dd_OPN2101A_31032021_023139.zip",
        "state": "generated",
        "updated_at": "2021-03-31T01:37:19+00:00",
    }
    assert slow_process_error(state_record) == (
        "Instrument has been in state 'generated' for 1h:08m:26s - 4106 seconds total. "
        + "Slow error configuration is 300 seconds"
    )


@pytest.mark.parametrize(
    "state,expected_timeout",
    [
        ("started", 35 * 60),
        ("nifi_notified", 120 * 60),
        ("default", 5 * 60),
        ("foobar", 5 * 60),
    ],
)
def test_slow_seconds(state, expected_timeout):
    assert slow_seconds({"state": state}) == expected_timeout


def test_state_error():
    assert state_error({"error_info": "Big explosions"}) == "Big explosions"


def test_state_error_default():
    assert state_error({}) == "An unknown error occured"


@pytest.mark.parametrize(
    "state,alerted,slow,alert,error",
    [
        ("started", False, False, False, None),
        ("nifi_notified", False, True, True, "Slow process error"),
        ("errored", True, True, False, None),
        ("generated", False, True, True, "Slow process error"),
        ("errored", False, False, True, "An unknown error occured"),
    ],
)
@mock.patch("rules.slow_process_error")
def test_should_alert(mock_slow_process_error, state, alerted, slow, alert, error):
    mock_slow_process_error.return_value = "Slow process error"
    with mock.patch("rules.running_slow") as mock_running_slow:
        mock_running_slow.return_value = slow
        assert should_alert({"state": state, "alerted": alerted}) == (alert, error)
