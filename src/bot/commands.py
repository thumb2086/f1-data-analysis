from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .render import render_markdown, render_text, response_to_json
from .services import BotService
from .types import COMMAND_SPECS, BotResponse


Handler = Callable[[BotService, dict[str, Any]], BotResponse]


@dataclass
class CommandExecution:
    response: BotResponse
    text: str
    markdown: str
    json_text: str


class BotCommandRunner:
    """Simple command handler registry for the bot scaffold."""

    def __init__(self, service: BotService) -> None:
        self.service = service
        self._handlers: dict[str, Handler] = {
            "standings": lambda svc, kwargs: svc.get_standings_response(),
            "strategy": lambda svc, kwargs: svc.get_strategy_response(),
            "compare": lambda svc, kwargs: svc.get_compare_response(
                user_csv=kwargs.get("user_csv"),
                benchmark_csv=kwargs.get("benchmark_csv"),
                output_dir=kwargs.get("output_dir"),
            ),
            "weather": lambda svc, kwargs: svc.get_weather_response(),
            "telemetry": lambda svc, kwargs: svc.get_telemetry_response(driver=kwargs.get("driver")),
            "laps": lambda svc, kwargs: svc.get_laps_response(driver=kwargs.get("driver")),
        }

    @property
    def available_commands(self) -> list[str]:
        return [spec.name for spec in COMMAND_SPECS]

    def run(self, command: str, **kwargs: Any) -> BotResponse:
        if command not in self._handlers:
            raise KeyError(f"Unknown bot command: {command}")
        return self._handlers[command](self.service, kwargs)

    def render(self, command: str, **kwargs: Any) -> CommandExecution:
        response = self.run(command, **kwargs)
        return CommandExecution(
            response=response,
            text=render_text(response),
            markdown=render_markdown(response),
            json_text=response_to_json(response),
        )
