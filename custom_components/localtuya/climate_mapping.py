"""Helpers for building custom climate mode mappings."""


def build_custom_mapping(config, fields):
    """Build a mode-to-raw-value mapping from configured string values."""
    mapping = {}
    for mode, config_key in fields.items():
        value = config.get(config_key)
        if not isinstance(value, str):
            continue
        value = value.strip()
        if value:
            mapping[mode] = value
    return mapping
