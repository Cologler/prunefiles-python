# -*- coding: utf-8 -*-
# 
# Copyright (c) 2024~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

from functools import cached_property
from pathlib import Path
from typing import Annotated, Any

import humanfriendly
import parse
import rich
import typer


class _PathState:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.orderby: Any = self.path.stem
        self.is_match = True
        self.prune_reasons: list[str] = []

    def __str__(self) -> str:
        return str(self.path)

    @cached_property
    def size(self) -> int:
        return self.path.stat().st_size


def prune_files(
        folder: Annotated[
            Path,
            typer.Argument(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
        ],
        match_format: Annotated[str, typer.Option(help="match format, see https://github.com/r1chardj0n3s/parse")] = None,
        orderby: Annotated[str, typer.Option()] = None,
        keep_count: Annotated[int, typer.Option()] = None,
        keep_size: Annotated[str, typer.Option()] = None,
        dry_run: Annotated[bool, typer.Option('--dry-run')] = False,
    ):

    # check args

    if keep_count is not None and keep_count <= 0:
        rich.print('keep-count must be > 0')
        raise typer.Exit(1)

    keep_size_bytes: int | None = None
    if keep_size is not None:
        try:
            keep_size_bytes = humanfriendly.parse_size(keep_size)
        except humanfriendly.InvalidSize:
            rich.print('keep-size must be a valid size')
            raise typer.Exit(1)

    # print execute info
    rich.print(f"Pruning files in [green]{folder}[/]")

    # collect files
    files: list[_PathState] = [_PathState(path) for path in folder.iterdir() if path.is_file()]

    # filter
    files.sort(key=lambda x: x.path.name)

    if match_format:
        for file in files:
            if match := parse.parse(match_format, file.path.name):
                if orderby:
                    file.orderby = match.named[orderby]
            file.is_match = bool(match)

    if excluded := [x for x in files if not x.is_match]:
        rich.print('[yellow]Excluded[/]:')
        [rich.print(f'   [green]{x}[/]') for x in excluded]
    files = [x for x in files if x.is_match]

    # sort
    files.sort(key=lambda x: x.orderby)

    # prune

    if keep_count is not None and keep_count > 0:
        for file in files[:-keep_count]:
            file.prune_reasons.append(f'keep-count <= {keep_count}')

    if keep_size_bytes is not None:
        sum_of_size = 0
        for file in reversed(files):
            sum_of_size += file.size
            if sum_of_size > keep_size_bytes:
                file.prune_reasons.append(f'keep-size <= {keep_size}')

    if keep := [x for x in files if not x.prune_reasons]:
        rich.print('[cyan]Keep[/]:')
        for file in keep:
            rich.print(f'   ([blue]{file.orderby!r}[/]) [green]{file}[/]')

    if remove := [x for x in files if x.prune_reasons]:
        rich.print('[red]Remove[/]:')
        for file in remove:
            rich.print(f'   ([blue]{file.orderby!r}[/]) [green]{file}[/] by {file.prune_reasons[0]}')
            if dry_run:
                rich.print('       Skipped by [yellow]--dry-run[/]')
            else:
                file.path.unlink()

def main():
    typer.run(prune_files)
