from rich.console import Console

info = Console(style="dim")
success = Console(style="green")
err = Console(stderr=True, style="red")


def print_info(message: str) -> None:
    info.print(message)


def print_success(message: str) -> None:
    success.print(message)


def print_error(message: str) -> None:
    err.print(message)
