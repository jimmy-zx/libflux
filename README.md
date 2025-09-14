# libflux

A simple library to collect coverage for coverage-guided fuzzing.

## Introduction

This project provides the following libraries:

### `libtracepc.so`

This library needs to be linked against the target executable,
with option `-fsanitize-coverage=trace-pc` enabled.
The following environs are used to control the behavior:

- `FLUXCOV_DUMP=[file]`: dump the raw coverage to `[file]` after completion.
- `FLUXCOV_SHM=[path]`: store the raw coverage to shared memory `[path]`.

### `libfluxcov.so`

The library uses shared memory to collect coverage from `libtracepc.so`.
See [fluxcov.h](include/fluxcov.h) for details.

This project also provides a Python binding [fluxcov](python/fluxcov).

## Quick start

```bash
cd libflux
make       # or `make libs` if you only want the libraries
```

The simple [testsuite](tests/test_simple.py) contains example usages.

Note: If ASLR is present on the system, the coverage might be different
even if the execution is exactly the same. This project
provides a binary `bin/no_aslr.out` to execute an executable without ASLR
(built by `make bins`).

To run the testsuite,

```bash
python3 -m venv venv
pip3 install -r requirements.txt
. .envrc
pytest
```

To build 32-bit libraries,

```bash
CFLAGS="-m32" OBJ_DIR=obj32 LIB_DIR=lib32 BIN_DIR=bin32 make
```

## Instrumentation

- Checking whether object files are instrumented: `objdump -dr [file]`.
- If the target executable invokes other instrumented executables,
  using `FLUXCOV_FILTER` might be helpful.

See [instrumentation.md](docs/instrumentation.md) for futher details.

## Configs

- `-DPATH_COVERAGE`: use path coverage instead of block coverage.
- `-DDEBUG`: enable debugging messages.
