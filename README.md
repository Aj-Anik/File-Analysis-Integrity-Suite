# Smart Academic Integrity & File Optimization Suite

A desktop application built with **Python 3** and **PyQt6** that combines four practical tools
into a single, polished GUI program, built specifically to demonstrate Data Structures and
Algorithms (DSA) concepts in real, working software rather than isolated exercises.

## Modules

1. **Plagiarism Detector** — compare two texts (typed or uploaded as `.txt` / `.docx` / `.pdf`)
   and get a similarity score, common/unique keywords, and matching phrases.
2. **File Compression & Decompression** — compress any file with Huffman Coding into a custom
   `.huf` container, and decompress it back losslessly.
3. **Duplicate File Finder** — recursively scan a folder and find duplicate files using
   SHA-256 content hashing, with an option to delete selected duplicates.
4. **History & Reports** — every operation above can be saved; browse, search, sort, delete
   (with undo), and re-export any past report as a PDF.
5. **About** — project description, technologies, and DSA concepts used.

## Setup

Requires Python 3.9+.

```bash
cd project
pip install -r requirements.txt
python main.py
```

If `pip install` fails on PyQt6 for your platform, try upgrading pip first:
`python -m pip install --upgrade pip`, then retry.

## Project Structure

```
project/
├── main.py                      # Entry point
├── requirements.txt
├── ui/                          # PyQt6 GUI layer (one file per module)
│   ├── main_window.py           # Sidebar nav + page switching + theming
│   ├── plagiarism_ui.py
│   ├── compression_ui.py
│   ├── duplicate_ui.py
│   ├── history_ui.py
│   ├── about_ui.py
│   ├── theme.py                 # Light/Dark QSS stylesheets
│   └── widgets.py                # Shared custom widgets (drop zone, gauge, stat card)
├── algorithms/                  # Pure-Python DSA logic, no PyQt dependency
│   ├── plagiarism.py             # File reading + comparison orchestration
│   ├── similarity.py              # Jaccard, Cosine, Rabin-Karp, KMP
│   ├── huffman.py                 # Huffman coding compress/decompress
│   ├── duplicate_detector.py      # SHA-256 based duplicate detection
│   ├── search_sort.py             # Merge sort, quick sort, linear/binary search
│   └── pdf_export.py              # Generates PDF reports via reportlab
├── models/                      # Data models + persistence
│   ├── report.py                  # Report dataclass
│   ├── history.py                  # HistoryManager + UndoStack + RecentActivityQueue
│   └── file_info.py                # FileInfo dataclass for scanned files
├── utils/
│   └── paths.py                   # Shared project-relative path constants
├── data/
│   ├── history/history.json       # Persisted history (auto-created)
│   └── reports/                   # Default folder offered when exporting PDFs
└── assets/
```

## DSA Concepts Demonstrated (for viva reference)

| Concept | Where it's used |
|---|---|
| Arrays / Lists | Tokenized word lists, file scan results, history records |
| Hash Tables (dict) | Term-frequency vectors, Huffman frequency table, duplicate hash buckets |
| Sets | Jaccard similarity, common/unique keyword extraction |
| Stacks | `UndoStack` in `models/history.py` — undo last delete |
| Queues | `RecentActivityQueue` (bounded `collections.deque`) — Recent Activity panel |
| Priority Queue (Heap) | `heapq` used to build the Huffman tree in `algorithms/huffman.py` |
| Binary Trees | The Huffman coding tree (`HuffmanNode`) |
| String Matching | Rabin-Karp (rolling hash) and KMP (prefix function), `algorithms/similarity.py` |
| Searching | Linear search, binary search, fuzzy substring search, `algorithms/search_sort.py` |
| Sorting | Merge sort and quick sort (custom implementations), same file |

## Notes

- All persistence is plain JSON (`data/history/history.json`) — no database required.
- The Huffman `.huf` file format is custom and self-describing (stores its own frequency
  table), so compressed files don't depend on any external metadata.
- Every long-running operation (comparison, compression, directory scan) runs on a background
  `QThread` so the UI never freezes.
- Before submitting, update the "Developer Information" section in the About tab
  (`ui/about_ui.py`) with your name, student ID, and course details.
