# Custom Climate Mappings Design

## Goal

Add generic, user-configurable HVAC mode and fan mode mappings to LocalTuya climate entities so devices with Tuya enum values that do not match LocalTuya's predefined sets can be configured without editing source files or Home Assistant storage.

The feature must remain backward-compatible with all existing predefined climate mappings and must not contain device-specific Klarstein logic.

## Context

LocalTuya currently exposes predefined dictionaries in `custom_components/localtuya/climate.py` for HVAC and fan modes. These work for many devices but fail when a device uses different raw Tuya enum strings. A representative device uses the following values:

- HVAC: `auto`, `cool`, `fan`, `dry`
- Fan: `low`, `mid`, `high`

Existing LocalTuya presets use values such as `cold`, `wind`, `wet`, `middle`, `auto`, and `strong`, so the UI cannot represent this device accurately.

The options flow already stores platform-specific entity fields returned by each platform's `flow_schema()`. Therefore the smallest upstream-friendly change is to extend the climate schema and climate runtime mapping logic while leaving the generic config flow architecture intact.

## Scope

This change adds:

- A `Custom` HVAC mode set option.
- Optional raw-value fields for supported Home Assistant HVAC modes.
- A `Custom` fan mode set option.
- Optional raw-value fields for supported Home Assistant fan modes.
- Runtime construction of custom mappings from the stored entity configuration.
- Validation and safe fallback behavior for empty or invalid custom configurations.
- English translations for the new fields.
- Tests that preserve existing behavior and verify custom behavior.

## Non-goals

This change does not:

- Add Klarstein-specific code or device detection.
- Change Tuya protocol handling.
- Change timer, ionizer, sleep, fault, swing, preset, eco, or action handling.
- Automatically discover enum values from Tuya Cloud.
- Replace or remove existing predefined HVAC or fan mode sets.
- Add a second config-flow page solely for custom mappings.
- Modify Home Assistant `.storage` manually.

## User Experience

The climate configuration form keeps the current `HVAC Mode Set` and `Fan Mode Set` selectors. Each gains a `Custom` option.

The custom raw-value fields are always visible to keep the implementation small and compatible with LocalTuya's current static platform schema. They are ignored unless the related set is `Custom`.

### HVAC fields

- Custom HVAC Auto
- Custom HVAC Cool
- Custom HVAC Heat
- Custom HVAC Dry
- Custom HVAC Fan Only

Example:

```text
HVAC Mode DP: 2
HVAC Mode Set: Custom

Custom HVAC Auto:      auto
Custom HVAC Cool:      cool
Custom HVAC Heat:
Custom HVAC Dry:       dry
Custom HVAC Fan Only:  fan
```

A blank field means that Home Assistant mode is unsupported and must not be exposed for the entity.

### Fan fields

- Custom Fan Auto
- Custom Fan Low
- Custom Fan Medium
- Custom Fan High

Example:

```text
Fan Mode DP: 3
Fan Mode Set: Custom

Custom Fan Auto:
Custom Fan Low:        low
Custom Fan Medium:     mid
Custom Fan High:       high
```

A blank field means that fan mode is unsupported and must not be exposed for the entity.

## Configuration Keys

Add constants in `custom_components/localtuya/const.py`:

```python
CONF_CUSTOM_HVAC_AUTO = "custom_hvac_auto"
CONF_CUSTOM_HVAC_COOL = "custom_hvac_cool"
CONF_CUSTOM_HVAC_HEAT = "custom_hvac_heat"
CONF_CUSTOM_HVAC_DRY = "custom_hvac_dry"
CONF_CUSTOM_HVAC_FAN_ONLY = "custom_hvac_fan_only"

CONF_CUSTOM_FAN_AUTO = "custom_fan_auto"
CONF_CUSTOM_FAN_LOW = "custom_fan_low"
CONF_CUSTOM_FAN_MEDIUM = "custom_fan_medium"
CONF_CUSTOM_FAN_HIGH = "custom_fan_high"
```

The stored values are strings. Empty strings are treated the same as missing values.

## Schema Changes

`custom_components/localtuya/climate.py` remains the owner of climate-specific form fields.

Add `Custom` to the selectable HVAC and fan mode set choices without altering any existing keys or mappings.

Add each custom value as an optional string field to `flow_schema(dps)`.

The generic `config_flow.py` requires no architecture change because it already persists fields returned from the platform schema and restores them during editing.

## Runtime Mapping Logic

The entity should resolve its mappings during initialization.

For predefined sets, behavior remains exactly as it is today:

```python
HVAC_MODE_SETS.get(configured_set, {})
HVAC_FAN_MODE_SETS.get(configured_set, {})
```

For `Custom`, build dictionaries from the configured values.

Conceptually:

```python
{
    HVACMode.AUTO: "auto",
    HVACMode.COOL: "cool",
    HVACMode.DRY: "dry",
    HVACMode.FAN_ONLY: "fan",
}
```

and:

```python
{
    FAN_LOW: "low",
    FAN_MEDIUM: "mid",
    FAN_HIGH: "high",
}
```

Only non-empty values are inserted.

The runtime should expose only keys present in the resulting mapping. Existing `hvac_modes` and `fan_modes` properties can therefore continue deriving UI choices from the mapping keys.

## Mapping Helper Design

