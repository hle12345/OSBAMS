/*
 * test_protocol_estop.c — regression test: Protocol_StateName(TEST_ESTOP)
 * must return "E_STOP", not fall through to "UNKNOWN". main.c's
 * EnterEstop() sends this frame during an actual E-stop trip, so this
 * silently breaking would mean the desktop sees "OSBAMS,STATE,UNKNOWN"
 * during the one event that most needs to be unambiguous on screen.
 */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "protocol.h"

int main(void)
{
    const char *name = Protocol_StateName(TEST_ESTOP);
    printf("Protocol_StateName(TEST_ESTOP) = %s\n", name);
    assert(strcmp(name, "E_STOP") == 0);

    char buf[64];
    size_t len = Protocol_EncodeState(buf, sizeof(buf), TEST_ESTOP);
    assert(len > 0);
    printf("Encoded frame: %s", buf);
    assert(strstr(buf, "E_STOP") != NULL);
    assert(strstr(buf, "UNKNOWN") == NULL);

    /* FAULT must still resolve correctly too -- guard against a future
     * edit reordering the switch and breaking the adjacent case. */
    assert(strcmp(Protocol_StateName(TEST_FAULT), "FAULT") == 0);

    printf("Protocol E_STOP naming test passed.\n");
    return 0;
}
