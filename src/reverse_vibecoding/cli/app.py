from pathlib import Path
import typer

from reverse_vibecoding.cli.helpers import InitProjectOptions, init_project

app = typer.Typer(help="Reverse Vibe Coding project generator.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Reverse Vibe Coding project generator."""


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
    bug_seed_count: int = typer.Option(0, "--bug-seed-count", min=0, help="Number of controlled bug seeds to apply. Default: 0 for a clean repo."),
    bug_seed_random_seed: int | None = typer.Option(None, "--bug-seed-random-seed", help="Random seed for reproducible bug seed selection."),
    bug_categories: list[str] | None = typer.Option(None, "--bug-category", help="Restrict bug seeds to a category. Can be passed multiple times."),
    bug_hidden: bool = typer.Option(False, "--bug-hidden", help="Hide selected bug type and target details in hidden metadata."),
    no_bugs: bool = typer.Option(False, "--no-bugs", help="Force a clean repo with no bug seeds."),
) -> None:
    """Generate a project into sandbox."""

    if no_bugs:
        bug_seed_count = 0

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
                bug_seed_count=bug_seed_count,
                bug_seed_random_seed=bug_seed_random_seed,
                bug_categories=tuple(bug_categories or ()),
                bug_hidden=bug_hidden,
            ),
            progress=typer.echo,
        )
    except (FileExistsError, FileNotFoundError, NotADirectoryError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(f"[init:done] Generated project at {result.target}")
    typer.echo("Applied layers:")
    for layer_id in result.compose_result.applied_layers:
        typer.echo(f"  - {layer_id}")
    if result.bug_seeds:
        typer.echo(f"Applied bug seeds: {len(result.bug_seeds)}")
        if bug_hidden:
            typer.echo("  Details hidden. Inspect the generated project to identify the bugs.")
        else:
            for bug_seed in result.bug_seeds:
                typer.echo(f"  - {bug_seed.id} ({bug_seed.category})")
    else:
        typer.echo("Applied bug seeds: 0 (clean repo)")
    handoff_path = (result.target / ".rv" / "agent_handoff.md").as_posix()
    short_handoff_path = (result.target / ".rv" / "agent_handoff_short.md").as_posix()
    typer.echo("[init:agent] To wake your IDE agent, paste this:")
    typer.echo(f"  Read {handoff_path} and start the reverse-vibecoding workflow.")
    typer.echo("For short-context agents, paste this instead:")
    typer.echo(f"  Read {short_handoff_path} and start the reverse-vibecoding workflow.")
    if setup_environment and result.setup_terminal_launched:
        typer.echo("[init:setup] Setup terminal opened for backend and frontend dependency installation")
    elif setup_environment:
        typer.echo("[init:setup] Run manually: python -m venv venv; . .\\venv\\Scripts\\Activate.ps1; python -m pip install -r requirements.txt; cd mobile; npm install")


if __name__ == "__main__":
    app()
