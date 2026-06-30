from pathlib import Path
import typer

from reverse_vibecoding.template_resolver import LEVEL_ORDER
from reverse_vibecoding.bug_seeds import BUG_SEEDS
from reverse_vibecoding.cli.helpers import (
    DoctorOptions,
    ImportProjectOptions,
    InitProjectOptions,
    NO_DATABASE,
    NO_DOMAIN,
    doctor as run_doctor,
    import_project,
    init_project,
    open_project,
)

app = typer.Typer(help="Reverse Vibe Coding project generator.", no_args_is_help=True)

BACKEND_STACK_OPTIONS = ("fastapi", "nodejs", "flask", "django", "spring_boot")
FRONTEND_STACK_OPTIONS = ("react_native", "vue", "react", "angular")
DOMAIN_OPTIONS = (NO_DOMAIN, "todo_app", "habit_tracker", "expense_tracker")
DATABASE_OPTIONS = (NO_DATABASE, "sqlite", "postgresql_local", "postgresql_supabase")
LEVEL_OPTIONS = LEVEL_ORDER["fastapi"]
BUG_CATEGORY_OPTIONS = tuple(sorted({bug.category for bug in BUG_SEEDS}))


def _options_help(label: str, values: tuple[str, ...], default: str) -> str:
    return f"{label}. Options: {', '.join(values)}. Default: {default}."


@app.callback()
def main() -> None:
    """Reverse Vibe Coding project generator."""


@app.command()
def init(
    name: str = typer.Argument(..., help="Project folder name under the sandbox root."),
    backend_stack: str = typer.Option(
        "fastapi",
        help=_options_help("Backend stack", BACKEND_STACK_OPTIONS, "fastapi"),
    ),
    frontend_stack: str = typer.Option(
        "react_native",
        help=_options_help("Frontend stack", FRONTEND_STACK_OPTIONS, "react_native"),
    ),
    domain: str = typer.Option(
        "todo_app",
        help=_options_help("Domain overlay to apply", DOMAIN_OPTIONS, "todo_app"),
    ),
    database: str = typer.Option(
        "sqlite",
        help=_options_help("Backend database overlay to apply", DATABASE_OPTIONS, "sqlite"),
    ),
    backend_level: str = typer.Option(
        "level_3",
        help=_options_help("Backend completeness level", LEVEL_OPTIONS, "level_3"),
    ),
    frontend_level: str = typer.Option(
        "level_3",
        help=_options_help("Frontend completeness level", LEVEL_OPTIONS, "level_3"),
    ),
    templates_root: Path = typer.Option(Path("templates"), help="Template root directory."),
    sandbox_root: Path = typer.Option(Path("sandbox"), help="Generated project root directory. Do not change unless you know what you're doing."),
    force: bool = typer.Option(False, "--force", help="Allow overwriting of existing project. Use with caution."),
    setup_environment: bool = typer.Option(True, "--setup/--no-setup", help="Open the project and install dependencies after generation."),
    bug_seed_count: int = typer.Option(0, "--bug-seed-count", min=0, help="Number of controlled bug seeds to apply. Default: 0 for a clean repo."),
    bug_seed_random_seed: int | None = typer.Option(None, "--bug-seed-random-seed", help="Random seed for reproducible bug seed selection."),
    bug_categories: list[str] | None = typer.Option(
        None,
        "--bug-category",
        help=_options_help(
            "Restrict bug seeds to a category. Can be passed multiple times",
            BUG_CATEGORY_OPTIONS,
            "none",
        ),
    ),
    bug_hidden: bool = typer.Option(False, "--bug-hidden", help="Hide selected bug type and target details in hidden metadata."),
    no_bugs: bool = typer.Option(False, "--no-bugs", help="Force a clean repo with no bug seeds."),
) -> None:
    """Generate a project into sandbox.

    Available values:

    backend-stack: fastapi, nodejs, flask, django, spring_boot
    frontend-stack: react_native, vue, react, angular
    domain: no_domain, todo_app, habit_tracker, expense_tracker
    database: no_database, sqlite, postgresql_local, postgresql_supabase
    backend-level/frontend-level: level_1, level_2, level_3, level_4
    bug-category: api_integration, boundary_status_code, environment_config,
    http_status, partial_update, response_shape, route_mismatch, validation
    """

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
    if setup_environment and result.project_opened:
        typer.echo("[init:setup] Project opened in a new VS Code window")
    elif setup_environment:
        typer.echo(f"[init:setup] Open manually: code -n {result.target}")
    if setup_environment and result.setup_process_launched:
        typer.echo("[init:setup] Dependency installation started; log: " + (result.target / ".rv" / "setup.log").as_posix())
    elif setup_environment:
        typer.echo("[init:setup] Run dependency setup manually from the generated project root; see README.md for stack-aware commands")


