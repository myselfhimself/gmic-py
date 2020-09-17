# This hack prevents test-suites with only skipped tests to return an error exit code
# Per https://stackoverflow.com/a/32372274/420684
import pytest
from _pytest.config import ExitCode

TEST_RESULTS = []


@pytest.mark.tryfirst
def pytest_runtest_makereport(item, call, __multicall__):
    rep = __multicall__.execute()
    if rep.when == "call":
        TEST_RESULTS.append(rep.outcome)
    return rep


@pytest.hookimpl(hookwrapper=True)
def pytest_sessionfinish(session, exitstatus):
    outcome = yield
    # print(outcome.get_result())
    # print(exitstatus)
    # Make test suites with nothing run (eg. all skipped) return a success status
    if exitstatus == ExitCode.NO_TESTS_COLLECTED:
        session.exitstatus = 0
    else:
        session.exitstatus = exitstatus
