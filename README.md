difftree
=======
difftree is a tool that diffs two directories. It recursively walks through the directories
and lists files that are missing on either side.

By default `difftree` only checks whether a file is present or not, so files
present on both sides but with different file sizes, permissions or content
will not be listed. However, checking any of those can be enabled via
the `-s`, `-p`, and `-z` flags respectively.

Usage
-----

    > difftree dir-a/ dir-b/
    dir-a/                 <-> dir-b/
                           <-  file-only-in-dirb.txt
    file-only-in-dir-a.txt  ->

The following options are available:

      -h, --help            show this help message and exit
      -p, --check-perms     Diff file permissions
      -s, --check-sizes     Diff file sizes
      -z, --check-hashes    Diff file hashes
      -d, --dir-norecurse   Show missing directories as a single entry (don't show files in the directory)
      -e exclude_regex, --exclude exclude_regex
                            Exclude files matching this regex

Install
-------
The recommended way to install `difftree` is via [pipx]:

    pipx difftree

Alternatives
------------
UNIX built-in `diff -rq dir1 dir2` works quite well.

`rsync --dry-run -r --itemize-changes dir1 dir2` also works quite well, but
doesn't list files that are present in `dir2` but missing in `dir1`. It requires you
to parse the quite terse change format e.g. `>fcsT....` and `>f+++++++`.


[pipx]: https://github.com/pypa/pipx