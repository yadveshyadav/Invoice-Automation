#!/usr/bin/env python3
"""Remove comments from source files in the invoice-automation project.

Creates a backup for each modified file with a `.bak` suffix.

Usage: python tools/remove_comments.py
"""
import os
import io
import sys
import re
import tokenize

ROOT_DIR_NAME = "invoice-automation"
EXCLUDE_DIRS = {"venv", ".venv", "node_modules", ".git", "build", "dist"}
TARGET_EXTS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".css",
    ".scss",
    ".html",
    ".json",
}


def find_root():
    cwd = os.getcwd()
    # walk up until we find the ROOT_DIR_NAME or stop at drive root
    path = cwd
    while True:
        candidate = os.path.join(path, ROOT_DIR_NAME)
        if os.path.isdir(candidate):
            return candidate
        parent = os.path.dirname(path)
        if parent == path:
            # not found; fallback to cwd
            return cwd
        path = parent


def strip_python_comments(src: str) -> str:
    # Use the tokenize module to remove COMMENT tokens while preserving strings/docstrings
    out = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(src).readline)
    except Exception:
        return src
    for tok_type, tok_str, start, end, line in tokens:
        if tok_type == tokenize.COMMENT:
            continue
        out.append(tok_str)
    return "".join(out)


def strip_c_like_comments(src: str) -> str:
    # Remove /* ... */ and //... comments. Naive but effective for most files.
    # First remove block comments
    src = re.sub(r"/\*[\s\S]*?\*/", "", src)
    # Then remove line comments
    src = re.sub(r"(?m)//.*$", "", src)
    return src


def strip_html_comments(src: str) -> str:
    return re.sub(r"<!--([\s\S]*?)-->", "", src)


def process_file(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, "r", encoding="utf-8") as f:
            src = f.read()
    except Exception:
        return False

    if ext == ".py":
        new = strip_python_comments(src)
    elif ext in {".js", ".jsx", ".ts", ".tsx", ".css", ".scss", ".json"}:
        new = strip_c_like_comments(src)
    elif ext == ".html":
        new = strip_html_comments(src)
    else:
        return False

    if new != src:
        bak = path + ".bak"
        if not os.path.exists(bak):
            try:
                with open(bak, "w", encoding="utf-8") as f:
                    f.write(src)
            except Exception:
                pass
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new)
        except Exception:
            return False
        return True
    return False


def main():
    root = find_root()
    print("Root for processing:", root)
    modified = 0
    scanned = 0
    for dirpath, dirnames, filenames in os.walk(root):
        # prune excluded directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            scanned += 1
            path = os.path.join(dirpath, fn)
            ext = os.path.splitext(fn)[1].lower()
            if ext in TARGET_EXTS:
                ok = process_file(path)
                if ok:
                    modified += 1
                    print("Modified:", path)
    print(f"Scanned {scanned} files. Modified {modified} files.")


if __name__ == "__main__":
    main()
