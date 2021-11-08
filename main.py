import argparse
import hashlib
import os
import re
import stat
from collections import namedtuple
from itertools import cycle

DirEntry = namedtuple(
    'DirEntry', ['file_path', 'file_type', 'file_hash', 'file_size', 'file_perms']
)
DirEntryProps = namedtuple(
    'DirEntry', ['file_type', 'file_hash', 'file_size', 'file_perms']
)


def file_hash(path):
    with open(path, 'rb') as f:
        hash = hashlib.blake2b()
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            hash.update(chunk)
    return hash.hexdigest()


def build_dirtree(
    base_path,
    return_hashes=False,
    return_sizes=False,
    return_perms=False,
    exclude_pattern=None,
):
    '''Build a `set` of tuples for each file under the given filepath

    The tuples are of the form

        (file_path, file_type, file_hash, file_size, file_perms)

    For directories `file_hash` is always `None`.
    '''
    tree = dict()
    set_dirtree = set()
    for dirpath, dirnames, filenames in os.walk(base_path):
        dir_entries = [(f, 'F') for f in filenames] + [(d, 'D') for d in dirnames]

        for entry, entry_type in dir_entries:
            full_rel_path = os.path.join(dirpath, entry)
            path = full_rel_path[len(base_path) :]

            if exclude_pattern and exclude_pattern.match(path):
                continue

            stat = os.stat(full_rel_path)
            file_props = {
                'file_type': entry_type,
                'file_hash': file_hash(full_rel_path) if return_hashes else None,
                'file_size': stat.st_size
                if return_sizes and entry_type == 'F'
                else None,
                'file_perms': stat.st_mode if return_perms else None,
            }
            dir_entry = DirEntry(
                file_path=path,
                **file_props,
            )
            set_dirtree.add(dir_entry)
            tree[path] = DirEntryProps(**file_props)

    return set_dirtree, tree


def pp_file_size(size_bytes):
    if size_bytes < 2 ** 10:
        value = size_bytes
        unit = 'bytes'
    elif size_bytes < 2 ** 20:
        value = size_bytes / 2 ** 10
        unit = 'KiB'
    elif size_bytes < 2 ** 30:
        value = size_bytes / 2 ** 20
        unit = 'MiB'
    else:
        value = size_bytes / 2 ** 30
        unit = 'GiB'

    if unit == 'bytes':
        return f'{value} {unit}'
    else:
        return f'{value:.2f} {unit}'


def pp_file_perms(perms):
    CONST_FILE_PERMS = [
        stat.S_IRUSR,
        stat.S_IWUSR,
        stat.S_IXUSR,
        stat.S_IRGRP,
        stat.S_IWGRP,
        stat.S_IXGRP,
        stat.S_IROTH,
        stat.S_IWOTH,
        stat.S_IXOTH,
    ]
    result = ''
    for char, stat_const in zip(cycle(['r', 'w', 'x']), CONST_FILE_PERMS):
        if perms & stat_const != 0:
            result += char
        else:
            result += '-'
    return result


def entry():
    # fmt: off
    argparser = argparse.ArgumentParser(description='Easily compare the contents of two directories')
    argparser.add_argument('dir1', help='The jason command to run on the JSON')
    argparser.add_argument('dir2', help='The files to transform')
    # argparser.add_argument('--strict', action='store_true', help='Error on missing attributes')
    argparser.add_argument('-p', '--check-perms', action='store_true', help='Diff file permissions')
    argparser.add_argument('-s', '--check-sizes', action='store_true', help='Diff file sizes')
    argparser.add_argument('-z', '--check-hashes', action='store_true', help='Diff file hashes')
    argparser.add_argument('-e', '--exclude', help='Exclude files matching this regex', metavar='exclude_regex')
    # fmt: on

    args = argparser.parse_args()
    dir1 = args.dir1
    dir2 = args.dir2

    re_exclude = re.compile(args.exclude) if args.exclude else None

    if not os.path.exists(dir1):
        print(f'"{dir1}" does not exist')
        return
    if not os.path.exists(dir2):
        print(f'"{dir2}" does not exist')
        return

    set_tree1, tree1 = build_dirtree(
        dir1,
        return_sizes=args.check_sizes,
        return_perms=args.check_perms,
        return_hashes=args.check_hashes,
        exclude_pattern=re_exclude,
    )
    set_tree2, tree2 = build_dirtree(
        dir2,
        return_sizes=args.check_sizes,
        return_perms=args.check_perms,
        return_hashes=args.check_hashes,
        exclude_pattern=re_exclude,
    )

    diff = set_tree1.symmetric_difference(set_tree2)

    if len(set_tree1) == 0 and len(set_tree2) == 0:
        print('Both directories are empty')
        return
    elif len(diff) == 0:
        print('Directories are identical')
        return

    width = len(dir1)
    print(f'{dir1} <-> {dir2}')
    visited = set()
    for dir_entry in sorted(diff):
        path = dir_entry.file_path
        if path in visited:
            continue
        else:
            visited.add(path)

        if path in tree1 and path not in tree2:
            padded_path = (path + ' ' * width)[:max(width, len(path))]
            print(f'{padded_path}  -> ')
        elif path not in tree1 and path in tree2:
            print(' ' * width + f' <-  {path}')
        elif tree1[path].file_type != tree2[path].file_type:
            print(f'{path} ({file_type1}) <-> {path} ({file_type2})')
        elif tree1[path].file_size != tree2[path].file_size:
            file_size1 = pp_file_size(tree1[path].file_size)
            file_size2 = pp_file_size(tree2[path].file_size)
            print(f'{path} ({file_size1}) <-> {path} ({file_size2})')
        elif tree1[path].file_hash != tree2[path].file_hash:
            file_hash1 = tree1[path].file_hash
            file_hash2 = tree2[path].file_hash
            print(f'{path} ({file_hash1[:6]}) <-> {path} ({file_hash2[:6]})')
        elif tree1[path].file_perms != tree2[path].file_perms:
            file_perms1 = pp_file_perms(tree1[path].file_perms)
            file_perms2 = pp_file_perms(tree2[path].file_perms)
            print(f'{path} ({file_perms1}) <-> {path} ({file_perms2})')


if __name__ == '__main__':
    entry()
