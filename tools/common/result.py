from __future__ import annotations

import inspect
import json
import logging
from datetime import datetime, timezone
from functools import wraps
from time import perf_counter
from typing import (
    Any,
    Callable,
    Generic,
    Literal,
    Mapping,
    Optional,
    TypeVar,
    get_type_hints,
)

from langchain_core.tools import StructuredTool, ToolException, tool
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    TypeAdapter,
    model_validator,
)


SCHEMA_VERSION = "1.0"
DataT = TypeVar("DataT")

logger = logging.getLogger(__name__)
META_ADAPTER = TypeAdapter(dict[str, JsonValue])


# 通过装饰器统一agent和tool的协议

class ToolError(BaseModel):
    """Machine-readable error returned by every repository tool."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]*$")
    message: str = Field(min_length=1)
    retryable: bool = False


class ToolResult(BaseModel, Generic[DataT]):
    """Versioned envelope shared by all repository tools."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    tool: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
    ok: bool
    data: Optional[DataT] = None
    error: Optional[ToolError] = None
    meta: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_result_state(self) -> ToolResult[DataT]:
        if self.ok and (self.data is None or self.error is not None):
            raise ValueError("successful tool results require data and forbid error")
        if not self.ok and (self.data is not None or self.error is None):
            raise ValueError("failed tool results require error and forbid data")
        return self


class ToolExecutionError(Exception):
    """Expected operational or business error raised inside a tool."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        meta: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.meta = dict(meta or {})


def _validated_meta(meta: Optional[Mapping[str, Any]]) -> dict[str, JsonValue]:
    return META_ADAPTER.validate_python(dict(meta or {}), strict=True)


def _result_meta(meta: Optional[Mapping[str, Any]]) -> dict[str, JsonValue]:
    result = dict(meta or {})
    result.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    return _validated_meta(result)


def _serialize(result: ToolResult[Any]) -> str:
    return json.dumps(
        result.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def tool_success(
    tool_name: str,
    data: DataT,
    *,
    meta: Optional[Mapping[str, Any]] = None,
) -> str:
    """Create and serialize a successful ToolResult."""
    return _serialize(
        ToolResult[DataT](
            tool=tool_name,
            ok=True,
            data=data,
            meta=_result_meta(meta),
        )
    )


def tool_failure(
    tool_name: str,
    code: str,
    message: str,
    *,
    retryable: bool = False,
    meta: Optional[Mapping[str, Any]] = None,
) -> str:
    """Create and serialize a failed ToolResult."""
    return _serialize(
        ToolResult[Any](
            tool=tool_name,
            ok=False,
            error=ToolError(
                code=code,
                message=message,
                retryable=retryable,
            ),
            meta=_result_meta(meta),
        )
    )


def standard_tool(
    *,
    description: str,
    name: Optional[str] = None,
    meta: Optional[Mapping[str, Any]] = None,
    args_schema: Optional[type[BaseModel]] = None,
    data_model: Optional[type[BaseModel]] = None,
) -> Callable[[Callable[..., DataT]], StructuredTool]:
    """Wrap a synchronous function with validated ToolResult v1 responses."""

    def decorator(function: Callable[..., DataT]) -> StructuredTool:
        if inspect.iscoroutinefunction(function):
            raise TypeError("standard_tool currently supports synchronous functions only")

        tool_name = name or function.__name__
        base_meta = _validated_meta(meta)
        return_type = data_model or get_type_hints(function).get("return")
        if return_type is None or return_type is Any:
            raise TypeError("standard_tool functions require a concrete return annotation")
        data_adapter = TypeAdapter(return_type)

        @wraps(function)
        def wrapped(*args: Any, **kwargs: Any) -> str:
            started_at = perf_counter()

            def elapsed_meta(extra: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
                return {
                    **dict(extra or {}),
                    **base_meta,
                    "duration_ms": round(
                        (perf_counter() - started_at) * 1000,
                        2,
                    ),
                }

            try:
                data = function(*args, **kwargs)
            except ToolExecutionError as error:
                try:
                    return tool_failure(
                        tool_name,
                        error.code,
                        error.message,
                        retryable=error.retryable,
                        meta=elapsed_meta(error.meta),
                    )
                except Exception:
                    logger.exception("Invalid expected error from tool %s", tool_name)
                    return tool_failure(
                        tool_name,
                        "INTERNAL_ERROR",
                        "工具错误信息不符合统一协议",
                        retryable=False,
                        meta=elapsed_meta(),
                    )
            except Exception:
                logger.exception("Unexpected failure in tool %s", tool_name)
                return tool_failure(
                    tool_name,
                    "INTERNAL_ERROR",
                    "工具执行失败",
                    retryable=False,
                    meta=elapsed_meta(),
                )

            try:
                validated_data = data_adapter.validate_python(data)
                json_data = data_adapter.dump_python(validated_data, mode="json")
                return tool_success(
                    tool_name,
                    json_data,
                    meta=elapsed_meta(),
                )
            except Exception:
                logger.exception("Invalid result returned by tool %s", tool_name)
                return tool_failure(
                    tool_name,
                    "INVALID_TOOL_RESULT",
                    "工具返回结果不符合统一协议",
                    retryable=False,
                    meta=elapsed_meta(),
                )

        structured_tool = tool(
            tool_name,
            description=description,
            args_schema=args_schema,
        )(wrapped)

        def handle_tool_error(_: ToolException) -> str:
            return tool_failure(
                tool_name,
                "TOOL_ERROR",
                "工具执行失败，请稍后重试",
                retryable=True,
                meta=base_meta,
            )

        def handle_validation_error(_: Any) -> str:
            return tool_failure(
                tool_name,
                "INVALID_ARGUMENTS",
                "工具参数格式不正确",
                retryable=False,
                meta=base_meta,
            )

        structured_tool.handle_tool_error = handle_tool_error
        structured_tool.handle_validation_error = handle_validation_error
        return structured_tool

    return decorator
