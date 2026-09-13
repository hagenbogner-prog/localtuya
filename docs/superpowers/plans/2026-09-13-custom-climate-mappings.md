# Custom Climate Mappings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Track each checkbox before moving on.

**Goal:** Add persistent user-configurable HVAC and fan raw-value mappings while preserving every existing LocalTuya climate preset.

**Architecture:** `climate.py` remains responsible for climate schema and runtime behavior. A small pure helper filters and trims custom values so it can be unit-tested without importing Home Assistant. `config_flow.py` remains unchanged because it already persists platform fields.

**Tech Stack:** Python 3.11, Home Assistant custom integration APIs, Voluptuous, unittest, Tox.

**Spec:** `docs/superpowers/specs/2026-09-13-custom-climate-mappings-design.md`

## Global Constraints

- Existing predefined mappings remain unchanged.
- No brand-specific logic.
- Blank custom fields mean unsupported.
- Temperature and unrelated climate features remain unchanged.
- No config-entry migration.
- Conventional Commits only.

---

### Task 1: Mapping helper and tests

**Files:** Create `custom_components/localtuya/climate_mapping.py`, create `tests/test_climate_mapping.py`, modify `tox.ini`.

- [ ] Write failing unittest cases for missing/blank values, whitespace trimming, and preservation of `auto/cool/dry/fan` and `low/mid/high`.
- [ ] Run `python -m unittest discover -s tests -p "test_*.py" -v` and confirm failure.
- [ ] Implement `build_custom_mapping(config, fields)` as a pure function that accepts only non-empty strings, strips surrounding whitespace, and returns a dict keyed by the supplied mode objects.
- [ ] Re-run tests and confirm PASS.
- [ ] Replace the dormant Tox `true` test command with unittest discovery; do not change the pinned Home Assistant dependency in this feature.
- [ ] Commit: `test: cover custom climate mapping values`.

### Task 2: Persistent fields and schema

**Files:** Modify `custom_components/localtuya/const.py` and `custom_components/localtuya/climate.py`.

- [ ] Add config keys for custom HVAC Auto/Cool/Heat/Dry/Fan Only and custom Fan Auto/Low/Medium/High.
- [ ] Add `CUSTOM_MODE_SET = "Custom"` and two field maps from Home Assistant modes to config keys.
- [ ] Add `build_custom_hvac_mode_set(config)` and `build_custom_fan_mode_set(config)` wrappers using the pure helper.
- [ ] Extend the existing HVAC and fan selectors with `Custom` without changing any existing preset key.
- [ ] Add all nine custom values to `flow_schema()` as optional strings with empty-string defaults.
- [ ] Leave `config_flow.py` unchanged.
- [ ] Run unit tests, Black, and flake8 on changed Python files.
- [ ] Commit: `feat: add custom climate mode fields`.

### Task 3: Runtime resolution and safety

**Files:** Modify `custom_components/localtuya/climate.py`.

- [ ] In `LocaltuyaClimate.__init__`, resolve predefined sets exactly as today; when the selector is `Custom`, build the mapping from stored fields.
- [ ] Store booleans identifying whether HVAC/fan use Custom; log one warning if Custom resolves to an empty mapping.
- [ ] Add guards to `async_set_hvac_mode()` so a missing DP or unsupported mode returns before any device write.
- [ ] Advertise fan support only when the fan DP exists and the resolved mapping is non-empty.
- [ ] Preserve legacy unknown-status fallbacks for predefined sets. For Custom only, unknown HVAC/fan raw states become `None` instead of an unconfigured Auto mode.
- [ ] Confirm mode lists remain derived directly from mapping keys.
- [ ] Run tests and targeted static checks.
- [ ] Commit: `fix: reject unsupported custom climate modes`.

### Task 4: UI text and documentation

**Files:** Modify `custom_components/localtuya/translations/en.json` and `README.md`.

- [ ] Add English labels for all nine custom fields under `options.step.configure_entity.data`.
- [ ] Under `# Climates`, document when to select Custom, that raw values must match the Tuya enum, and that blank fields disable unsupported Home Assistant modes.
- [ ] Validate JSON with `python -m json.tool custom_components/localtuya/translations/en.json` and run codespell on edited documentation.
- [ ] Commit: `docs: document custom climate mappings`.

### Task 5: Full validation and real-device acceptance

- [ ] Run direct unittest discovery and `tox -e lint,typing`; report any pre-existing repository-wide failures separately rather than claiming success.
- [ ] Verify HACS/hassfest workflow status.
- [ ] Test the fork build in Home Assistant and configure the representative entity as: DP1 power, DP2 Custom HVAC (`auto`, `cool`, blank Heat, `dry`, `fan`), DP3 Custom fan (blank Auto, `low`, `mid`, `high`), DP5 target temperature, DP8 current temperature, range 18–32, step/precision 1, Celsius.
- [ ] Expected HVAC modes: Off, Auto, Cool, Dry, Fan only. Expected fan modes: Low, Medium, High.
- [ ] Verify raw writes: DP2 receives `auto/cool/dry/fan`; DP3 receives `low/mid/high`.
- [ ] Verify target/current temperature behavior is unchanged and auxiliary entities on DPs 4, 6, 7, 9, 12, 13, 15 still behave as before.

### Task 6: Upstream PR

- [ ] Compare the feature branch against `master` and remove unrelated changes.
- [ ] Open a PR from `hagenbogner-prog/localtuya:feat-custom-climate-mappings` to `rospogrigio/localtuya:master`.
- [ ] Title: `feat: support custom climate mode mappings`.
- [ ] PR sections: `## Änderungen` and `## Testen`; describe the generic capability, preserved preset behavior, focused tests, and real-device verification.
- [ ] Allow maintainer edits and reference the existing upstream discussion about configurable climate modes.

## Final Self-Review

- [ ] Every approved spec requirement is covered.
- [ ] Existing presets are unchanged.
- [ ] Blank values are ignored and unsupported writes are blocked.
- [ ] Temperature logic is untouched.
- [ ] No device-specific logic is present.
- [ ] Tests and validation are accurately reported.
- [ ] Real-device acceptance passes before opening the upstream PR.

## Progress

- 2026-09-13: GitHub Actions was enabled for the fork. This documentation-only push is used to trigger branch CI; automated validation is pending.
