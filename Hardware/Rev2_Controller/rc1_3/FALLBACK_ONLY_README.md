# RC1.3 — archived ESD fallback (NOT the release candidate)

The release candidate is **RC1.2e** (`../OSBAMS_Rev2_RELEASE_CANDIDATE_1/`, status `READY FOR JOE'S LOCAL KICAD 10 EXPORT`).
This folder holds a separate RC1.3 hardware variant (INA228 differential clamp + connector-entry ESD stage). It is kept **only as the documented fallback** if first-article ESD testing (F1/F5 in `../CONTROLLER_PROTECTION_AND_CONNECTOR_AUDIT.md`) fails, or if J5/J6 pins are ever exposed in normal use (release condition RC-A = YES currently holds: J5/J6 are internal and permanently mated). Do not merge it into RC1.2e and do not regenerate RC1.2e from it.
