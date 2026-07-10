"""Rich interactive REPL for chat-harness."""

from __future__ import annotations

import asyncio

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.status import Status

from chat_harness.agent import Agent
from chat_harness.config import Config
from chat_harness.llm import LLMError, OllamaClient
from chat_harness.mcp_client import MCPClient

console = Console()

_COMMANDS = {"/exit", "/quit", "/clear"}


def _print_banner(config: Config, mcp_client: MCPClient) -> None:
    tools = mcp_client.list_tools()
    servers = sorted(set(mcp_client._tool_server.values()))  # noqa: SLF001
    server_lines = "\n".join(
        f"  [green]✓[/green] {s}" for s in servers
    ) or "  [yellow](none connected)[/yellow]"

    banner = (
        f"[bold]chat-harness[/bold]\n"
        f"Model : [cyan]{config.model}[/cyan]\n"
        f"Vault : [cyan]{config.vault_path}[/cyan]\n"
        f"Tools : [cyan]{len(tools)}[/cyan] across {len(servers)} server(s)\n"
        f"{server_lines}"
    )
    console.print(Panel(banner, expand=False))
    console.print("Type [bold]/exit[/bold] to quit, [bold]/clear[/bold] to reset history.\n")


async def run_repl(config: Config) -> None:
    """Boot all components and run the interactive REPL."""
    async with MCPClient() as mcp_client:
        async with OllamaClient(config) as llm:
            agent = Agent(config, mcp_client, llm)
            _print_banner(config, mcp_client)

            while True:
                try:
                    user_input = Prompt.ask("[bold blue]you[/bold blue]").strip()
                except (EOFError, KeyboardInterrupt):
                    console.print("\n[dim]Goodbye.[/dim]")
                    break

                if not user_input:
                    continue

                if user_input.lower() in {"/exit", "/quit"}:
                    console.print("[dim]Goodbye.[/dim]")
                    break

                if user_input.lower() == "/clear":
                    agent.clear_history()
                    console.print("[dim]History cleared.[/dim]")
                    continue

                with Status("[dim]thinking…[/dim]", console=console, spinner="dots"):
                    try:
                        answer = await agent.run(user_input)
                    except LLMError as exc:
                        console.print(f"[red]LLM error:[/red] {exc}")
                        continue
                    except Exception as exc:  # noqa: BLE001
                        console.print(f"[red]Unexpected error:[/red] {exc}")
                        continue

                console.print(Panel(Markdown(answer), title="[bold green]assistant[/bold green]", expand=False))
