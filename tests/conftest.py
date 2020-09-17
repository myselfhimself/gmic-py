# This hack prevents test-suites with only skipped tests to return an error exit code
# Per https://stackoverflow.com/a/32372274/420684
import pytest

TEST_RESULTS = []


@pytest.mark.tryfirst
def pytest_runtest_makereport(item, call, __multicall__):
    rep = __multicall__.execute()
    if rep.when == "call":
        TEST_RESULTS.append(rep.outcome)
    return rep


def pytest_sessionfinish(session, exitstatus):
    # Make test suites with nothing run (eg. all skipped) return a success status
    if TEST_RESULTS == []:
        session.exitstatus = 0
