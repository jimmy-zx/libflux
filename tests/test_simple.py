import subprocess
import os
from fluxcov import Globals, Instance

SHM_PATH = "/shm_test"


def test_instance():
    with Globals.create() as globals:
        with Instance.create(SHM_PATH) as instance:
            assert not instance.check(globals)


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
                }
            )
            assert instance.check(globals)


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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
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
                }
            )
            assert instance.check(globals)
