import subprocess
import os
import pytest
from fluxcov.binding import Globals, Instance
from fluxcov.coverage import ELF, Coverage

SHM_PATH = "/shm_test"


def test_instance():
    with Globals.create() as globals:
        with Instance.create(SHM_PATH) as instance:
            assert not instance.check(globals)
            assert globals.ptr.contents.counters.sum() == 0
            assert globals.ptr.contents.counters.count() == 0


def test_max_global_value():
    with Globals.create() as globals:
        with Instance.create(SHM_PATH) as instance:
            assert not instance.check(globals)
            globals.ptr.contents.counters.counters[0] = 1
            instance.ptr.contents.counters.contents.counters[0] = 2
            assert not instance.check(globals)


def test_exclusion():
    with Instance.create(SHM_PATH):
        with pytest.raises(AssertionError):
            with Instance.create(SHM_PATH):
                pass


def test_shm_once():
    """
    First invocation of any application should always increase coverage.
    """
    with Globals.create() as globals:
        with Instance.create(SHM_PATH) as instance:
            subprocess.check_call(
                [
                    os.path.abspath("./bin/no_aslr.out"),
                    os.path.abspath("./bin/example_test.out"),
                ],
                env={
                    "LD_LIBRARY_PATH": os.path.abspath("./lib"),
                    "FLUXCOV_SHM": SHM_PATH,
                },
            )
            elf = ELF.from_path("./bin/example_test.out")
            cov_prev = Coverage(elf, globals.counters)
            assert not cov_prev.hits
            assert instance.check(globals)
            cov_after = Coverage(elf, globals.counters)
            assert cov_after.hits
            assert sum(cov_after.hits.values()) == globals.counters.sum()
            assert len(cov_after.hits) == globals.counters.count()


def test_shm_repeat():
    """
    Repeated invocation of the same pure application with the same parameters
    should not increase coverage.
    """
    with Globals.create() as globals:
        with Instance.create(SHM_PATH) as instance:
            subprocess.check_call(
                [
                    os.path.abspath("./bin/no_aslr.out"),
                    os.path.abspath("./bin/example_test.out"),
                ],
                env={
                    "LD_LIBRARY_PATH": os.path.abspath("./lib"),
                    "FLUXCOV_SHM": SHM_PATH,
                },
            )
            assert instance.check(globals)
            subprocess.check_call(
                [
                    os.path.abspath("./bin/no_aslr.out"),
                    os.path.abspath("./bin/example_test.out"),
                ],
                env={
                    "LD_LIBRARY_PATH": os.path.abspath("./lib"),
                    "FLUXCOV_SHM": SHM_PATH,
                },
            )
            assert not instance.check(globals)


def test_shm_branch():
    """
    Repeated invocation of the same application with the different paremeters
    is likely to increase coverage.
    """
    with Globals.create() as globals:
        with Instance.create(SHM_PATH) as instance:
            subprocess.check_call(
                [
                    os.path.abspath("./bin/no_aslr.out"),
                    os.path.abspath("./bin/example_branch.out"),
                ],
                env={
                    "LD_LIBRARY_PATH": os.path.abspath("./lib"),
                    "FLUXCOV_SHM": SHM_PATH,
                },
            )
            assert instance.check(globals)
            subprocess.check_call(
                [
                    os.path.abspath("./bin/no_aslr.out"),
                    os.path.abspath("./bin/example_branch.out"),
                    "args",
                ],
                env={
                    "LD_LIBRARY_PATH": os.path.abspath("./lib"),
                    "FLUXCOV_SHM": SHM_PATH,
                },
            )
            assert instance.check(globals)
            subprocess.check_call(
                [
                    os.path.abspath("./bin/no_aslr.out"),
                    os.path.abspath("./bin/example_branch.out"),
                    "args",
                ],
                env={
                    "LD_LIBRARY_PATH": os.path.abspath("./lib"),
                    "FLUXCOV_SHM": SHM_PATH,
                },
            )
            assert not instance.check(globals)


def test_filter():
    with Globals.create() as globals:
        with Instance.create(SHM_PATH) as instance:
            subprocess.check_call(
                [
                    os.path.abspath("./bin/no_aslr.out"),
                    os.path.abspath("./bin/example_test.out"),
                ],
                env={
                    "LD_LIBRARY_PATH": os.path.abspath("./lib"),
                    "FLUXCOV_SHM": SHM_PATH,
                    "FLUXCOV_FILTER": "invalid",
                },
            )
            assert not instance.check(globals)
            subprocess.check_call(
                [
                    os.path.abspath("./bin/no_aslr.out"),
                    os.path.abspath("./bin/example_test.out"),
                ],
                env={
                    "LD_LIBRARY_PATH": os.path.abspath("./lib"),
                    "FLUXCOV_SHM": SHM_PATH,
                    "FLUXCOV_FILTER": "example_test.out",
                },
            )
            assert instance.check(globals)
