"""Shared test types."""

type JsonValue = dict[str, "JsonValue"] | list["JsonValue"] | str | int | float | bool | None
type JsonObject = dict[str, JsonValue]
type JsonPayload = object
type QueryParamValue = str | int | float | bool | None
