from google.adk.agents import Agent

root_agent = Agent(
    name="ripple_test_agent",
    model="gemini-3.7-flash",
    description="Initial test agent for RIPPLE.",
    instruction=(
        "You are a test agent for the RIPPLE film production intelligence project. "
        "For now, respond clearly and briefly."
    ),
)