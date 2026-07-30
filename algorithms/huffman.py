"""
algorithms/huffman.py

Implements file compression and decompression using Huffman Coding,
built entirely from first principles.

Data structures explicitly demonstrated:
    * Priority Queue (Min-Heap) -> built with Python's heapq module, used
                                    to repeatedly pull the two
                                    lowest-frequency nodes while building
                                    the Huffman tree.
    * Binary Tree                -> HuffmanNode forms the Huffman coding
                                    tree (each internal node has left/right
                                    children; leaves hold byte values).
    * Hash Map (dict)            -> frequency table (byte -> count) and
                                    code table (byte -> bitstring).

File format written by this module (custom, self-contained):
    [4 bytes]  magic header  b"HUF1"
    [4 bytes]  original file size in bytes (unsigned int, big-endian)
    [2 bytes]  number of bits of padding added to the final byte
    [4 bytes]  length of the serialized header table (JSON) in bytes
    [N bytes]  JSON-serialized frequency table, used to rebuild the tree
    [...]      the Huffman-encoded payload, bit-packed into bytes
"""

import heapq
import json
import struct
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


MAGIC_HEADER = b"HUF1"


# ---------------------------------------------------------------------- #
# Binary Tree node
# ---------------------------------------------------------------------- #
@dataclass(order=False)
class HuffmanNode:
    """
    A single node of the Huffman binary tree.

    Leaf nodes hold a `byte_value` (0-255) and represent one symbol.
    Internal nodes have `left` and `right` children and no byte_value.
    """
    frequency: int
    byte_value: Optional[int] = None
    left: Optional["HuffmanNode"] = None
    right: Optional["HuffmanNode"] = None
    # Tie-breaker counter so heapq has a deterministic, comparable order
    # even when two nodes share the same frequency (avoids comparing
    # HuffmanNode objects directly, which have no natural ordering).
    order: int = 0

    def is_leaf(self) -> bool:
        return self.left is None and self.right is None

    def __lt__(self, other: "HuffmanNode") -> bool:
        # Required so heapq can order nodes purely by (frequency, order)
        if self.frequency != other.frequency:
            return self.frequency < other.frequency
        return self.order < other.order


# ---------------------------------------------------------------------- #
# Step 1-2: Frequency table
# ---------------------------------------------------------------------- #
def build_frequency_table(data: bytes) -> Dict[int, int]:
    """
    Build a hash map of byte-value -> occurrence count.
    Demonstrates explicit Hash Table usage as required by the spec.
    """
    freq: Dict[int, int] = {}
    for byte in data:
        freq[byte] = freq.get(byte, 0) + 1
    return freq


# ---------------------------------------------------------------------- #
# Step 3: Build Huffman Tree using a Priority Queue (min-heap)
# ---------------------------------------------------------------------- #
def build_huffman_tree(freq_table: Dict[int, int]) -> Optional[HuffmanNode]:
    """
    Build the Huffman binary tree from a frequency table using a min-heap
    priority queue (heapq). Repeatedly pops the two lowest-frequency nodes
    and merges them into a new internal node until only the root remains.

    Returns None for empty input (e.g. an empty file).
    Returns a single leaf node if the file contains only one distinct byte.
    """
    if not freq_table:
        return None

    heap = []
    counter = 0  # tie-breaker for heap ordering
    for byte_value, frequency in freq_table.items():
        heapq.heappush(heap, HuffmanNode(frequency=frequency, byte_value=byte_value, order=counter))
        counter += 1

    if len(heap) == 1:
        # Special case: only one distinct symbol in the whole file.
        # We still need a valid tree so the symbol gets a 1-bit code.
        only_node = heap[0]
        wrapper = HuffmanNode(frequency=only_node.frequency, left=only_node, order=counter)
        return wrapper

    while len(heap) > 1:
        node_a = heapq.heappop(heap)
        node_b = heapq.heappop(heap)
        merged = HuffmanNode(
            frequency=node_a.frequency + node_b.frequency,
            left=node_a,
            right=node_b,
            order=counter,
        )
        counter += 1
        heapq.heappush(heap, merged)

    return heap[0]


# ---------------------------------------------------------------------- #
# Step 4: Generate Huffman codes by traversing the tree
# ---------------------------------------------------------------------- #
def generate_codes(root: Optional[HuffmanNode]) -> Dict[int, str]:
    """
    Traverse the Huffman tree (DFS) to produce a hash map of
    byte_value -> bitstring code (e.g. {65: '101', 66: '01'}).
    """
    codes: Dict[int, str] = {}
    if root is None:
        return codes

    def _walk(node: HuffmanNode, path: str) -> None:
        if node.is_leaf():
            # Guard against a tree with just one node and an empty path
            codes[node.byte_value] = path if path else "0"
            return
        if node.left is not None:
            _walk(node.left, path + "0")
        if node.right is not None:
            _walk(node.right, path + "1")

    _walk(root, "")
    return codes


