documents=[
    {
        "url": "https://docs.google.com/document/d/e/2PACX-1vRxGnnDCVAO3KX2CGtMIcJQuDrAasVk2JHbDxkjsGrTP5ShhZK8N6ZSPX89lexKx86QPAUswSzGLsOA/pub?urp=gmail_link",
        "source" : "Student Handbook"
    },
    {
        "url":"https://docs.google.com/document/u/0/d/e/2PACX-1vT_FeqnTq0Br4sUaN7OYAmj1B9MwjchyTEed1Bh5FkZvi5NyIMeAvvkuttostVsJBPjZcs3SjjEfiho/pub?urp=gmail_link&pli=1#h.2zbgiuw",
        "source" : "Grading_Document"
    }
]

from bs4 import BeautifulSoup
import requests
import os

def fetch_document(url):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove Google Docs webpage boilerplate
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    # Actual document content
    content = soup.find(id="contents")

    if content is None:
        raise ValueError("Could not find document content")

    return content
def extract_table(table):
    """Extract a table as rows."""

    rows = []

    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"], recursive=False)

        row = [
            cell.get_text(" ", strip=True)
            for cell in cells
        ]

        if row:
            rows.append(row)

    return rows


def table_to_text(rows):
    """Convert table rows into semantic text."""

    if not rows:
        return ""

    headers = rows[0]
    output = []

    for row in rows[1:]:

        row_data = []

        for header, value in zip(headers, row):

            if value:
                row_data.append(f"{header}: {value}")

        if row_data:
            output.append("\n".join(row_data))

    return "\n\n".join(output)


def extract_document(content, source_name):
    """Extract headings, paragraphs, lists and tables in document order."""

    chunks = []

    current_section = "General"

    # Process elements in document order
    for element in content.find_all(
        ["h1", "h2", "h3", "p", "ol", "ul", "table"]
    ):
        if element.name in ["p", "ol", "ul"] and element.find_parent("table"):
            continue
        # -------------------------
        # HEADINGS
        # -------------------------
        if element.name in ["h1", "h2", "h3"]:

            text = element.get_text(" ", strip=True)

            if text:
                current_section = text

                chunks.append({
                    "text": text,
                    "type": "heading",
                    "section": current_section,
                    "source": source_name
                })

        # -------------------------
        # PARAGRAPH
        # -------------------------
        elif element.name == "p":

            text = element.get_text(" ", strip=True)

            if text:
                chunks.append({
                    "text": text,
                    "type": "paragraph",
                    "section": current_section,
                    "source": source_name
                })

        # -------------------------
        # ORDERED LIST
        # -------------------------
        elif element.name == "ol":

            items = element.find_all("li", recursive=False)

            list_text = []

            for i, li in enumerate(items, start=1):

                text = li.get_text(" ", strip=True)

                if text:
                    list_text.append(f"{i}. {text}")

            if list_text:

                chunks.append({
                    "text": "\n".join(list_text),
                    "type": "ordered_list",
                    "section": current_section,
                    "source": source_name
                })

        # -------------------------
        # UNORDERED LIST
        # -------------------------
        elif element.name == "ul":

            items = element.find_all("li", recursive=False)

            list_text = []

            for li in items:

                text = li.get_text(" ", strip=True)

                if text:
                    list_text.append(f"- {text}")

            if list_text:

                chunks.append({
                    "text": "\n".join(list_text),
                    "type": "unordered_list",
                    "section": current_section,
                    "source": source_name
                })

        # -------------------------
        # TABLE
        # -------------------------
        elif element.name == "table":

            rows = extract_table(element)

            text = table_to_text(rows)

            if text:

                chunks.append({
                    "text": text,
                    "type": "table",
                    "section": current_section,
                    "headers": rows[0] if rows else [],
                    "rows": rows[1:] if len(rows) > 1 else [],
                    "source": source_name
                })

    return chunks


all_documents = []

for document in documents:

    print(
        f"Fetching: {document['source']}"
    )

    content = fetch_document(
        document["url"]
    )

    chunks = extract_document(content, document["source"])

    all_documents.append({
        "source": document["source"],
        "chunks": chunks
    })

    print(
        f"Extracted {len(chunks)} elements"
    )


# -----------------------------------------
# 7. Create source.txt
# -----------------------------------------

with open(
    "source1.txt",
    "w",
    encoding="utf-8"
) as f:

    for document in all_documents:

        f.write("\n")
        f.write("=" * 80)
        f.write("\n")

        f.write(
            f"SOURCE: {document['source']}\n"
        )

        f.write("=" * 80)
        f.write("\n\n")

        for chunk in document["chunks"]:

            f.write(
                f"[TYPE: {chunk['type']}]\n"
            )

            f.write(
                f"[SECTION: {chunk['section']}]\n"
            )

            if "headers" in chunk and "rows" in chunk:
                f.write(
                    f"[HEADERS: {', '.join(chunk['headers'])}]\n"
                )

                for row in chunk["rows"]:
                    f.write(
                        f"[ROW: {', '.join(row)}]\n"
                    )
            else:
                f.write(
                    f"{chunk['text']}\n"
                )
            

            f.write("\n\n")