import tiktoken
from chunk_stratergy import chunk_source_by_section

TOKEN_LIMIT = 1000
ROWS_PER_SPLIT = 12

enc = tiktoken.encoding_for_model("text-embedding-3-small")


def count_tokens(chunk):
    parts = []
    if "content" in chunk:
        parts.append(chunk["content"])
    for table in chunk.get("tables", []):
        rows_text = "\n".join(
            ", ".join(f"{h}: {v}" for h, v in zip(table["headers"], row))
            for row in table["rows"]
        )
        parts.append(f"Headers: {', '.join(table['headers'])}\n{rows_text}")
    return len(enc.encode("\n\n".join(parts)))


def split_table(base_chunk, table, table_index):
    headers = table["headers"]
    rows = table["rows"]
    sub_chunks = []
    for i in range(0, len(rows), ROWS_PER_SPLIT):
        sub = {
            "section": base_chunk["section"],
            "types": base_chunk["types"],
            "tables": [{"headers": headers, "rows": rows[i:i + ROWS_PER_SPLIT]}],
            "split_from_table": table_index,
            "split_part": i // ROWS_PER_SPLIT,
        }
        if "content" in base_chunk:
            sub["content"] = base_chunk["content"]
        sub_chunks.append(sub)
    return sub_chunks


def split_large_chunks(chunks):
    result = []
    for chunk in chunks:
        tokens = count_tokens(chunk)
        if tokens <= TOKEN_LIMIT or "table" not in chunk.get("types", []):
            chunk["tokens"] = tokens
            result.append(chunk)
            continue

        # split each table in the chunk by rows
        if len(chunk.get("tables", [])) == 0:
            chunk["tokens"] = tokens
            result.append(chunk)
            continue

        for t_idx, table in enumerate(chunk["tables"]):
            for sub in split_table(chunk, table, t_idx):
                sub["tokens"] = count_tokens(sub)
                result.append(sub)

    return result


if __name__ == "__main__":
    chunks = chunk_source_by_section("source1.txt")
    chunks = split_large_chunks(chunks)
    for i, chunk in enumerate(chunks, 1):
        print(f"\n--- Chunk {i} | {chunk['section']} | types: {chunk['types']} ---")
        if 'tables' in chunk:
            for t, table in enumerate(chunk['tables'], 1):
                print(f"  Table {t} Headers: {table['headers']}")
                for row in table['rows']:
                    print(f"    Row: {row}")
        if 'content' in chunk:
            print(chunk['content'])
    