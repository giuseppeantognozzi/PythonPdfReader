#!/usr/bin/env python3
"""
PDF Interactive Reader
A menu-driven tool to explore and analyze PDF documents in multiple ways.
"""

import sys
import re
import os
from collections import Counter

# ── dependency check ──────────────────────────────────────────────────────────
# must identify exact location of the PDF file on your windows system, for me the right
# path is specified below for you will be something like
#     c:\PycharmProjects\PythonPdfReader\Mass_Deportations__2026_UK.pdf
# /Users/giuseppeantognozzi/PycharmProjects/PythonPdfReader/Mass_Deportations__2026_UK.pdf
try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber…")
    os.system(f"{sys.executable} -m pip install pdfplumber -q")
    import pdfplumber

try:
    from pypdf import PdfReader
except ImportError:
    print("Installing pypdf…")
    os.system(f"{sys.executable} -m pip install pypdf -q")
    from pypdf import PdfReader

# ── helpers ───────────────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║               📄  PDF INTERACTIVE READER                     ║
╠══════════════════════════════════════════════════════════════╣
║  1. Read a specific page                                     ║
║  2. Count occurrences of a word                              ║
║  3. Print a range of pages                                   ║
║  4. Search for a keyword (returns matching paragraphs)       ║
║  5. AI-powered document summary (via Claude API)             ║
║  6. Document information & statistics                        ║
║  7. Joe's opinion                                            ║
║  0. Exit                                                     ║
╚══════════════════════════════════════════════════════════════╝
"""

SEP = "─" * 66


def load_pdf(path: str):
    """Return (pdfplumber_pdf, pypdf_reader, total_pages)."""
    try:
        plumb = pdfplumber.open(path)
        reader = PdfReader(path)
        return plumb, reader, len(plumb.pages)
    except Exception as exc:
        print(f"\n❌  Could not open PDF: {exc}")
        sys.exit(1)


def extract_page_text(plumb, page_num: int) -> str:
    """Extract text from a 1-based page number."""
    return plumb.pages[page_num - 1].extract_text() or "(No extractable text on this page)"


def extract_all_text(plumb) -> str:
    """Extract text from the entire document."""
    parts = []
    for page in plumb.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n".join(parts)


def wrap(text: str, width: int = 80) -> str:
    """Simple word-wrap for display."""
    lines = []
    for raw_line in text.splitlines():
        if len(raw_line) <= width:
            lines.append(raw_line)
        else:
            words = raw_line.split()
            cur = ""
            for w in words:
                if len(cur) + len(w) + 1 <= width:
                    cur = f"{cur} {w}".lstrip()
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
    return "\n".join(lines)


def get_int(prompt: str, lo: int, hi: int) -> int | None:
    raw = input(prompt).strip()
    if not raw.isdigit():
        print("⚠  Please enter a valid number.")
        return None
    val = int(raw)
    if not (lo <= val <= hi):
        print(f"⚠  Number must be between {lo} and {hi}.")
        return None
    return val


# ── menu options ──────────────────────────────────────────────────────────────

def option_read_page(plumb, total: int):
    """Option 1 – Read a specific page."""
    print(f"\n{SEP}")
    print(f"  READ A SPECIFIC PAGE  (1 – {total})")
    print(SEP)
    pg = get_int(f"  Enter page number [1-{total}]: ", 1, total)
    if pg is None:
        return
    text = extract_page_text(plumb, pg)
    print(f"\n{'═'*66}")
    print(f"  PAGE {pg}")
    print('═'*66)
    print(wrap(text))
    print('═'*66)


def option_word_count(plumb):
    """Option 2 – Count occurrences of a specific word."""
    print(f"\n{SEP}")
    print("  WORD FREQUENCY COUNTER")
    print(SEP)
    word = input("  Enter the word to search for: ").strip()
    if not word:
        print("⚠  No word entered.")
        return

    pattern = re.compile(re.escape(word), re.IGNORECASE)
    total_hits = 0
    page_hits = {}

    for i, page in enumerate(plumb.pages, 1):
        t = page.extract_text() or ""
        hits = len(pattern.findall(t))
        if hits:
            page_hits[i] = hits
            total_hits += hits

    print(f"\n  Results for  '{word}'")
    print(SEP)
    if total_hits == 0:
        print("  The word was not found in this document.")
    else:
        print(f"  Total occurrences : {total_hits}")
        print(f"  Found on {len(page_hits)} page(s):")
        for pg, cnt in sorted(page_hits.items()):
            bar = "█" * min(cnt, 40)
            print(f"    Page {pg:>4}  {bar}  ({cnt})")
    print(SEP)


def option_page_range(plumb, total: int):
    """Option 3 – Print a range of pages."""
    print(f"\n{SEP}")
    print(f"  PAGE RANGE READER  (1 – {total})")
    print(SEP)
    start = get_int(f"  Start page [1-{total}]: ", 1, total)
    if start is None:
        return
    end = get_int(f"  End   page [{start}-{total}]: ", start, total)
    if end is None:
        return

    for pg in range(start, end + 1):
        text = extract_page_text(plumb, pg)
        print(f"\n{'═'*66}")
        print(f"  PAGE {pg}  of  {end}")
        print('═'*66)
        print(wrap(text))
    print('═'*66)
    print(f"\n  ✅  Printed pages {start} – {end}  ({end - start + 1} page(s))")


def option_keyword_search(plumb):
    """Option 4 – Search and return all paragraphs containing a keyword."""
    print(f"\n{SEP}")
    print("  KEYWORD PARAGRAPH SEARCH")
    print(SEP)
    keyword = input("  Enter keyword to search: ").strip()
    if not keyword:
        print("⚠  No keyword entered.")
        return

    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    results = []   # list of (page_num, paragraph)

    for i, page in enumerate(plumb.pages, 1):
        text = page.extract_text() or ""
        # Split into paragraphs (blank-line separated or sentence groups)
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
        for para in paragraphs:
            if pattern.search(para):
                results.append((i, para))

    print(f"\n  Keyword: '{keyword}'")
    print(SEP)
    if not results:
        print("  No paragraphs found containing that keyword.")
    else:
        print(f"  Found {len(results)} matching paragraph(s):\n")
        for idx, (pg, para) in enumerate(results, 1):
            # Highlight keyword in terminal using ANSI bold
            highlighted = pattern.sub(
                lambda m: f"\033[1;33m{m.group()}\033[0m", para
            )
            print(f"  ┌─ Match {idx}  (Page {pg})")
            print(f"  │")
            for line in wrap(highlighted, 74).splitlines():
                print(f"  │  {line}")
            print(f"  └{'─'*63}")
            print()
    print(SEP)


def option_ai_summary(plumb, pdf_path: str):
    """Option 5 – AI-powered summary using Claude API (via requests) or sumy fallback."""
    print(f"\n{SEP}")
    print("  AI-POWERED DOCUMENT SUMMARY")
    print(SEP)
    print("  Choose summary method:")
    print("    A. Claude API  (requires ANTHROPIC_API_KEY env var)")
    print("    B. Local NLP   (sumy – no API key needed)")
    choice = input("  Your choice [A/B]: ").strip().upper()

    full_text = extract_all_text(plumb)

    if choice == "A":
        _summary_claude(full_text)
    elif choice == "B":
        _summary_local(full_text)
    else:
        print("⚠  Invalid choice.")


def _summary_claude(full_text: str):
    """Call Anthropic Claude API for a structured summary."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("\n  ⚠  ANTHROPIC_API_KEY environment variable not set.")
        print("     Set it with:  export ANTHROPIC_API_KEY=sk-ant-…")
        print("     Falling back to local NLP summary.\n")
        _summary_local(full_text)
        return

    try:
        import urllib.request, urllib.error, json
    except ImportError:
        print("⚠  urllib not available.")
        return

    # Trim text to ~8000 words to stay within token limits
    words = full_text.split()
    trimmed = " ".join(words[:8000])
    if len(words) > 8000:
        trimmed += "\n\n[… document truncated for API call …]"

    prompt = (
        "You are an expert document analyst. Analyze the following document "
        "and provide:\n"
        "1. A concise executive summary (3–5 sentences)\n"
        "2. The 5 most important key points\n"
        "3. Main themes or topics discussed\n"
        "4. Any notable conclusions or recommendations\n\n"
        f"DOCUMENT TEXT:\n{trimmed}"
    )

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    print("\n  ⏳  Sending request to Claude API…")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        summary = data["content"][0]["text"]
        print(f"\n{'═'*66}")
        print("  🤖  CLAUDE AI SUMMARY")
        print('═'*66)
        print(wrap(summary, 78))
        print('═'*66)
    except urllib.error.HTTPError as e:
        print(f"\n  ❌  API error {e.code}: {e.read().decode()}")
    except Exception as exc:
        print(f"\n  ❌  Request failed: {exc}")


