"""
Scrape any article URL and save as a .txt knowledge file.
Usage: python utils/scrape_article.py <URL> <output_filename>

Example:
  python utils/scrape_article.py https://www.gq.com/story/best-haircuts oval_face_guide.txt
"""

import sys
import re
import urllib.request
from html.parser import HTMLParser


class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self._skip_tags = {"script", "style", "nav", "footer", "header", "aside", "form"}
        self._current_skip = 0
        self._block_tags = {"p", "h1", "h2", "h3", "h4", "li", "blockquote"}
        self._in_block = False

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._current_skip += 1
        if tag in self._block_tags:
            self._in_block = True

    def handle_endtag(self, tag):
        if tag in self._skip_tags:
            self._current_skip = max(0, self._current_skip - 1)
        if tag in self._block_tags:
            self._in_block = False
            self.text_parts.append("\n")

    def handle_data(self, data):
        if self._current_skip == 0 and self._in_block:
            cleaned = data.strip()
            if cleaned:
                self.text_parts.append(cleaned)

    def get_text(self):
        raw = " ".join(self.text_parts)
        raw = re.sub(r"\s{2,}", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def scrape(url: str, output_filename: str):
    print(f"Fetching: {url}")

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )

    with urllib.request.urlopen(req, timeout=15) as response:
        html = response.read().decode("utf-8", errors="ignore")

    parser = ArticleParser()
    parser.feed(html)
    text = parser.get_text()

    if len(text) < 200:
        print("WARNING: Very little text extracted. The site may block scrapers.")
        print("Try Method 1 (manual copy-paste) for this site.")
        return

    output_path = f"knowledge_base/docs/{output_filename}"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"Source: {url}\n\n")
        f.write(text)

    print(f"Saved {len(text)} characters to {output_path}")
    print(f"Preview:\n{text[:300]}...")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python utils/scrape_article.py <URL> <output_filename.txt>")
        sys.exit(1)
    scrape(sys.argv[1], sys.argv[2])
