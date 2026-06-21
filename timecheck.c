#include <stdio.h>
#include <mach/mach_time.h>
int main() {
    mach_timebase_info_data_t tb;
    mach_timebase_info(&tb);
    printf("numer: %d, denom: %d\n", tb.numer, tb.denom);
    return 0;
}
