#include <stdio.h>

int main(int argc, char **argv) {
  (void)argv;
  if (argc == 1) {
    printf("argc == 1\n");
  } else {
    printf("argc > 1\n");
  }
}
