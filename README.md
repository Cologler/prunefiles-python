# prunefiles

A CLI tool to prune files like old logs.

## Installation

``` shell
pipx install git+https://github.com/Cologler/prunefiles-python
```

## Usage

The example show how to prune log files with name `PREFIX-0000.log`.

``` shell
prunefiles
    --match-format 'PREFIX-{seq:d}.log'
    --orderby seq
    --keep-count 5
    --keep-size 20MiB
    {DIRECTORY}
```

- `match-format`: see https://github.com/r1chardj0n3s/parse for syntax.
- `orderby`: the value of `seq` is captured from the `match-format`.
