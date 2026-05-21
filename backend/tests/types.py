"""Shared test types."""

from typing import TypeAlias


JsonValue: TypeAlias = dict[str, "JsonValue"] | list["JsonValue"] | str | int | float | bool | None
JsonObject: TypeAlias = dict[str, JsonValue]
JsonPayload: TypeAlias = object
QueryParamValue: TypeAlias = str | int | float | bool | None
