# Instrumentation

## `gcc`

- A linker that does not require ordering is required.
- Not all compilations receiving `CFLAGS` receives `LDFLAGS`,
  which might lead to a linker error for `__sanitizer_cov_trace_pc`.
  As a workaround, `CFLAGS` includes both `$CFLAGS` and `$LDFLAGS`.

Folder structure:

```
$ROOTDIR
| gcc
| | build
| | prefix
| `
| libflux
`
```

Build:

```bash
#!/bin/sh

ROOTDIR=$HOME
CFLAGS="-fsanitize-coverage=trace-pc"
LDFLAGS="-L$ROOTDIR/libflux/lib -L$ROOTDIR/libflux/lib32 -ltracepc -fuse-ld=mold"

export LD_LIBRARY_PATH=$ROOTDIR/libflux/lib:$ROOTDIR/libflux/lib32:$LD_LIBRARY_PATH

cd gcc/build

../configure \
    --prefix $PWD/../prefix \
    --enable-languages=c \
    --disable-multilib \
    --disable-bootstrap \
    --disable-nls \
    --with-target-system-zlib \
    CC="gcc $LDFLAGS $CFLAGS" \
    CXX="g++ $LDFLAGS $CFLAGS" \
    LD="ld.mold $LDFLAGS"

make -j
```
