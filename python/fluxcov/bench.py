from typing import Self
from fluxcov.coverage import ELF, Coverage
from fluxcov.binding import Closable, Globals, Instance


class Bench(Closable):
    def __init__(self, elf: ELF | None, shm_path: str) -> None:
        self.elf = elf
        self.shm_path = shm_path
        self.globals = Globals.create()
        self.instance = Instance.create(shm_path)

    def close(self) -> None:
        self.globals.close()
        self.instance.close()

    def check(self) -> bool:
        return self.instance.check(self.globals)

    def context(self, **kwargs) -> "BenchContext":
        assert self.elf is not None
        return BenchContext(self, **kwargs)


class BenchContext(Closable):
    def __init__(self, bench: Bench, full: bool = False) -> None:
        assert bench.elf is not None
        self.bench = bench
        self.full = full
        self.cov_prev: Coverage | None = None
        self.cov_after: Coverage | None = None
        self.cov_cur: Coverage | None = None

    def __enter__(self) -> Self:
        if self.full:
            self.cov_prev = Coverage(self.bench.elf, self.bench.globals.counters)
        return self

    def close(self) -> None:
        self.cov_after = Coverage(self.bench.elf, self.bench.globals.counters)
        if self.full:
            self.cov_cur = Coverage(self.bench.elf, self.bench.instance.counters)