To keep initialization readable and testable, add focused helper functions in `climate.py` rather than embedding repeated conditionals in `LocaltuyaClimate.__init__`.

Suggested interfaces:

```python
def build_custom_hvac_mode_set(config: dict) -> dict:
    """Build a Home Assistant HVAC mode to raw Tuya value mapping."""


def build_custom_fan_mode_set(config: dict) -> dict:
    """Build a Home Assistant fan mode to raw Tuya value mapping."""
```

The helpers:

- Read only their relevant custom configuration keys.
- Strip surrounding whitespace from string values.
- Ignore missing or empty values.
- Return an empty dictionary when nothing is configured.
- Never invent raw Tuya values.

## Validation and Error Handling

If `Custom` is selected and the resulting mapping is empty, LocalTuya must not send arbitrary or fallback raw values.

Expected behavior:

- The custom mapping remains empty.
- The entity logs a warning explaining that `Custom` was selected without any configured values.
- Unsupported modes are not exposed.
- Calls attempting to set an unsupported mode continue to use the existing validation path and are rejected instead of sending a command.

For predefined mappings, no new warnings or behavior changes occur.

No secrets, local keys, access tokens, device IDs, or IP addresses are written to source code, tests, docs, or logs introduced by this feature.

## Backward Compatibility

Existing climate entities must continue to work without migration.

Compatibility requirements:

- Existing `hvac_mode_set` values keep the same names and dictionaries.
- Existing `hvac_fan_mode_set` values keep the same names and dictionaries.
- New custom fields are optional.
- Entities not using `Custom` ignore all custom fields.
- No config-entry version bump is required because existing stored entries remain valid and new keys are optional.
- Editing an existing entity restores any new custom values when present.

## Representative Acceptance Configuration

A device using the following configuration must be supported without source edits:

```text
Main DP:                 1
HVAC Mode DP:            2
HVAC Mode Set:           Custom
Custom HVAC Auto:        auto
Custom HVAC Cool:        cool
Custom HVAC Heat:
Custom HVAC Dry:         dry
Custom HVAC Fan Only:    fan

Fan Mode DP:             3
Fan Mode Set:            Custom
Custom Fan Auto:
Custom Fan Low:          low
Custom Fan Medium:       mid
Custom Fan High:         high

Target Temperature DP:   5
Current Temperature DP:  8
Minimum Temperature:     18
Maximum Temperature:     32
Temperature Step:        1
Precision:               1
Target Precision:        1
Temperature Unit:        Celsius
```

Expected Home Assistant behavior:

- HVAC modes exposed: Auto, Cool, Dry, Fan Only, Off.
- Heat is not exposed.
- Fan modes exposed: Low, Medium, High.
- Fan Auto and Strong are not exposed.
- Selecting Cool sends raw value `cool` to DP 2.
- Selecting Dry sends raw value `dry` to DP 2.
- Selecting Fan Only sends raw value `fan` to DP 2.
- Selecting Medium fan sends raw value `mid` to DP 3.
- Temperature target and current temperature continue using the existing generic climate logic.

## Testing Strategy

Tests should cover both regression and new behavior.

Required cases:

1. Existing predefined HVAC mapping resolves exactly as before.
2. Existing predefined fan mapping resolves exactly as before.
3. Custom HVAC mapping contains only non-empty configured modes.
4. Custom fan mapping contains only non-empty configured modes.
5. Surrounding whitespace is removed from custom raw values.
6. Empty custom HVAC configuration returns an empty mapping and produces the warning path.
7. Empty custom fan configuration returns an empty mapping and produces the warning path.
8. Unsupported HVAC modes are not exposed by `hvac_modes`.
9. Unsupported fan modes are not exposed by `fan_modes`.
10. Raw values `cool`, `dry`, `fan`, and `mid` are preserved exactly when used in custom mappings.

Run the repository's existing Tox/validation tooling before opening the upstream pull request.

## Documentation

Update English config-flow translations for all new custom fields and the `Custom` selector value where translation structure allows.

Add a concise README or integration documentation section explaining:

- When `Custom` mappings are useful.
- That raw values must exactly match the device's Tuya enum values.
- That blank fields disable the corresponding Home Assistant mode.
- That users should not publish local keys, cloud access tokens, or other credentials when asking for help.

## Upstream Strategy

Development occurs in the fork branch `feat-custom-climate-mappings`.

Use small Conventional Commits, for example:

```text
test: cover custom climate mappings
feat: add custom hvac mode mappings
feat: add custom fan mode mappings
docs: document custom climate mappings
```

After automated checks and real-device verification pass, open a pull request against `rospogrigio/localtuya:master`.

The pull request should describe the feature as generic LocalTuya functionality. The representative air conditioner is evidence for testing, not a code-level special case.

## Success Criteria

The design is complete when all of the following are true:

- Existing predefined climate mappings behave unchanged.
- A user can configure arbitrary raw values for Auto, Cool, Heat, Dry, and Fan Only.
- A user can configure arbitrary raw values for Auto, Low, Medium, and High fan modes.
- Blank values remove unsupported modes from the Home Assistant entity.
- No source-code edit is needed for the representative `auto/cool/fan/dry` and `low/mid/high` device.
- Temperature handling remains unchanged.
- The repository's validation/tests pass.
- The feature can be proposed upstream without any device-specific code.
