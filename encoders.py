"""
Encoders for serializing the agent payload into JSON or TOON.

The TOON encoder here implements a pragmatic subset of the format spec
focused on what we actually need for this benchmark:

  - Top-level scalars (str/int/float/bool/None) → indented `key: value`
  - Lists of uniform dicts (the agent dataframes) → tabular form:
        table_name[N]{field1,field2,...}:
          v1,v2,...
          v1,v2,...
  - Nested dicts → indented YAML-like blocks

Reference: https://github.com/toon-format/toon
"""

from __future__ import annotations

import json
from typing import Any


# ---------------------------------------------------------------------------
# JSON encoder (trivial wrapper for parity with TOON interface)
# ---------------------------------------------------------------------------

def encode_json(payload: dict, *, pretty: bool = True) -> str:
    """Serialize to JSON. Pretty-printed by default (most common LLM input form)."""
    if pretty:
        return json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# TOON encoder
# ---------------------------------------------------------------------------

_TOON_DELIM = ","


def _toon_scalar(v: Any) -> str:
    """Render a single scalar in TOON form."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        # Keep ints as ints; floats with their natural repr
        return str(v)
    s = str(v)
    # Quote if the string contains the delimiter, the structural chars,
    # leading/trailing whitespace, or starts with a special char.
    needs_quote = (
        _TOON_DELIM in s
        or '"' in s
        or "\n" in s
        or s != s.strip()
        or s.startswith(("[", "{", "-", "#"))
    )
    if needs_quote:
        escaped = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return s


def _is_uniform_list_of_dicts(value: Any) -> bool:
    """A list qualifies for tabular encoding if every element is a dict
    with the *same set of keys* and *scalar values only*."""
    if not isinstance(value, list) or not value:
        return False
    if not all(isinstance(x, dict) for x in value):
        return False
    keys = list(value[0].keys())
    for row in value[1:]:
        if list(row.keys()) != keys:
            return False
    # All values must be scalars (no nested dicts/lists)
    for row in value:
        for v in row.values():
            if isinstance(v, (dict, list)):
                return False
    return True


def _encode_table(name: str, rows: list[dict], indent: int = 0) -> list[str]:
    """Render a uniform list of dicts as a TOON table block."""
    pad = "  " * indent
    fields = list(rows[0].keys())
    header = f"{pad}{name}[{len(rows)}]{{{_TOON_DELIM.join(fields)}}}:"
    lines = [header]
    inner_pad = "  " * (indent + 1)
    for row in rows:
        values = [_toon_scalar(row[f]) for f in fields]
        lines.append(f"{inner_pad}{_TOON_DELIM.join(values)}")
    return lines


def _encode_value(key: str | None, value: Any, indent: int = 0) -> list[str]:
    """Recursively encode a value. If `key` is None, treat as top-level block."""
    pad = "  " * indent

    # Dict → nested indented block
    if isinstance(value, dict):
        lines = []
        if key is not None:
            lines.append(f"{pad}{key}:")
            child_indent = indent + 1
        else:
            child_indent = indent
        for k, v in value.items():
            lines.extend(_encode_value(k, v, child_indent))
        return lines

    # List of uniform dicts → tabular
    if isinstance(value, list) and _is_uniform_list_of_dicts(value):
        return _encode_table(key or "items", value, indent)

    # List of scalars → inline bracket
    if isinstance(value, list):
        if all(not isinstance(x, (dict, list)) for x in value):
            scalars = _TOON_DELIM.join(_toon_scalar(x) for x in value)
            return [f"{pad}{key}[{len(value)}]: {scalars}"]
        # Mixed/non-uniform list — fall back to indented entries
        lines = [f"{pad}{key}:"]
        for x in value:
            lines.extend(_encode_value(None, x, indent + 1))
        return lines

    # Scalar
    return [f"{pad}{key}: {_toon_scalar(value)}"]


def encode_toon(payload: dict) -> str:
    """Encode a payload dict to TOON format."""
    lines: list[str] = []
    for key, value in payload.items():
        lines.extend(_encode_value(key, value, 0))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Convenience: encode just the agent results (the bulk of the prompt)
# ---------------------------------------------------------------------------

def encode_agent_data_json(agent_results: dict[str, list[dict]], *, pretty: bool = True) -> str:
    """Encode {agent_name: [rows]} as JSON."""
    return encode_json(agent_results, pretty=pretty)


def encode_agent_data_toon(agent_results: dict[str, list[dict]]) -> str:
    """Encode {agent_name: [rows]} as flat TOON tables — one block per agent."""
    blocks = []
    for agent_name, rows in agent_results.items():
        if not rows:
            blocks.append(f"{agent_name}[0]{{}}:")
            continue
        if _is_uniform_list_of_dicts(rows):
            blocks.extend(_encode_table(agent_name, rows, indent=0))
        else:
            # Fall back to generic encoding
            blocks.extend(_encode_value(agent_name, rows, indent=0))
        blocks.append("")  # blank line between agents for readability
    return "\n".join(blocks).rstrip()


if __name__ == "__main__":
    # Quick smoke test
    from agents import get_full_payload

    payload = get_full_payload()
    agent_results = payload["agent_results"]

    json_out = encode_agent_data_json(agent_results, pretty=True)
    toon_out = encode_agent_data_toon(agent_results)

    print(f"JSON pretty:    {len(json_out):>7,} chars")
    print(f"JSON compact:   {len(encode_agent_data_json(agent_results, pretty=False)):>7,} chars")
    print(f"TOON:           {len(toon_out):>7,} chars")
    print()
    print("--- TOON preview (first 1500 chars) ---")
    print(toon_out[:1500])
