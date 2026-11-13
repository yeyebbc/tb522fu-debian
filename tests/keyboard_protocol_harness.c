#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
typedef uint8_t u8;
#include "lenovo-yoga-keyboard-protocol.h"

int main(void)
{
    char *line = NULL;
    size_t cap = 0;
    while (getline(&line, &cap, stdin) > 0) {
        struct ly_receiver rx = {0};
        u8 payload[LY_FRAME_MAX], wire[LY_FRAME_MAX];
        unsigned int byte, i = 0;
        int n, errors = 0, packets = 0, valid;
        while (line[i] && line[i] != '\n') {
            if (sscanf(line + i, "%2x", &byte) != 1) return 2;
            i += 2;
            n = ly_receive_byte(&rx, byte, payload);
            if (n < 0) errors++;
            if (n <= 0) continue;
            packets++;
            valid = payload[0] == 0x11 ? ly_valid_keyboard(payload, n) :
                    payload[0] == 0x12 ? ly_valid_consumer(payload, n) :
                    payload[0] == 0x13 ? ly_valid_touch(payload, n) : 1;
            printf("P %d ", valid);
            for (int j = 0; j < n; j++) printf("%02x", payload[j]);
            int encoded = ly_encode(payload, n, 0, wire);
            printf(" E ");
            if (encoded < 0) printf("error");
            else for (int j = 0; j < encoded; j++) printf("%02x", wire[j]);
            putchar('\n');
        }
        printf("END %d %d %u\n", packets, errors, rx.length);
    }
    free(line);
    return 0;
}
