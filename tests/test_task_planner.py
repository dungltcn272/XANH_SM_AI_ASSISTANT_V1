import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "backend" / "app" / "assistant" / "orchestrator" / "task_planner.py"
spec = importlib.util.spec_from_file_location("task_planner", MODULE_PATH)
task_planner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(task_planner)
plan_tools = task_planner.plan_tools


def test_driver_rag_uses_driver_rag_tool():
    assert plan_tools("rag", "driver") == ["rag_driver"]


def test_driver_support_for_customer_falls_back_to_rag():
    assert plan_tools("driver_support", "customer") == ["rag"]


def test_driver_support_for_driver_uses_realtime_tools():
    assert plan_tools("driver_support", "driver") == ["ride_status", "charging", "demand_heatmap"]
