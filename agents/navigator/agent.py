"""navigator_v1. M0 skeleton: no tools yet. M3 adds the MCP toolset,
the answer contract and the citation check (docs/AGENTS.md)."""

from pathlib import Path

from google.adk.agents import LlmAgent

from .config import load_profile

profile = load_profile()

root_agent = LlmAgent(
    name="navigator",
    description="Unofficial assistant for Swiss federal law. Not legal advice.",
    model=profile.agent_model,
    instruction=(Path(__file__).parent / "prompts" / "system.md").read_text(encoding="utf-8"),
)
