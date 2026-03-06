import subprocess
import os
from fluxcov.binding import Globals, Instance
from fluxcov.coverage import ELF, Coverage
from fluxcov.bench import Bench

SHM_PATH = "/shm_test"


def test_instance():
    with Bench(
            ELF.from_path("./bin/example_test.out"),
            SHM_PATH,
            ) as bench:
        assert not bench.check()


def test_shm_once():
    """
    First invocation of any application should always increase coverage.
    """
    with Bench(
            ELF.from_path("./bin/example_test.out"),
            SHM_PATH,
            ) as bench:
        with bench.context() as context:
            subprocess.check_call(
                [
                    os.path.abspath("./bin/no_aslr.out"),
                    os.path.abspath("./bin/example_test.out"),
                ],
                env={
                    "LD_LIBRARY_PATH": os.path.abspath("./lib"),
                    "FLUXCOV_SHM": SHM_PATH,
                }
            )
            assert bench.check()

        assert not context.cov_prev.hits
        assert context.cov_after.hits
        assert context.cov_cur.hits


def test_shm_repeat():
    """
    Repeated invocation of the same pure application with the same parameters
    should not increase coverage.
    """
    with Bench(
            ELF.from_path("./bin/example_test.out"),
            SHM_PATH,
            ) as bench:
        with bench.context() as context1:
            subprocess.check_call(
                [
                    os.path.abspath("./bin/no_aslr.out"),
                    os.path.abspath("./bin/example_test.out"),
                ],
                env={
                    "LD_LIBRARY_PATH": os.path.abspath("./lib"),
                    "FLUXCOV_SHM": SHM_PATH,
                }
            )
            assert bench.check()
        with bench.context() as context2:
            subprocess.check_call(
                [
                    os.path.abspath("./bin/no_aslr.out"),
                    os.path.abspath("./bin/example_test.out"),
                ],
                env={
                    "LD_LIBRARY_PATH": os.path.abspath("./lib"),
                    "FLUXCOV_SHM": SHM_PATH,
                }
            )
            assert not bench.check()
        assert context1.cov_after.hits == context2.cov_after.hits


def test_shm_branch():
    """
    Repeated invocation of the same application with the different paremeters
    is likely to increase coverage.
    """
    with Bench(
            ELF.from_path("./bin/example_branch.out"),
            SHM_PATH,
            ) as bench:
        with bench.context() as context1:
            subprocess.check_call(
                [
                    os.path.abspath("./bin/no_aslr.out"),
                    os.path.abspath("./bin/example_branch.out"),
                ],
                env={
                    "LD_LIBRARY_PATH": os.path.abspath("./lib"),
                    "FLUXCOV_SHM": SHM_PATH,
                }
            )
            assert bench.check()
        with bench.context() as context2:
            subprocess.check_call(
                [
                    os.path.abspath("./bin/no_aslr.out"),
                    os.path.abspath("./bin/example_branch.out"),
                    "args",
                ],
                env={
                    "LD_LIBRARY_PATH": os.path.abspath("./lib"),
                    "FLUXCOV_SHM": SHM_PATH,
                }
            )
            assert bench.check()
        with bench.context() as context3:
            subprocess.check_call(
                [
                    os.path.abspath("./bin/no_aslr.out"),
                    os.path.abspath("./bin/example_branch.out"),
                    "args",
                ],
                env={
                    "LD_LIBRARY_PATH": os.path.abspath("./lib"),
                    "FLUXCOV_SHM": SHM_PATH,
                }
            )
            assert not bench.check()
        assert context1.cov_after.hits != context2.cov_after.hits
        assert context2.cov_after.hits == context3.cov_after.hits
        assert len(context2.cov_after.hits) == len(bench.elf.buckets)


def test_filter():
    with Bench(
            ELF.from_path("./bin/example_test.out"),
            SHM_PATH,
            ) as bench:
        with bench.context() as context1:
            subprocess.check_call(
                [
                    os.path.abspath("./bin/no_aslr.out"),
                    os.path.abspath("./bin/example_test.out"),
                ],
                env={
                    "LD_LIBRARY_PATH": os.path.abspath("./lib"),
                    "FLUXCOV_SHM": SHM_PATH,
                    "FLUXCOV_FILTER": "invalid",
                }
            )
            assert not bench.check()
        assert not context1.cov_after.hits
        with bench.context() as context2:
            subprocess.check_call(
                [
                    os.path.abspath("./bin/no_aslr.out"),
                    os.path.abspath("./bin/example_test.out"),
                ],
                env={
                    "LD_LIBRARY_PATH": os.path.abspath("./lib"),
                    "FLUXCOV_SHM": SHM_PATH,
                    "FLUXCOV_FILTER": "example_test.out",
                }
            )
            assert bench.check()
        assert context2.cov_after.hits
