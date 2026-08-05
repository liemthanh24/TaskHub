import logging

from app.core.logging import RequestIdFilter, request_id_var, setup_logging


def test_request_id_default_is_dash():
    assert request_id_var.get() == "-"


def test_request_id_var_set_and_reset():
    token = request_id_var.set("REQ-123")
    assert request_id_var.get() == "REQ-123"
    request_id_var.reset(token)
    assert request_id_var.get() == "-"


def test_filter_attaches_request_id():
    filter_ = RequestIdFilter()
    record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
    assert filter_.filter(record) is True
    assert record.request_id == "-"

    token = request_id_var.set("REQ-456")
    try:
        record2 = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
        filter_.filter(record2)
        assert record2.request_id == "REQ-456"
    finally:
        request_id_var.reset(token)


def test_setup_logging_format_contains_request_id():
    setup_logging()
    root = logging.getLogger()
    assert root.handlers
    fmt = root.handlers[0].formatter._fmt
    assert "%(request_id)s" in fmt