def _summary_local(full_text: str):
    """Use sumy (local) for extractive summarization."""
    try:
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.summarizers.lsa import LsaSummarizer
        from sumy.nlp.stemmers import Stemmer
        from sumy.utils import get_stop_words
    except ImportError:
        print("  Installing sumy for local NLP summarization…")
        os.system(f"{sys.executable} -m pip install sumy -q")
        try:
            from sumy.parsers.plaintext import PlaintextParser
            from sumy.nlp.tokenizers import Tokenizer
            from sumy.summarizers.lsa import LsaSummarizer
            from sumy.nlp.stemmers import Stemmer
            from sumy.utils import get_stop_words
        except Exception as exc:
            print(f"  ❌  Could not install sumy: {exc}")
            return

    print("\n  ⏳  Running local LSA summarization…")
    LANGUAGE = "english"
    SENTENCES = 10

    try:
        parser = PlaintextParser.from_string(full_text, Tokenizer(LANGUAGE))
        stemmer = Stemmer(LANGUAGE)
        summarizer = LsaSummarizer(stemmer)
        summarizer.stop_words = get_stop_words(LANGUAGE)
        summary_sentences = summarizer(parser.document, SENTENCES)

        print(f"\n{'═'*66}")
        print(f"  🧠  LOCAL NLP SUMMARY  (top {SENTENCES} extracted sentences)")
        print('═'*66)
        for i, sentence in enumerate(summary_sentences, 1):
            print(f"\n  {i}. {wrap(str(sentence), 74)}")
        print(f"\n{'═'*66}")
    except Exception as exc:
        print(f"  ❌  Summarization failed: {exc}")


