import json
import unittest
from typing import Any
from unittest.mock import patch

from pydantic import BaseModel, ConfigDict, ValidationError

from tools.common import ToolExecutionError, ToolResult, standard_tool
from tools.common.result import logger


class DemoInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    value: str


class DemoData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str


@standard_tool(
    name="success_demo",
    description="Return demo data",
    args_schema=DemoInput,
    data_model=DemoData,
    meta={"provider": "test"},
)
def success_demo(value: str) -> dict[str, Any]:
    return {"value": value}


@standard_tool(
    name="expected_error_demo",
    description="Return an expected error",
    args_schema=DemoInput,
    data_model=DemoData,
)
def expected_error_demo(value: str) -> dict[str, Any]:
    raise ToolExecutionError("NOT_FOUND", f"Missing {value}")


@standard_tool(
    name="invalid_result_demo",
    description="Return invalid data",
    args_schema=DemoInput,
    data_model=DemoData,
)
def invalid_result_demo(value: str) -> dict[str, Any]:
    return {"unexpected": value}


@standard_tool(
    name="unexpected_error_demo",
    description="Raise an unexpected error",
    args_schema=DemoInput,
    data_model=DemoData,
)
def unexpected_error_demo(value: str) -> dict[str, Any]:
    raise RuntimeError(f"sensitive detail: {value}")


class ToolContractTests(unittest.TestCase):
    def test_success_uses_exact_v1_envelope(self):
        result = json.loads(success_demo.invoke({"value": "ok"}))

        self.assertEqual(
            set(result),
            {"schema_version", "tool", "ok", "data", "error", "meta"},
        )
        self.assertEqual(result["schema_version"], "1.0")
        self.assertEqual(result["tool"], "success_demo")
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"], {"value": "ok"})
        self.assertIsNone(result["error"])
        self.assertEqual(result["meta"]["provider"], "test")
        self.assertIn("timestamp", result["meta"])
        self.assertIn("duration_ms", result["meta"])

    def test_expected_error_uses_common_error_shape(self):
        result = json.loads(expected_error_demo.invoke({"value": "item"}))

        self.assertFalse(result["ok"])
        self.assertIsNone(result["data"])
        self.assertEqual(result["error"]["code"], "NOT_FOUND")
        self.assertFalse(result["error"]["retryable"])

    def test_input_schema_is_strict(self):
        wrong_type = json.loads(success_demo.invoke({"value": 1}))
        extra_field = json.loads(
            success_demo.invoke({"value": "ok", "extra": "not allowed"})
        )

        self.assertEqual(wrong_type["error"]["code"], "INVALID_ARGUMENTS")
        self.assertEqual(extra_field["error"]["code"], "INVALID_ARGUMENTS")

    def test_invalid_output_is_not_reported_as_bad_input(self):
        with patch.object(logger, "disabled", True):
            result = json.loads(invalid_result_demo.invoke({"value": "bad"}))

        self.assertEqual(result["error"]["code"], "INVALID_TOOL_RESULT")
        self.assertFalse(result["error"]["retryable"])

    def test_unexpected_error_is_sanitized(self):
        with patch.object(logger, "disabled", True):
            result = json.loads(unexpected_error_demo.invoke({"value": "secret"}))

        self.assertEqual(result["error"]["code"], "INTERNAL_ERROR")
        self.assertNotIn("secret", result["error"]["message"])

    def test_schema_version_and_state_are_enforced(self):
        with self.assertRaises(ValidationError):
            ToolResult(
                schema_version="2.0",
                tool="demo",
                ok=True,
                data={},
            )

        with self.assertRaises(ValidationError):
            ToolResult(tool="demo", ok=False, data={})

    def test_async_tools_are_rejected_explicitly(self):
        async def async_demo(value: str) -> DemoData:
            return DemoData(value=value)

        with self.assertRaises(TypeError):
            standard_tool(description="async demo")(async_demo)


if __name__ == "__main__":
    unittest.main()
