"""
algorithms/search_sort.py

Classic searching and sorting algorithms implemented from scratch.
These are used throughout the application's UI layer wherever a list
needs to be sorted or searched (e.g. sorting duplicate file groups by
wasted size, sorting history records by date, searching report titles),
satisfying the project's explicit "Searching Algorithms" and "Sorting
Algorithms" DSA requirements.

All functions operate generically using a `key` function, similar in
spirit to Python's builtin sorted(key=...), so they can sort any list of
objects (FileInfo, Report, etc.) by any attribute.
"""

from typing import Any, Callable, List, Optional, TypeVar

T = TypeVar("T")


# ---------------------------------------------------------------------- #
# Sorting Algorithms
# ---------------------------------------------------------------------- #
def merge_sort(items: List[T], key: Callable[[T], Any] = lambda x: x, reverse: bool = False) -> List[T]:
    """
    Stable O(n log n) merge sort. Returns a NEW sorted list; does not
    mutate the input. Used for sorting larger lists (e.g. all history
    records) where guaranteed O(n log n) performance matters.
    """
    if len(items) <= 1:
        return list(items)

    mid = len(items) // 2
    left = merge_sort(items[:mid], key=key, reverse=reverse)
    right = merge_sort(items[mid:], key=key, reverse=reverse)

    return _merge(left, right, key=key, reverse=reverse)


def _merge(left: List[T], right: List[T], key: Callable[[T], Any], reverse: bool) -> List[T]:
    """Merge two already-sorted lists into one sorted list (helper for merge_sort)."""
    merged: List[T] = []
    i = j = 0
    while i < len(left) and j < len(right):
        left_val, right_val = key(left[i]), key(right[j])
        take_left = (left_val <= right_val) if not reverse else (left_val >= right_val)
        if take_left:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def quick_sort(items: List[T], key: Callable[[T], Any] = lambda x: x, reverse: bool = False) -> List[T]:
    """
    O(n log n) average-case quicksort using the Lomuto partition scheme
    with a median-of-three pivot choice (helps avoid worst-case O(n^2) on
    already-sorted or reverse-sorted input). Returns a NEW sorted list.

    Used for sorting smaller, frequently-resorted lists (e.g. the
    duplicate-file results table when the user clicks a column header).
    """
    items_copy = list(items)
    _quick_sort_inplace(items_copy, 0, len(items_copy) - 1, key, reverse)
    return items_copy


def _quick_sort_inplace(arr: List[T], low: int, high: int, key: Callable[[T], Any], reverse: bool) -> None:
    if low < high:
        pivot_index = _partition(arr, low, high, key, reverse)
        _quick_sort_inplace(arr, low, pivot_index - 1, key, reverse)
        _quick_sort_inplace(arr, pivot_index + 1, high, key, reverse)


def _partition(arr: List[T], low: int, high: int, key: Callable[[T], Any], reverse: bool) -> int:
    # Median-of-three pivot selection to reduce worst-case behavior
    mid = (low + high) // 2
    candidates = [(key(arr[low]), low), (key(arr[mid]), mid), (key(arr[high]), high)]
    candidates.sort(key=lambda pair: pair[0])
    median_index = candidates[1][1]
    arr[median_index], arr[high] = arr[high], arr[median_index]

    pivot_value = key(arr[high])
    i = low - 1
    for j in range(low, high):
        condition = (key(arr[j]) <= pivot_value) if not reverse else (key(arr[j]) >= pivot_value)
        if condition:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


# ---------------------------------------------------------------------- #
# Searching Algorithms
# ---------------------------------------------------------------------- #
def linear_search(items: List[T], target: Any, key: Callable[[T], Any] = lambda x: x) -> Optional[int]:
    """
    O(n) linear search. Returns the index of the first item whose key()
    equals target, or None if not found. Works on unsorted data -- used
    for free-text searches across history/report titles.
    """
    for i, item in enumerate(items):
        if key(item) == target:
            return i
    return None


def binary_search(items: List[T], target: Any, key: Callable[[T], Any] = lambda x: x) -> Optional[int]:
    """
    O(log n) binary search. REQUIRES `items` to already be sorted
    ascending by key(). Returns the index of a matching item, or None.
    Used for fast lookups once a list (e.g. file sizes) has been sorted.
    """
    low, high = 0, len(items) - 1
    while low <= high:
        mid = (low + high) // 2
        mid_val = key(items[mid])
        if mid_val == target:
            return mid
        elif mid_val < target:
            low = mid + 1
        else:
            high = mid - 1
    return None


def fuzzy_substring_search(items: List[T], query: str, key: Callable[[T], str] = lambda x: x) -> List[T]:
    """
    Case-insensitive substring search across a list of items, returning
    every item whose key() contains `query` as a substring. This backs
    the live "search as you type" boxes in the History & Reports and
    Duplicate Finder screens.
    """
    if not query:
        return list(items)
    query_lower = query.lower()
    return [item for item in items if query_lower in key(item).lower()]
