import abc
import sys
from typing import Any, Self, TYPE_CHECKING
from ctypes import (
    CDLL,
    c_void_p,
    c_int,
    c_char_p,
    c_bool,
    POINTER,
    pointer,
    Structure,
    c_uint8,
    _Pointer,
)


c_int_p = POINTER(c_int)

NUM_TRACKED_BITS = 18
NUM_COUNTERS = 2**NUM_TRACKED_BITS


class CaptureErrno:
    def __init__(self) -> None:
        self.err = c_int(0)
        self.errp = pointer(self.err)


class Closable(abc.ABC):
    @abc.abstractmethod
    def close(self) -> None: ...

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


class COUNTERS(Structure):
    _fields_ = [("counters", c_uint8 * NUM_COUNTERS)]

    def __str__(self) -> str:
        average = sum(self.counters) / NUM_COUNTERS
        count = sum(val != 0 for val in self.counters)
        return f"<COUNTERS count={count}/{NUM_COUNTERS}, avg={average}"


class GLOBALS(Structure):
    _fields_ = [
        ("counters", COUNTERS),
    ]


class INSTANCE(Structure):
    _fields_ = [
        ("path", c_char_p),
        ("counters", POINTER(COUNTERS)),
    ]


if TYPE_CHECKING:
    GLOBALS_P = _Pointer[GLOBALS]
    INSTANCE_P = _Pointer[INSTANCE]
else:
    GLOBALS_P = POINTER(GLOBALS)
    INSTANCE_P = POINTER(INSTANCE)


class Globals(CaptureErrno, Closable):
    def __init__(self, ptr: GLOBALS_P) -> None:
        super().__init__()
        self.ptr = ptr

    @classmethod
    def create(cls) -> Self:
        errp = pointer(c_int(0))
        ptr = _lib.fluxcov_init(errp)
        assert ptr is not None and errp.contents.value == 0
        return cls(ptr)

    def close(self) -> None:
        assert _lib.fluxcov_fini(self.ptr, self.errp) == 0
        assert self.err.value == 0

    def __str__(self) -> str:
        return str(self.ptr.contents.counters)


class Instance(CaptureErrno, Closable):
    def __init__(self, ptr: INSTANCE_P, path_ptr: c_char_p) -> None:
        super().__init__()
        self.ptr = ptr
        self.path_ptr = path_ptr

    @classmethod
    def create(cls, path: str) -> Self:
        errp = pointer(c_int(0))
        path_ptr = c_char_p(path.encode())
        ptr = _lib.fluxcov_start(path_ptr, errp)
        assert ptr is not None and errp.contents.value == 0
        return cls(ptr, path_ptr)

    def close(self) -> None:
        assert _lib.fluxcov_end(self.ptr, self.errp) == 0
        assert self.err.value == 0

    def check(self, globals: Globals) -> bool:
        res = _lib.fluxcov_check(globals.ptr, self.ptr, self.errp)
        assert self.err.value == 0
        return res

    def __str__(self) -> str:
        return str(self.ptr.contents.counters.contents)


def get_lib() -> CDLL:
    lib = CDLL("libfluxcov.so")
    signatures: dict[str, tuple[list[Any], Any]] = {
        "fluxcov_init": ([c_int_p], GLOBALS_P),
        "fluxcov_fini": ([GLOBALS_P, c_int_p], c_int),
        "fluxcov_start": ([c_char_p, c_int_p], INSTANCE_P),
        "fluxcov_check": ([GLOBALS_P, INSTANCE_P, c_int_p], c_bool),
        "fluxcov_end": ([INSTANCE_P, c_int_p], int),
    }
    for name, (args, res) in signatures.items():
        getattr(lib, name).argtypes = args
        getattr(lib, name).restype = res
    return lib


_lib = get_lib()
