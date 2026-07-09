"""Entry point stub — provides --help without a runnable REPL yet."""

import click

from chat_harness import __version__


@click.command()
@click.version_option(__version__, prog_name="chat-harness")
@click.option("--config", default=None, help="Path to config.yaml")
def main(config: str | None) -> None:
    """chat-harness: local Qwen+MCP vault assistant (work in progress)."""
    click.echo("chat-harness is not yet fully implemented. Stay tuned.")


if __name__ == "__main__":
    main()
