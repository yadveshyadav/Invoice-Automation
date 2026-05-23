#!/usr/bin/env python3
"""Restore files from .bak backups created by remove_comments.py

This will overwrite current files with their .bak contents and then remove the .bak files.
"""
import os


def find_root():
    cwd = os.getcwd()
    path = cwd
    while True:
        candidate = os.path.join(path, "invoice-automation")
        if os.path.isdir(candidate):
            return candidate
        parent = os.path.dirname(path)
        if parent == path:
            return cwd
        path = parent


def main(remove_backups=True):
    root = find_root()
    restored = []
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith('.bak'):
                bak_path = os.path.join(dirpath, fn)
                orig_path = bak_path[:-4]
                try:
                    with open(bak_path, 'r', encoding='utf-8') as f:
                        data = f.read()
                    with open(orig_path, 'w', encoding='utf-8') as f:
                        f.write(data)
                    restored.append(orig_path)
                    if remove_backups:
                        os.remove(bak_path)
                except Exception as e:
                    print('Failed to restore', orig_path, e)
    print(f"Restored {len(restored)} files")
    for p in restored:
        print('Restored:', p)


if __name__ == '__main__':
    main()
