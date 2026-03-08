import argparse
import io
import os
import pickle
import hashlib
import lief
from capstone import Cs, CsInsn, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86Op, X86_OP_IMM
from elftools.elf.elffile import ELFFile

from fluxcov.binding import NUM_TRACKED_BITS


class ELF:
    def __init__(
        self,
        data: bytes,
        symbol: str = "__sanitizer_cov_trace_pc",
        num_tracked_bits: int = NUM_TRACKED_BITS,
        path: bool = False,
    ) -> None:
        self.data = data
        self.symbol = symbol
        self.num_tracked_bits = num_tracked_bits
        assert not path

        self.imm_calls = self.get_imm_calls_for_elf()
        self.plt_table = self.get_plt_table()
        self.call_sites = self.collect_call_sites_for_symbol(symbol=symbol)
        self.buckets = self.bucket_to_pcs()

    @classmethod
    def from_path(cls, path: str) -> "ELF":
        with open(path, "rb") as fp:
            return cls(fp.read())

    def get_imm_calls_for_elf(self) -> list[tuple[int, int]]:
        stream = io.BytesIO(self.data)
        elf = ELFFile(stream)
        text = elf.get_section_by_name(".text")
        code = text.data()
        addr = text["sh_addr"]

        md = Cs(CS_ARCH_X86, CS_MODE_64)
        md.detail = True

        i: CsInsn
        calls: list[tuple[str, str]] = []
        for i in md.disasm(code, addr):
            if i.mnemonic == "call":
                if len(i.operands) != 1:
                    continue
                op: X86Op = i.operands[0]
                if op.type != X86_OP_IMM:
                    continue
                # deemed return addr, target
                calls.append((i.address + i.size, op.imm))
        return calls

    def get_plt_table(self) -> dict[int, str]:
        elf = lief.parse(self.data)
        plt = elf.get_section(".plt")
        stub_size = 0x10

        if (plt_sec := elf.get_section(".plt.sec")) is not None:
            # split CET PLT, not tested
            stub0 = plt_sec.virtual_address
        elif bytes(plt.content).startswith(b"\xf3\x0f\x1e\xfa\x41\x53"):
            # CET/IBT compact layout
            stub0 = plt.virtual_address + 0x20
        else:
            stub0 = plt.virtual_address + 0x10

        relocs: dict[int, str] = {}
        for idx, rel in enumerate(elf.pltgot_relocations):
            relocs[stub0 + idx * stub_size] = rel.symbol.name
        return relocs

    def collect_call_sites_for_symbol(
        self,
        symbol: str = "__sanitizer_cov_trace_pc",
    ) -> list[int]:
        calls: list[int] = []
        for addr, imm in self.imm_calls:
            if imm not in self.plt_table:
                continue
            if self.plt_table[imm] != symbol:
                continue
            calls.append(addr)
        return calls

    def pc_to_bucket(self, pc: int) -> int:
        return pc & ((1 << self.num_tracked_bits) - 1)

    def bucket_to_pcs(self) -> dict[int, list[int]]:
        buckets: dict[int, list[int]] = {}
        for pc in self.call_sites:
            bucket = self.pc_to_bucket(pc)
            buckets[bucket] = buckets.get(bucket, []) + [pc]
        return buckets


class Coverage:
    def __init__(self, elf: ELF, dump: list[int], no_check: bool = False) -> None:
        self.elf = elf
        self.dump = dump

        self.hits: dict[int, int] = {}
        for bucket, count in enumerate(self.dump):
            if count != 0:
                self.hits[bucket] = count

        assert no_check or not self.validate()

    def validate(self) -> list[int]:
        invalid: list[int] = []
        for bucket in self.hits:
            if bucket not in self.elf.buckets:
                invalid.append(bucket)
        return invalid


class ELFCache:
    def __init__(self, cache_path: str) -> None:
        self.cache_path = cache_path

    def get_path(self, digest: str) -> str:
        return os.path.join(self.cache_path, f"{digest}.coverage_pickle")

    def get(self, elf_path: str) -> ELF:
        with open(elf_path, "rb") as fp:
            data = fp.read()
        digest = hashlib.sha256(data).hexdigest()
        path = self.get_path(digest)
        if os.path.isfile(path):
            with open(path, "rb") as fp:
                obj = pickle.load(fp)
            assert isinstance(obj, ELF)
        else:
            obj = ELF(data)
            if not os.path.exists(self.cache_path):
                os.makedirs(os.path.abspath(self.cache_path))
            with open(path, "wb") as fp:
                pickle.dump(obj, fp)
        return obj


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("elf", type=str)
    parser.add_argument("-d", "--dump", type=str)
    parser.add_argument("--cache", type=str, default="cache")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    cache = ELFCache(args.cache)
    elf = cache.get(args.elf)

    dump: list[int] = []
    if args.dump:
        with open(args.dump, "rb") as fp:
            dump = list(fp.read())

    coverage = Coverage(elf, dump)

    if args.verbose:
        for bucket, pcs in elf.buckets.items():
            if (count := coverage.hits.get(bucket, 0)) != 0:
                print(f"Bucket {hex(bucket)} ->", end=" ")
                print(",".join(hex(pc) for pc in pcs), end=" ")
                print(count)
        print()

    conflicts = len([k for k, v in elf.buckets.items() if len(v) > 1])
    print(f"Coverage: {len(coverage.hits) / len(elf.buckets) * 100}%")
    print(f"Usage: {len(elf.buckets) / (1 << NUM_TRACKED_BITS)}")
    print(f"Simple conflicts: {conflicts} ({conflicts / len(elf.buckets)})")
    print(f"Load factor: {len(elf.call_sites) / len(elf.buckets)}")

    invalid = coverage.validate()
    if invalid:
        raise Exception(f"The following buckets are invalid: {invalid}")


if __name__ == "__main__":
    main()