# ---------------------------------------------------------------------- #
# Step 5-6: Compression
# ---------------------------------------------------------------------- #
def _pack_bits(bitstring: str) -> Tuple[bytes, int]:
    """
    Pack a string of '0'/'1' characters into actual bytes.
    Returns (packed_bytes, padding_bits_added).
    """
    padding = (8 - len(bitstring) % 8) % 8
    bitstring += "0" * padding

    out = bytearray()
    for i in range(0, len(bitstring), 8):
        byte_chunk = bitstring[i:i + 8]
        out.append(int(byte_chunk, 2))

    return bytes(out), padding


def compress_bytes(data: bytes) -> Tuple[bytes, Dict]:
    """
    Compress raw bytes using Huffman coding.

    Returns:
        (compressed_file_bytes, stats_dict)
        stats_dict contains original_size, compressed_size, compression_ratio,
        space_saved_percent, frequency_table, and code_table -- all of which
        the UI displays directly.
    """
    if len(data) == 0:
        # Trivial empty-file case: still produce a valid (tiny) container.
        empty_header = json.dumps({}).encode("utf-8")
        out = MAGIC_HEADER + struct.pack(">IH", 0, 0) + struct.pack(">I", len(empty_header)) + empty_header
        stats = {
            "original_size": 0, "compressed_size": len(out),
            "compression_ratio": 1.0, "space_saved_percent": 0.0,
            "frequency_table": {}, "code_table": {},
        }
        return out, stats

    freq_table = build_frequency_table(data)
    tree_root = build_huffman_tree(freq_table)
    code_table = generate_codes(tree_root)

    # Encode the whole file as one long bitstring using the code table.
    bit_parts = [code_table[byte] for byte in data]
    full_bitstring = "".join(bit_parts)
    packed_payload, padding_bits = _pack_bits(full_bitstring)

    # Serialize the frequency table as JSON (string keys, since JSON has
    # no integer keys) so the decompressor can rebuild the exact same tree.
    freq_table_str_keys = {str(k): v for k, v in freq_table.items()}
    header_json = json.dumps(freq_table_str_keys).encode("utf-8")

    out = bytearray()
    out += MAGIC_HEADER
    out += struct.pack(">I", len(data))          # original size
    out += struct.pack(">H", padding_bits)        # padding bits in last byte
    out += struct.pack(">I", len(header_json))    # length of header JSON
    out += header_json
    out += packed_payload

    compressed_size = len(out)
    original_size = len(data)
    ratio = compressed_size / original_size if original_size else 1.0

    stats = {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "compression_ratio": round(ratio, 4),
        "space_saved_percent": round((1 - ratio) * 100, 2),
        "frequency_table": freq_table,
        "code_table": code_table,
    }
    return bytes(out), stats


def compress_file(input_path: str, output_path: str) -> Dict:
    """Read a file from disk, compress it, and write the .huf container. Returns stats."""
    with open(input_path, "rb") as f:
        data = f.read()
    compressed, stats = compress_bytes(data)
    with open(output_path, "wb") as f:
        f.write(compressed)
    return stats


# ---------------------------------------------------------------------- #
# Step 7: Decompression
# ---------------------------------------------------------------------- #
class CorruptHuffmanFileError(Exception):
    """Raised when a .huf file is missing the expected magic header or is truncated."""
    pass


def decompress_bytes(compressed: bytes) -> bytes:
    """
    Reverse compress_bytes(): parse the custom container format, rebuild
    the Huffman tree from the stored frequency table, then walk the tree
    bit-by-bit to recover the original bytes.
    """
    if len(compressed) < 10 or compressed[:4] != MAGIC_HEADER:
        raise CorruptHuffmanFileError("File is not a valid Huffman-compressed (.huf) file.")

    offset = 4
    original_size, = struct.unpack(">I", compressed[offset:offset + 4])
    offset += 4
    padding_bits, = struct.unpack(">H", compressed[offset:offset + 2])
    offset += 2
    header_len, = struct.unpack(">I", compressed[offset:offset + 4])
    offset += 4

    if original_size == 0:
        return b""

    header_json = compressed[offset:offset + header_len]
    offset += header_len
    freq_table_str_keys = json.loads(header_json.decode("utf-8"))
    freq_table = {int(k): v for k, v in freq_table_str_keys.items()}

    tree_root = build_huffman_tree(freq_table)

    payload = compressed[offset:]
    # Convert payload bytes back into a bitstring, then strip the padding
    # bits that were appended to round out the final byte during compression.
    bitstring = "".join(f"{byte:08b}" for byte in payload)
    if padding_bits:
        bitstring = bitstring[:-padding_bits]

    decoded = bytearray()
    node = tree_root
    if node is not None and node.is_leaf():
        # Whole file was a single repeated byte; each '0' bit = one symbol.
        decoded.extend([node.byte_value] * original_size)
        return bytes(decoded)

    for bit in bitstring:
        node = node.left if bit == "0" else node.right
        if node.is_leaf():
            decoded.append(node.byte_value)
            node = tree_root
            if len(decoded) == original_size:
                break

    return bytes(decoded)


def decompress_file(input_path: str, output_path: str) -> int:
    """Read a .huf file from disk, decompress it, write the result. Returns byte count written."""
    with open(input_path, "rb") as f:
        compressed = f.read()
    data = decompress_bytes(compressed)
    with open(output_path, "wb") as f:
        f.write(data)
    return len(data)
