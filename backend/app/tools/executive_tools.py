from app.tools.base_tool import ToolSpec
from app.tools.registry import register_tool

bi_analysis_tool = register_tool(
    ToolSpec(name="bi_analysis", group="executive", description="Analyze strategic BI questions.")
)
forecast_simulation_tool = register_tool(
    ToolSpec(name="forecast_simulation", group="executive", description="Run forecast and voucher simulations.")
)
churn_prediction_tool = register_tool(
    ToolSpec(name="churn_prediction", group="executive", description="Estimate churn risk by customer segment.")
)
expansion_advisor_tool = register_tool(
    ToolSpec(name="expansion_advisor", group="executive", description="Advise expansion by region and product.")
)
