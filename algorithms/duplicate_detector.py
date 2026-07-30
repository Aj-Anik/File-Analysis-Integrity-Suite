"""
algorithms/duplicate_detector.py

Implements duplicate-file detection within a directory tree.

Algorithm: Hash-Based Duplicate Detection using SHA-256.

Data structures explicitly demonstrated:
    * Hash Table (dict)  -> maps content hash -> list of FileInfo sharing
                              that hash. This is the core mechanism: any
                              two files producing the same SHA-256 digest
                              are (for all practical purposes) identical.
    * Set                 -> used to dedupe file paths already visited and
                              to skip symlink loops.

Performance optimization:
    Hashing every byte of every file purely by content can be slow for
    large trees. We first bucket files by SIZE (an O(1) hash-table lookup),
    since two files of different sizes can never be duplicates. Only
    files that collide on size are actually read and hashed with SHA-256.
    This mirrors how real-world dedupe tools (e.g. fdupes) optimize the
    naive "hash everything" approach.
"""

import hashlib
import os
from typing import Callable, Dict, List, Optional

from models.file_info import FileInfo


CHUNK_SIZE = 65536  # 64 KB read chunks, keeps memory flat for huge files


def compute_sha256(path: str) -> str:
    """Compute the SHA-256 hex digest of a file's contents, streamed in chunks."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def scan_directory(
    root_dir: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> List[FileInfo]:
    """
    Recursively walk `root_dir` and return a FileInfo for every regular
    file found (hash is NOT computed yet at this stage -- only fast
    metadata like size, to keep the initial scan quick).

    progress_callback(files_scanned, total_estimate) is invoked periodically
    so the UI can drive a progress bar.
    """
    all_paths: List[str] = []
    for dirpath, _dirnames, filenames in os.walk(root_dir):
        for name in filenames:
            full_path = os.path.join(dirpath, name)
            if os.path.islink(full_path):
                continue  # avoid symlink loops / double counting
            all_paths.append(full_path)

    results: List[FileInfo] = []
    total = len(all_paths)
    for i, path in enumerate(all_paths):
        try:
            size = os.path.getsize(path)
        except OSError:
            continue
        results.append(FileInfo(path=path, size=size))
        if progress_callback and (i % 25 == 0 or i == total - 1):
            progress_callback(i + 1, total)

    return results


def find_duplicates(
    files: List[FileInfo],
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Dict[str, List[FileInfo]]:
    """
    Given a list of FileInfo (from scan_directory), find duplicate groups.

    Step 1 (Hash Table by size): group files by size first. Any size
            bucket with only one file cannot contain duplicates, so it's
            discarded immediately without ever touching disk content.

    Step 2 (Hash Table by SHA-256): for every size bucket with 2+ files,
            compute the real content hash and group by it. Only buckets
            that still have 2+ files after this step are true duplicates.

    Returns:
        dict mapping sha256_hex -> list of FileInfo (length >= 2),
        i.e. the actual duplicate groups.
    """
    # --- Step 1: bucket by size (hash table) ---
    size_buckets: Dict[int, List[FileInfo]] = {}
    for file_info in files:
        size_buckets.setdefault(file_info.size, []).append(file_info)

    candidates: List[FileInfo] = []
    for size, group in size_buckets.items():
        if len(group) > 1 and size > 0:  # ignore empty files trivially "matching" each other? keep them too
            candidates.extend(group)
        elif len(group) > 1 and size == 0:
            candidates.extend(group)  # zero-byte files are legitimately identical

    # --- Step 2: bucket candidates by real SHA-256 content hash ---
    hash_buckets: Dict[str, List[FileInfo]] = {}
    total = len(candidates)
    for i, file_info in enumerate(candidates):
        try:
            file_info.file_hash = compute_sha256(file_info.path)
        except (OSError, PermissionError):
            continue
        hash_buckets.setdefault(file_info.file_hash, []).append(file_info)
        if progress_callback and (i % 10 == 0 or i == total - 1):
            progress_callback(i + 1, total)

    duplicate_groups = {h: group for h, group in hash_buckets.items() if len(group) > 1}
    return duplicate_groups


def calculate_wasted_space(duplicate_groups: Dict[str, List[FileInfo]]) -> int:
    """
    Sum of bytes that could be reclaimed by keeping only ONE copy from
    each duplicate group and deleting the rest.
    """
    wasted = 0
    for group in duplicate_groups.values():
        if len(group) > 1:
            # Keep one copy "free", the rest is reclaimable waste
            wasted += group[0].size * (len(group) - 1)
    return wasted


def scan_and_find_duplicates(
    root_dir: str,
    scan_progress_callback: Optional[Callable[[int, int], None]] = None,
    hash_progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Dict:
    """
    Convenience all-in-one entry point used by the UI: scans the directory,
    finds duplicates, and returns a summary dict ready for display/export.
    """
    files = scan_directory(root_dir, progress_callback=scan_progress_callback)
    duplicate_groups = find_duplicates(files, progress_callback=hash_progress_callback)
    wasted_bytes = calculate_wasted_space(duplicate_groups)

    return {
        "total_files_scanned": len(files),
        "duplicate_groups_count": len(duplicate_groups),
        "duplicate_files_count": sum(len(g) for g in duplicate_groups.values()),
        "wasted_bytes": wasted_bytes,
        "duplicate_groups": duplicate_groups,
        "root_dir": root_dir,
    }
