import argparse
import os
import re
from collections import namedtuple

DirEntry = namedtuple('DirEntry', ['file_path', 'file_type', 'file_hash', 'file_size', 'file_permissions'])
DirEntryProps = namedtuple('DirEntry', ['file_type', 'file_hash', 'file_size', 'file_permissions'])


def build_dirtree(base_path, return_hashes=False, return_sizes=False, return_perms=False, exclude_pattern=None):
    '''Build a `set` of tuples for each file under the given filepath

    The tuples are of the form

        (file_path, file_type, file_hash, file_size, file_permissions)

    For directories `file_hash` is always `None`.
    '''
    tree = dict()
    set_dirtree = set()
    for dirpath, dirnames, filenames in os.walk(base_path):
        dir_entries = [(f, 'F') for f in filenames] + [(d, 'D') for d in dirnames]

        for entry, entry_type in dir_entries:
            full_rel_path = os.path.join(dirpath, entry)
            path = full_rel_path[len(base_path):]

            if exclude_pattern and exclude_pattern.match(path):
                continue

            stat = os.stat(full_rel_path)
            file_props = {
                'file_type': entry_type,
                'file_hash': None,
                'file_size': stat.st_size if return_sizes and entry_type == 'F' else None,
                'file_permissions': stat.mode if return_perms else None,
            }
            dir_entry = DirEntry(
                file_path=path,
                **file_props,
            )
            set_dirtree.add(dir_entry)
            tree[path] = DirEntryProps(**file_props)

    return set_dirtree, tree


def pp_file_size(size_bytes):
    if size_bytes < 2**10:
        value = size_bytes
        unit = 'bytes'
    elif size_bytes < 2**20:
        value = size_bytes / 2**10
        unit = 'KiB'
    elif size_bytes < 2**30:
        value = size_bytes / 2**20
        unit = 'MiB'
    else:
        value = size_bytes / 2**30
        unit = 'GiB'

    return f'{value:.2f} {unit}'


def entry():
    # fmt: off
    argparser = argparse.ArgumentParser(description='A JSON-biased alternative to jq')
    argparser.add_argument('dir1', help='The jason command to run on the JSON')
    argparser.add_argument('dir2', help='The files to transform')
    # argparser.add_argument('--strict', action='store_true', help='Error on missing attributes')
    argparser.add_argument('-p', '--check-perms', action='store_true', help='Diff file permissions')
    argparser.add_argument('-s', '--check-sizes', action='store_true', help='Diff file sizes')
    argparser.add_argument('-e', '--exclude')
    # fmt: on

    args = argparser.parse_args()
    dir1 = args.dir1
    dir2 = args.dir2

    re_exclude = re.compile(args.exclude) if args.exclude else None

    set_tree1, tree1 = build_dirtree(dir1, return_sizes=args.check_sizes, return_perms=args.check_perms, exclude_pattern=re_exclude)
    set_tree2, tree2 = build_dirtree(dir2, return_sizes=args.check_sizes, return_perms=args.check_perms, exclude_pattern=re_exclude)

    diff = set_tree1 - set_tree2

    print(f'{dir1} <-> {dir2}')
    for dir_entry in sorted(diff):
        path = dir_entry.file_path
        if path in tree1 and path not in tree2:
            print(f'{path}  -> ')
        elif path not in tree1 and path in tree2:
            print(f'       <-  {path}')
        elif tree1[path].file_type != tree2[path].file_type:
            print(f'{path} ({file_type1}) <-> {path} ({file_type2})')
        elif tree1[path].file_size != tree2[path].file_size:
            file_size1 = pp_file_size(tree1[path].file_size)
            file_size2 = pp_file_size(tree2[path].file_size)
            print(f'{path} ({file_size1}) <-> {path} ({file_size2})')
        elif tree1[path].hash != tree2[path].hash:
            print(f'{path} ({hash1}) <-> {path} {hash2}')
        elif tree1[path].perms != tree2[path].perms:
            print(f'{path} ({perms1}) <-> {path} {perms2}')


if __name__ == '__main__':
    entry()
