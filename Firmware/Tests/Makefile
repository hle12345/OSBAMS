# Tests/Makefile — RECONSTRUCTED. The real Makefile was listed among the
# uploads but its content never actually arrived in this conversation
# (only .c/.h files did) — diff this against the real one before trusting
# it as authoritative. Every rule below was actually run to build and
# pass all 9 test binaries during the final consolidation check.
#
# Usage:
#   make            # build + run every test
#   make clean

CC      := gcc
CFLAGS  := -Wall -Wextra -std=c11
INC     := -I../App/Inc -I../Drivers/Inc -I../Core/Inc -I.

APP_SRC     := ../App/Src
DRIVERS_SRC := ../Drivers/Src
CORE_SRC    := ../Core/Src

BIN_DIR := build

TARGETS := \
    $(BIN_DIR)/test_measurement \
    $(BIN_DIR)/test_measurement_invalid_channel \
    $(BIN_DIR)/test_protocol_c \
    $(BIN_DIR)/test_protocol_estop \
    $(BIN_DIR)/test_protocol_v2 \
    $(BIN_DIR)/test_safety_modules \
    $(BIN_DIR)/test_safety_power_optional \
    $(BIN_DIR)/test_ina228_calibration \
    $(BIN_DIR)/test_ina228_power_decode \
    $(BIN_DIR)/test_ina228_accum \
    $(BIN_DIR)/test_integrator \
    $(BIN_DIR)/test_accum_session \
    $(BIN_DIR)/test_estop_and_contactor \
    $(BIN_DIR)/test_tick_consolidation \
    $(BIN_DIR)/test_state_machine \
    $(BIN_DIR)/test_recovery_flow

.PHONY: all clean run
all: $(BIN_DIR) $(TARGETS)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

# Measurement Engine — no chip names, no hardware.
$(BIN_DIR)/test_measurement: test_measurement.c $(APP_SRC)/measurement.c
	$(CC) $(CFLAGS) $(INC) -o $@ $^

# Regression: failed sensor channels must not corrupt Ah/Wh integration.
$(BIN_DIR)/test_measurement_invalid_channel: test_measurement_invalid_channel.c $(APP_SRC)/measurement.c
	$(CC) $(CFLAGS) $(INC) -o $@ $^

# Protocol conformance — real encoder, prints frames for the Python side.
$(BIN_DIR)/test_protocol_c: test_protocol_c.c $(APP_SRC)/protocol.c
	$(CC) $(CFLAGS) $(INC) -o $@ $^

# Protocol v2 encoder against the golden vectors (docs/rev2/protocol_v2_test_vectors.json).
$(BIN_DIR)/test_protocol_v2: test_protocol_v2.c $(APP_SRC)/protocol.c
	$(CC) $(CFLAGS) $(INC) -o $@ $^

# Regression: Protocol_StateName(TEST_ESTOP) must be "E_STOP", not "UNKNOWN".
$(BIN_DIR)/test_protocol_estop: test_protocol_estop.c $(APP_SRC)/protocol.c
	$(CC) $(CFLAGS) $(INC) -o $@ $^

# Safety decision logic (watchdog gating, ADC agreement, fault evaluation).
$(BIN_DIR)/test_safety_modules: test_safety_modules.c \
    $(DRIVERS_SRC)/watchdog.c $(DRIVERS_SRC)/adc_safety.c $(APP_SRC)/safety.c
	$(CC) $(CFLAGS) $(INC) -o $@ $^

# Regression: a POWER-only sensor failure must not trigger a critical fault.
$(BIN_DIR)/test_safety_power_optional: test_safety_power_optional.c $(APP_SRC)/safety.c
	$(CC) $(CFLAGS) $(INC) -o $@ $^

# INA228 SHUNT_CAL regression guard — needs a link-only I2C stub because
# the real i2c_bus.c hard-includes the STM32 device header.
$(BIN_DIR)/test_ina228_calibration: test_ina228_calibration.c \
    $(DRIVERS_SRC)/ina228.c i2c_bus_link_stub.c
	$(CC) $(CFLAGS) $(INC) -o $@ $^

# Regression: INA228 POWER register decode (was ~16x too small).
$(BIN_DIR)/test_ina228_power_decode: test_ina228_power_decode.c $(DRIVERS_SRC)/ina228.c
	$(CC) $(CFLAGS) $(INC) -o $@ $^

# INA228 CHARGE/ENERGY accumulator decode, scaling, reset (fake I2C register file).
$(BIN_DIR)/test_ina228_accum: test_ina228_accum.c $(DRIVERS_SRC)/ina228.c
	$(CC) $(CFLAGS) $(INC) -o $@ $^

# Timestamp-based Ah/Wh integrator (actual dt, explicit reset, gap/overflow behaviour).
$(BIN_DIR)/test_integrator: test_integrator.c $(APP_SRC)/integrator.c
	$(CC) $(CFLAGS) $(INC) -o $@ $^

# Explicit accumulator start/reset rules, ACCUM_START command gating, protocol v2 field assembly.
$(BIN_DIR)/test_accum_session: test_accum_session.c $(APP_SRC)/accum_session.c $(APP_SRC)/integrator.c $(APP_SRC)/protocol.c
	$(CC) $(CFLAGS) $(INC) -o $@ $^

# E-stop + PC9 contactor supervision logic.
$(BIN_DIR)/test_estop_and_contactor: test_estop_and_contactor.c \
    $(DRIVERS_SRC)/estop.c $(DRIVERS_SRC)/load_driver.c $(CORE_SRC)/tick.c
	$(CC) $(CFLAGS) $(INC) -o $@ $^

# Single-tick-source timing behavior.
$(BIN_DIR)/test_tick_consolidation: test_tick_consolidation.c $(CORE_SRC)/tick.c
	$(CC) $(CFLAGS) $(INC) -o $@ $^

# FAULT/E_STOP state machine topology.
$(BIN_DIR)/test_state_machine: test_state_machine.c $(APP_SRC)/test_controller.c
	$(CC) $(CFLAGS) $(INC) -o $@ $^

# Full recovery-flow integration: real safety.c + real test_controller.c,
# including the persistent-overvoltage-clears-through-on-ACK regression.
$(BIN_DIR)/test_recovery_flow: test_recovery_flow.c \
    $(APP_SRC)/test_controller.c $(APP_SRC)/safety.c
	$(CC) $(CFLAGS) $(INC) -o $@ $^

run: all
	@for t in $(TARGETS); do \
	    echo "=== $$t ==="; \
	    ./$$t || exit 1; \
	done

clean:
	rm -rf $(BIN_DIR)