@app.command(name="import")
def import_existing_project(
    absolute_path_to_project: Path = typer.Argument(..., help="Absolute path to an existing project directory."),
    agents_root: Path = typer.Option(Path(".agents"), help="Agent support directory to copy into the project."),
) -> None:
    """Install reverse-vibecoding agent files into an existing project."""

    try:
        result = import_project(
            ImportProjectOptions(
                target=absolute_path_to_project,
                agents_root=agents_root,
                mentor_prompt_path=agents_root / "global_prompt.md",
                mentor_guardrails_path=agents_root / "global_guardrails.md",
            ),
            progress=typer.echo,
        )
    except (FileExistsError, FileNotFoundError, NotADirectoryError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    handoff_path = (result.target / ".rv" / "agent_handoff.md").as_posix()
    short_handoff_path = (result.target / ".rv" / "agent_handoff_short.md").as_posix()
    typer.echo(f"[import:done] Imported reverse-vibecoding agent files into {result.target}")
    typer.echo(f"[import:done] Files written: {len(result.agent_files)}")
    typer.echo("[import:agent] To wake your IDE agent, paste this:")
    typer.echo(f"  Read {handoff_path} and start the reverse-vibecoding workflow.")
    typer.echo("For short-context agents, paste this instead:")
    typer.echo(f"  Read {short_handoff_path} and start the reverse-vibecoding workflow.")


@app.command()
def doctor(
    agents_root: Path = typer.Option(Path(".agents"), help="Agent support directory to check."),
    templates_root: Path = typer.Option(Path("templates"), help="Template root directory to check."),
    sandbox_root: Path = typer.Option(Path("sandbox"), help="Sandbox root directory to check."),
) -> None:
    """Check local rev-vib environment readiness."""

    result = run_doctor(
        DoctorOptions(
            agents_root=agents_root,
            templates_root=templates_root,
            sandbox_root=sandbox_root,
        )
    )
    for check in result.checks:
        if check.ok:
            status = "ok"
        elif check.required:
            status = "error"
        else:
            status = "warn"
        typer.echo(f"[doctor:{status}] {check.name}: {check.message}")
    if not result.ok:
        raise typer.Exit(code=1)


@app.command(name="open")
def open_existing_project(
    project: Path = typer.Argument(..., help="Sandbox project name or path to a generated/imported project."),
    sandbox_root: Path = typer.Option(Path("sandbox"), help="Sandbox root used when PROJECT is a name."),
) -> None:
    """Open a generated or imported project in VS Code."""

    try:
        result = open_project(project, sandbox_root=sandbox_root)
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    if result.opened:
        typer.echo(f"[open:done] Project opened in VS Code: {result.target}")
    else:
        typer.echo(f"[open:warn] VS Code CLI not found on PATH; open manually: {result.target}")
    typer.echo("[open:agent] To wake your IDE agent, paste this:")
    typer.echo(f"  Read {result.handoff_path.as_posix()} and start the reverse-vibecoding workflow.")
    typer.echo("For short-context agents, paste this instead:")
    typer.echo(f"  Read {result.short_handoff_path.as_posix()} and start the reverse-vibecoding workflow.")


if __name__ == "__main__":
    app()
