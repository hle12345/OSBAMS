/*
 * accum_session.h — explicit start/reset of the capacity accumulators and assembly of the protocol v2 fields.
 *
 * One session owns the STM32 integrator and (through a callback) the INA228 accumulators; they are reset TOGETHER and only
 * by AccumSession_Start(), which refuses to run during an active test (anything other than IDLE..READY or COMPLETE), so a
 * stray Pi/UI command cannot zero the totals mid-run. The ACCUM_START line command is a thin wrapper over the same rule.
 * Nothing here changes relay, E-stop, load-enable or the safety state machine, and it works the same whichever
 * protocol version is on the wire. NOT wired into main.c yet (needs a target build; see PROTOCOL_V2_DESIGN.md).
 */
#ifndef ACCUM_SESSION_H
#define ACCUM_SESSION_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "osbams_status.h"
#include "integrator.h"
#include "ina228.h"
#include "protocol.h"
#include "test_controller.h"

typedef osbams_status_t (*accum_hw_reset_fn)(void);     /* normally INA228_ResetAccumulators; NULL = no hardware accumulator */

typedef struct {
    integrator_t      integ;
    bool              started;
    bool              hw_reset_failed;                    /* latched until the next clean start */
    uint32_t          acq_count;                          /* acquisitions since start */
    accum_hw_reset_fn hw_reset;
} accum_session_t;

typedef enum {
    ACCUM_START_OK = 0,
    ACCUM_START_REFUSED_STATE,
    ACCUM_START_HW_RESET_FAILED,    /* STM32 side was still reset; INA228 fields stay NA + ACCUM_INVALID */
    ACCUM_START_BAD_ARG
} accum_start_result_t;

void                 AccumSession_Init(accum_session_t *s, accum_hw_reset_fn hw_reset, uint64_t max_gap_us);
bool                 AccumSession_StateAllowsStart(test_state_t st);
accum_start_result_t AccumSession_Start(accum_session_t *s, test_state_t st);
void                 AccumSession_OnSample(accum_session_t *s, uint64_t t_us, int32_t i_ma, int32_t p_mw, bool valid);

/** Handles the line "ACCUM_START". Returns true if the line was this command (response written to resp), false otherwise. */
bool AccumSession_HandleCommand(accum_session_t *s, const char *line, test_state_t st, char *resp, size_t cap);

/** Fill the protocol v2 extra fields. ina may be NULL (not read). base_status carries caller-known PROTO_SS_* bits. */
void AccumSession_BuildExtra(const accum_session_t *s, bool adc_valid, int32_t adc_mv, const ina228_accum_snapshot_t *ina,
                             uint16_t base_status, protocol_v2_extra_t *out);

#endif /* ACCUM_SESSION_H */
