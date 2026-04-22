# prunefiles

A CLI tool to prune files like old logs.

## Installation

``` shell
uv tool install git+https://github.com/Cologler/prunefiles-python
```

## Usage

The following example shows how to prune log files with the name pattern `PREFIX-0000.log`:

``` shell
prunefiles \
    --match-format 'PREFIX-{seq:d}.log' \
    --orderby seq \
    --keep-count 5 \
    --keep-size 20MiB \
    {DIRECTORY}
```

### Options

- **`--match-format FORMAT`**: Match files by name using a format string. See https://github.com/r1chardj0n3s/parse for syntax details.
- **`--match-regex PATTERN`**: Match files by name using a regular expression. See https://docs.python.org/3/library/re.html#regular-expression-syntax for syntax details.
- **`--match-case-sensitive`**: Perform case-sensitive matching. Default is case-insensitive.
- **`--match-folder-only`**: Match folders only. Default matches files only.
- **`--match-file-and-folder`**: Match both files and folders.
- **`--orderby FIELD`**: Sort by a field captured from `--match-format` or `--match-regex`. Leave empty to sort by name.
- **`--order-reverse`**: Sort in reverse order.
- **`--keep-count COUNT`**: Keep only the specified number of files (others will be pruned).
- **`--keep-size SIZE`**: Keep files up to the specified total size (e.g., `20MiB`, `1GiB`). Files exceeding this limit will be pruned.
- **`--move-to-trash`**: Move files to trash instead of permanently deleting them.
- **`--dry-run`**: Show what would be deleted without actually deleting anything.
