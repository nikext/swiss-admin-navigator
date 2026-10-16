"""Routing for navigator_v2 (M8, ADR-030): the router's output, dispatch, search scope.

Pure logic, unit-tested. The SR lists mirror `corpus/acts.yaml` (a test keeps
them in sync); they are spelled out here because the agent ships without the
corpus folder.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from agents.navigator.contract import Lang

Domain = Literal["residence", "work", "housing", "tax", "mobility", "general"]
SPECIALISTS: tuple[Domain, ...] = ("residence", "work", "housing", "tax", "mobility")
GENERALIST: Domain = "general"

# Acts per domain (corpus/acts.yaml `domain`). OR (220) serves work and housing.
DOMAIN_ACTS: dict[Domain, tuple[str, ...]] = {
    "general": ("101", "210", "235.1"),
    "residence": ("142.20", "142.201", "142.203", "0.142.112.681", "141.0", "141.01", "431.02"),
    "work": ("220", "822.11", "831.10", "837.0", "834.1", "832.10", "832.102"),
    "housing": ("220", "221.213.11"),
    "tax": ("642.11", "642.14", "642.118.2"),
    "mobility": ("741.01", "741.51"),
}


class Route(BaseModel):
    language: Lang = Field(description="Language of the user's latest message.")
    domains: list[Domain] = Field(
        description="Domains the latest question needs, most important first; usually one."
    )


def parse_route(route: Route | dict[str, Any] | None) -> Route | None:
    if route is None or isinstance(route, Route):
        return route
    try:
        return Route.model_validate(route)
    except ValueError:
        return None


def dispatch(route: Route | dict[str, Any] | None) -> Domain:
    """The specialist of the question's primary (first) domain; the generalist
    (navigator_v1's prompt, all acts) for general or unclear questions."""
    parsed = parse_route(route)
    return parsed.domains[0] if parsed and parsed.domains else GENERALIST


def search_scope(domains: list[Domain]) -> list[str]:
    """The acts of every domain the question touches, plus the general ones (BV, ZGB,
    DSG). Empty for the generalist (no filter)."""
    if not domains or domains[0] == GENERALIST:
        return []
    touched: list[Domain] = [*domains, GENERALIST]
    acts = [sr for d in touched for sr in DOMAIN_ACTS[d]]
    return list(dict.fromkeys(acts))


def route_scope(route: Route | dict[str, Any] | None, fallback: Domain) -> list[str]:
    """Search scope for this turn: from the router's domains, else the specialist's own."""
    parsed = parse_route(route)
    domains: list[Domain] = parsed.domains if parsed and parsed.domains else [fallback]
    return search_scope(domains)


def scope_search_args(args: dict[str, Any], scope: list[str]) -> None:
    """Default `search_law`'s `sr` to the turn's scope, in place.

    An `sr` the model passes wins; `sr: []` means every act (sent as no filter)."""
    sr = args.get("sr")
    if sr is None:
        if scope:
            args["sr"] = list(scope)
    elif sr == []:
        args.pop("sr")
