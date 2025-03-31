import textwrap
from typing import Callable


def function(
    name: str,
    args: dict[str, str],
    comment: str = "",
) -> Callable[[str], str]:
    def wrapper(body: str):
        return (
            f"{name}({' // ' + comment if comment else ''}\n"
            + textwrap.indent(",\n".join([f"{k}: {v}" for k, v in args.items()]), "  ")
            + ",\n"
            + textwrap.indent(body, "  ")
            + "\n)"
        )

    return wrapper


def compute_gutter(space: float, n: int):
    return space / (n + (n - 1) * space)
