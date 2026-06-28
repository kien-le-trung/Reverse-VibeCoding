from pathlib import Path
import typer

from reverse_vibecoding.cli.helpers import InitProjectOptions, init_project

app = typer.Typer(help="Reverse Vibe Coding project generator.")


@app.command()
def init(
    name: str = typer.Argument(..., help="Project folder name under the sandbox root."),
    backend_stack: str = typer.Option("fastapi", help="Backend stack. Default: 'fastapi'."),
    frontend_stack: str = typer.Option("react_native", help="Frontend stack. Default: 'react_native'."),
    domain: str = typer.Option("todo_app", help="Domain overlay to apply. Default: 'todo_app'."),
    database: str = typer.Option("sqlite", help="Backend database overlay to apply. Default: 'sqlite'."),
    backend_level: str = typer.Option("level_3", help="Backend completeness level. Default: 'level_3'."),
    frontend_level: str = typer.Option("level_3", help="Frontend completeness level. Default: 'level_3'."),
    templates_root: Path = typer.Option(Path("templates"), help="Template root directory."),
    sandbox_root: Path = typer.Option(Path("sandbox"), help="Generated project root directory. Do not change unless you know what you're doing."),
    force: bool = typer.Option(False, "--force", help="Allow overwriting of existing project. Use with caution."),
    setup_environment: bool = typer.Option(True, "--setup/--no-setup", help="Open a setup terminal after generation."),
) -> None:
    """Generate a project into sandbox."""

    try:
        result = init_project(
            InitProjectOptions(
                name=name,
                backend_stack=backend_stack,
                frontend_stack=frontend_stack,
                domain=domain,
                database=database,
                backend_level=backend_level,
                frontend_level=frontend_level,
                templates_root=templates_root,
                sandbox_root=sandbox_root,
                force=force,
                setup_environment=setup_environment,
            ),
            progress=typer.echo,
        )
    except (FileExistsError, FileNotFoundError, NotADirectoryError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(f"[init:done] Generated project at {result.target}")
    typer.echo("Applied layers:")
    for layer_id in result.compose_result.applied_layers:
        typer.echo(f"  - {layer_id}")
    handoff_path = (result.target / ".rv" / "agent_handoff.md").as_posix()
    short_handoff_path = (result.target / ".rv" / "agent_handoff_short.md").as_posix()
    typer.echo("[init:agent] To wake your IDE agent, paste this:")
    typer.echo(f"  Read {handoff_path} and start the learning workflow.")
    typer.echo("For short-context agents, paste this instead:")
    typer.echo(f"  Read {short_handoff_path} and start the learning workflow.")
    if setup_environment and result.setup_terminal_launched:
        typer.echo("[init:setup] Setup terminal opened for venv and requirements installation")
    elif setup_environment:
        typer.echo("[init:setup] Run manually: python -m venv venv; .\\venv\\Scripts\\python.exe -m pip install -r requirements.txt")


if __name__ == "__main__":
    app()
