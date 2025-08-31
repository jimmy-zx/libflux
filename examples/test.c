#include <assert.h>
#include <stdlib.h>
#include <unistd.h>

#include "fluxcov.h"

int main(void) {
  char *shm_path = "/shm_test_c";

  struct fluxcov_globals *globals = fluxcov_init(NULL);
  assert(globals != NULL);

  struct fluxcov_instance *inst = fluxcov_start(shm_path, NULL);
  assert(inst != NULL);

  assert(fluxcov_end(inst, NULL) == 0);

  assert(fluxcov_fini(globals, NULL) == 0);

  return 0;
}
