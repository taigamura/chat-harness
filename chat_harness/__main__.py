"""Entry point for chat-harness."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click

from chat_harness import __version__
from chat_harness.config import load_config
from chat_harness.repl import run_repl


@click.command()
@click.version_option(__version__, prog_name="chat-harness")
@click.option("--config", default=None, help="Path to config.yaml")
def main(config: str | None) -> None:
    """chat-harness: local Qwen+MCP vault assistant."""
    cfg = load_config(Path(config) if config else None)
    asyncio.run(run_repl(cfg))


if __name__ == "__main__":
    main()
