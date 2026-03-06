#ifndef FLUXCOV_H_
#define FLUXCOV_H_

#include <stdbool.h>

#include "utils.h"

struct fluxcov_globals {
  struct counters_t counters;
};

struct fluxcov_instance {
  char *path;                  /* copy of path, malloc'd */
  struct counters_t *counters; /* points to shm buffer */
};

/* Creates and initializes a new fluxcov_globals buffer.
 * The globals buffer is used to store maximum coverage.
 */
struct fluxcov_globals *fluxcov_init(int *err);

/* Frees the fluxcov_globals buffer.
 */
int fluxcov_fini(struct fluxcov_globals *globals, int *err);

/* Creates a new fluxcov_instance buffer, backed by shm.
 * The local buffers should be written by `libtracepc.so` and read (compared)
 * using `fluxcov_check`.
 */
struct fluxcov_instance *fluxcov_start(const char *path, int *err);

/* Checks if there is new coverage.
 */
bool fluxcov_check(struct fluxcov_globals *globals,
                   struct fluxcov_instance *instance, int *err);

/* Frees the fluxcov_instance buffer.
 */
int fluxcov_end(struct fluxcov_instance *instance, int *err);

#endif  // FLUXCOV_H_
