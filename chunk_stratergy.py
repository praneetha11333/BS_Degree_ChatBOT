
def chunk_source_by_section(file_path):
    chunks = []
    current_section = ""
    current_types = set()
    current_lines = []
    current_tables = []
    current_headers = []
    current_rows = []
    pending_type = None

    def flush_table():
        nonlocal current_headers, current_rows
        if current_headers or current_rows:
            current_tables.append({"headers": current_headers[:], "rows": current_rows[:]})
            current_headers = []
            current_rows = []

    def flush_chunk():
        if not current_section:
            return
        flush_table()
        chunk = {
            "section": current_section,
            "types": list(current_types),
        }
        if current_lines:
            chunk["content"] = " ".join(current_lines)
        if current_tables:
            chunk["tables"] = current_tables
        if "content" in chunk or "tables" in chunk:
            if chunk.get("content") == current_section:
                return
            chunks.append(chunk)

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("===") or line.startswith("SOURCE:"):
                continue
            elif line.startswith("[TYPE:"):
                pending_type = line[6:-1].strip()
            elif line.startswith("[SECTION:"):
                new_section = line[9:-1].strip()
                if new_section != current_section:
                    flush_chunk()
                    current_section = new_section
                    current_types = set()
                    current_lines = []
                    current_tables = []
                    current_headers = []
                    current_rows = []
                if pending_type:
                    current_types.add(pending_type)
                    pending_type = None
            elif line.startswith("[HEADERS:"):
                flush_table()
                current_headers = [h.strip() for h in line[9:-1].split(",")]
            elif line.startswith("[ROW:"):
                current_rows.append([v.strip() for v in line[5:-1].split(",")])
            else:
                if pending_type:
                    current_types.add(pending_type)
                    pending_type = None
                current_lines.append(line)

    flush_chunk()
    return chunks


import tiktoken

def check_token_sizes(chunks, model="text-embedding-3-small"):
    enc = tiktoken.encoding_for_model(model)
    total_chunks = len(chunks)
    large_chunks = []

    for i, chunk in enumerate(chunks):
        # build text to encode: use content if present, else serialize table
        parts = []
        if "content" in chunk:
            parts.append(chunk["content"])
        for table in chunk.get("tables", []):
            rows_text = "\n".join(
                ", ".join(f"{h}: {v}" for h, v in zip(table["headers"], row))
                for row in table["rows"]
            )
            parts.append(f"Headers: {', '.join(table['headers'])}\n{rows_text}")
        text = "\n\n".join(parts)

        token_count = len(enc.encode(text))
        chunk["tokens"] = token_count
        chunk["chunk_index"] = i

        if token_count > 512:
            large_chunks.append(chunk)

    small_chunks = [c for c in chunks if c["tokens"] <= 512]
    avg_small = sum(c["tokens"] for c in small_chunks) / len(small_chunks) if small_chunks else 0
    min_small = min(c["tokens"] for c in small_chunks) if small_chunks else 0
    max_small = max(c["tokens"] for c in small_chunks) if small_chunks else 0

    print(f"Total chunks: {total_chunks}")
    print(f"Chunks > 512 tokens: {len(large_chunks)}")
    print(f"Chunks <= 512 tokens: {len(small_chunks)} | avg: {avg_small:.1f} | min: {min_small} | max: {max_small}")

    tiny_chunks = [c for c in chunks if c["tokens"] < 100]
    print(f"\nChunks < 100 tokens: {len(tiny_chunks)}")
    for chunk in tiny_chunks:
        print(f"  Chunk {chunk['chunk_index']} | Tokens: {chunk['tokens']} | Section: {chunk['section']}")
        if 'content' in chunk:
            print(f"  Content: {chunk['content'][:200]}")
        elif 'headers' in chunk:
            print(f"  Headers: {chunk['headers']}")
    print("\nLarge chunks:\n")

    for chunk in large_chunks:
        print(
            f"Chunk {chunk['chunk_index']} | "
            f"Tokens: {chunk['tokens']} | "
            f"Section: {chunk['section']} | "
            f"Types: {chunk['types']}"
        )

    return chunks


if __name__ == "__main__":
    chunks = chunk_source_by_section('source1.txt')
    chunks = check_token_sizes(chunks)
    for i, chunk in enumerate(chunks, 1):
        print(f"\n--- Chunk {i} | {chunk['section']} | types: {chunk['types']} ---")
        if 'tables' in chunk:
            for t, table in enumerate(chunk['tables'], 1):
                print(f"  Table {t} Headers: {table['headers']}")
                for row in table['rows']:
                    print(f"    Row: {row}")
        if 'content' in chunk:
            print(chunk['content'])
