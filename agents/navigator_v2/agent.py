"""navigator_v2: router + domain specialists as an ADK dynamic workflow (M8, ADR-030).

    START -> orchestrate: router -> dispatch -> {residence|work|housing|tax|mobility}_specialist
                                             -> generalist (navigator_v1's prompt, all acts)

- `router`: an LlmAgent with structured output (`routing.Route`: language and
  domains), on the profile's `router` model; it sees the whole conversation,
  so a short reply to a clarifying question keeps its domain.
- `dispatch`: code, not a model: the primary (first) domain's specialist, or
  the generalist for general and unclear questions (`routing.dispatch`).
- Specialists are navigator_v1 agents (`build_agent`: same tools, answer
  contract, citation verifier, optional claim checker, memory) with a domain
  brief appended to the v1 prompt and `search_law` scoped to the acts of
  every domain the router named plus the general ones, unless they pass `sr`
  themselves.

Every LlmAgent runs in ADK's `chat` mode: it reads the conversation from the
session. As a workflow node an LlmAgent defaults to `single_turn`, which
appends "You will not receive any user replies or clarifications" to its
prompt and re-injects the node input as a user turn (google-adk 2.12
`_llm_agent_wrapper`); that would suppress clarifying questions. A static
graph rejects chat-mode agents after another node, so one orchestrator node
calls the agents with `ctx.run_node` (ADK's dynamic workflows).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.tools import BaseTool, ToolContext
from google.adk.workflow import Workflow, node

from agents.navigator.agent import (
    MCP_URL,
    PROMPT,
    build_agent,
    gemini,
    generate_config,
    instruction_provider,
    new_toolset,
    profile,
)
from agents.navigator.verifier import Observer

from .routing import (
    GENERALIST,
    SPECIALISTS,
    Domain,
    Route,
    dispatch,
    route_scope,
    scope_search_args,
    search_scope,
)

PROMPTS = Path(__file__).parent / "prompts"
ROUTER_PROMPT = (PROMPTS / "router.md").read_text(encoding="utf-8")
ROUTER = "router"
NAME = "navigator_v2"
ROUTE_KEY = "temp:route"  # the router's output, per invocation


def specialist_prompt(domain: Domain) -> str:
    brief = (PROMPTS / "domains" / f"{domain}.md").read_text(encoding="utf-8").strip()
    scope = ", ".join(search_scope([domain]))
    return (
        f"{PROMPT.rstrip()}\n\n## Your domain\n\n{brief}\n\n"
        f"`search_law` searches only the acts of this question's domains (yours and the "
        f"general ones: SR {scope}; plus another domain's acts when the question also touches "
        "it) unless you pass `sr` yourself: pass other SR numbers to search those, or "
        "`sr: []` to search all 23 acts.\n"
    )


def scoped_search(domain: Domain):
    def before_tool(tool: BaseTool, args: dict[str, Any], tool_context: ToolContext) -> None:
        if tool.name == "search_law":
            scope_search_args(args, route_scope(tool_context.state.get(ROUTE_KEY), domain))

    return before_tool


def build_router() -> LlmAgent:
    ref = profile.role("router")
    return LlmAgent(
        name=ROUTER,
        mode="chat",
        description="Classifies the question by language and legal domain.",
        model=gemini(ref),
        instruction=instruction_provider(ROUTER_PROMPT),
        generate_content_config=generate_config(ref),
        output_schema=Route,
        # A chat-mode node returns no output to `run_node`; the route travels through state.
        output_key=ROUTE_KEY,
    )


def build_workflow(
    mcp_url: str = MCP_URL, *, claim_check: bool | None = None, observer: Observer | None = None
) -> Workflow:
    """navigator_v2 against one MCP server; the eval harness builds its own."""
    toolset = new_toolset(mcp_url)  # one MCP session pool for every specialist
    agents: dict[str, LlmAgent] = {}
    for domain in SPECIALISTS:
        agents[domain] = build_agent(
            mcp_url,
            name=f"{domain}_specialist",
            description=f"Answers {domain} questions from Swiss federal law. Not legal advice.",
            prompt=specialist_prompt(domain),
            toolset=toolset,
            before_tool_callback=scoped_search(domain),
            claim_check=claim_check,
            observer=observer,
        )
    agents[GENERALIST] = build_agent(
        mcp_url, name="generalist", toolset=toolset, claim_check=claim_check, observer=observer
    )
    for agent in agents.values():
        agent.mode = "chat"
    router = build_router()

    @node(name="orchestrate", rerun_on_resume=True)
    async def orchestrate(ctx: Context, node_input: Any) -> Any:
        await ctx.run_node(router)
        return await ctx.run_node(agents[dispatch(ctx.state.get(ROUTE_KEY))], use_as_output=True)

    return Workflow(
        name=NAME,
        description="Unofficial assistant for Swiss federal law. Not legal advice.",
        edges=[("START", orchestrate)],
    )


root_agent = build_workflow()
