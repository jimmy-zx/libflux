#include <stdio.h>
#include <stdlib.h>
#include <sys/personality.h>
#include <unistd.h>

extern char **environ;

int main(int argc, char **argv) {
  if (argc == 1) {
    printf("Usage: %s [cmd]\n", argv[0]);
    exit(EXIT_FAILURE);
  }
  if (personality(ADDR_NO_RANDOMIZE) != 0) {
    perror("personality");
    exit(EXIT_FAILURE);
  }
  if (execve(argv[1], &argv[1], environ)) {
    perror("execve");
    exit(EXIT_FAILURE);
  }
  return 0;
}