def option_doc_info(plumb, pdf_path: str):
    """Option 6 – Show document info and statistics."""
    reader = PdfReader(pdf_path)
    total = len(plumb.pages)

    print(f"\n{SEP}")
    print("  DOCUMENT INFORMATION & STATISTICS")
    print(SEP)

    # Metadata
    meta = reader.metadata or {}
    print(f"  Title    : {meta.get('/Title', 'N/A')}")
    print(f"  Author   : {meta.get('/Author', 'N/A')}")
    print(f"  Producer : {meta.get('/Producer', 'N/A')}")
    print(f"  Pages    : {total}")
    size_kb = os.path.getsize(pdf_path) / 1024
    print(f"  File size: {size_kb:,.1f} KB  ({size_kb/1024:.2f} MB)")

    # Word & character counts
    print("\n  ⏳  Counting words and characters…")
    all_text = extract_all_text(plumb)
    words = re.findall(r"\b\w+\b", all_text)
    chars = len(all_text)
    sentences = len(re.findall(r"[.!?]+", all_text))

    print(f"\n  Word count      : {len(words):,}")
    print(f"  Character count : {chars:,}")
    print(f"  Sentence count  : {sentences:,}")
    avg_wpp = len(words) // total if total else 0
    print(f"  Avg words/page  : {avg_wpp:,}")

    # Top 15 words
    stop = {
        "the","a","an","and","or","of","to","in","is","it","that","this",
        "was","for","on","are","as","with","be","by","at","from","have",
        "has","he","she","they","we","you","i","not","but","so","if","its",
        "which","who","their","been","had","were","will","would","can",
        "may","also","more","about","than","into","when","do","said","all",
    }
    freq = Counter(w.lower() for w in words if w.lower() not in stop and len(w) > 2)
    top15 = freq.most_common(15)

    print(f"\n  Top 15 most frequent words (excluding stop-words):")
    print(f"  {'Word':<20} {'Count':>6}  Bar")
    print(f"  {'─'*20} {'─'*6}  {'─'*30}")
    max_cnt = top15[0][1] if top15 else 1
    for word, cnt in top15:
        bar = "█" * int(cnt / max_cnt * 30)
        print(f"  {word:<20} {cnt:>6}  {bar}")
    print(SEP)


# ── main loop ─────────────────────────────────────────────────────────────────

def main():
    # Accept PDF path as argument or ask interactively
    if len(sys.argv) >= 2:
        pdf_path = sys.argv[1]
    else:
        #  /Users/giuseppeantognozzi/PycharmProjects/PythonPdfReader/Mass_Deportations__2026_UK.pdf
        pdf_path = input("  Enter path to PDF file: ").strip().strip('"').strip("'")

    if not os.path.isfile(pdf_path):
        print(f"❌  File not found: {pdf_path}")
        sys.exit(1)

    plumb, reader, total = load_pdf(pdf_path)
    print(f"\n  ✅  Loaded: {os.path.basename(pdf_path)}  ({total} pages)")

    while True:
        print(BANNER)
        choice = input("  Enter your choice [0-6]: ").strip()

        if choice == "0":
            print("\n  👋  Goodbye!\n")
            plumb.close()
            break
        elif choice == "1":
            option_read_page(plumb, total)
        elif choice == "2":
            option_word_count(plumb)
        elif choice == "3":
            option_page_range(plumb, total)
        elif choice == "4":
            option_keyword_search(plumb)
        elif choice == "5":
            option_ai_summary(plumb, pdf_path)
        elif choice == "6":
            option_doc_info(plumb, pdf_path)
        elif choice == "7":
            print('Cool program !')
        else:
            print("\n  ⚠  Invalid choice. Please enter a number from 0 to 6.")

        input("\n  Press Enter to return to the main menu…")


if __name__ == "__main__":
    main()
