# -*- coding: utf-8 -*-
# 
# Copyright (c) 2024~2999 - Cologler <skyoflw@gmail.com>
# ----------
# 
# ----------

import re
from functools import cached_property
from pathlib import Path
from typing import Annotated, Any

import humanfriendly
import parse
import rich
import typer


class ParseMatcher:
    def __init__(self, format: str, case_sensitive: bool) -> None:
        self.__parser = parse.compile(format, case_sensitive=case_sensitive)

    def match(self, value: str) -> parse.Result | None:
        return self.__parser.parse(value)

    def get_value(self, match_result: parse.Result, name: str) -> Any:
        return match_result[name]


class RegexMatcher:
    def __init__(self, pattern: str, case_sensitive: bool) -> None:
        self.__pattern = re.compile(pattern, re.IGNORECASE if not case_sensitive else 0)

    def match(self, value: str) -> re.Match | None:
        return self.__pattern.fullmatch(value)

    def get_value(self, match_result: re.Match, name: str) -> Any:
        return match_result.group(name)


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


class CountLimiter:
    def __init__(self, max_count: int, reason: str) -> None:
        assert max_count > 0
        self.__max_count = max_count
        self.__reason = reason

    def apply(self, files: list[_PathState]) -> bool:
        for file in files[:-self.__max_count]:
            file.prune_reasons.append(self.__reason)


class SizeLimiter:
    def __init__(self, max_size: int, reason: str) -> None:
        assert max_size >= 0
        self.__max_size = max_size # max size in bytes
        self.__reason = reason

    def apply(self, files: list[_PathState]) -> bool:
        sum_of_size = 0
        for file in reversed(files):
            sum_of_size += file.size
            if sum_of_size > self.__max_size:
                file.prune_reasons.append(self.__reason)


def prune_files(
        folder: Annotated[
            Path,
            typer.Argument(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
        ],

        match_format: Annotated[str, typer.Option(
            help="match format, alsosee https://github.com/r1chardj0n3s/parse.")] = None,
        match_regex: Annotated[str, typer.Option(
            help="match regex, alsosee https://docs.python.org/3/library/re.html#regular-expression-syntax.")] = None,
        match_case_sensitive: Annotated[bool, typer.Option('--match-case-sensitive',
            help='match case sensitive, default is case-insensitive.')] = False,

        orderby: Annotated[str, typer.Option(help='captured from --match-*. leave empty to sort by name.')] = None,
        order_reverse: Annotated[bool, typer.Option('--order-reverse', help='reverse order.')] = False,

        keep_count: Annotated[int, typer.Option(help='The count of files to keep.')] = None,
        keep_size: Annotated[str, typer.Option(help='The max size of files to keep.')] = None,

        dry_run: Annotated[bool, typer.Option('--dry-run')] = False,
    ):

    # check args

    limiters = []

    if keep_count is not None:
        if keep_count > 0:
            limiters.append(CountLimiter(keep_count, f'keep-count <= {keep_count}'))
        else:
            rich.print('keep-count must be > 0')
            raise typer.Exit(1)

    keep_size_bytes: int | None = None
    if keep_size is not None:
        try:
            keep_size_bytes = humanfriendly.parse_size(keep_size)
        except humanfriendly.InvalidSize:
            rich.print('keep-size must be a valid size')
            raise typer.Exit(1)
        else:
            limiters.append(SizeLimiter(keep_size_bytes, f'keep-size <= {keep_size}'))

    if sum(int(bool(x)) for x in [match_regex, match_format]) > 1:
        rich.print('Only one of --match-format or --match-regex can be specified')
        raise typer.Exit(1)
    elif match_format:
        rich.print(f'Using --match-format: [green]{match_format}[/]')
        matcher = ParseMatcher(match_format, match_case_sensitive)
    elif match_regex:
        rich.print(f'Using --match-regex: [green]{match_regex}[/]')
        matcher = RegexMatcher(match_regex, match_case_sensitive)
    else:
        matcher = None

    # print execute info
    rich.print(f"Pruning files in [green]{folder}[/]")

    # collect files
    files: list[_PathState] = [_PathState(path) for path in folder.iterdir() if path.is_file()]

    # filter
    files.sort(key=lambda x: x.path.name)

    if matcher:
        for file in files:
            if match := matcher.match(file.path.name):
                if orderby:
                    file.orderby = matcher.get_value(match, orderby)
            file.is_match = bool(match)

    if excluded := [x for x in files if not x.is_match]:
        rich.print('[yellow]Excluded[/]:')
        [rich.print(f'   [green]{x}[/]') for x in excluded]
    files = [x for x in files if x.is_match]

    # sort
    files.sort(key=lambda x: x.orderby, reverse=order_reverse)

    # prune

    for limiter in limiters:
        limiter.apply(files)

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
