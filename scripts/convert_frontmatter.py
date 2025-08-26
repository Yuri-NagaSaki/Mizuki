#!/usr/bin/env python3
import re
from pathlib import Path


FRONT_MATTER_START = re.compile(r"^---\s*$")
FRONT_MATTER_END = re.compile(r"^---\s*$|^\.\.\.\s*$")

# Matches a top-level YAML key like: key: value
TOP_LEVEL_KEY = re.compile(r"^[A-Za-z_][\w\-]*\s*:\s*(.*)$")

def parse_flow_sequence(s: str):
    # Very light-weight parser for [a, b, "c d"]
    # Not a full YAML parser; handles common cases.
    items = []
    buf = ''
    in_quote = False
    quote_char = ''
    escape = False
    for ch in s.strip():
        if in_quote:
            if escape:
                buf += ch
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == quote_char:
                in_quote = False
            else:
                buf += ch
        else:
            if ch in ('"', "'"):
                in_quote = True
                quote_char = ch
            elif ch == ',':
                item = buf.strip()
                if item:
                    items.append(item)
                buf = ''
            elif ch in '[]':
                continue
            else:
                buf += ch
    last = buf.strip()
    if last:
        items.append(last)
    # Strip optional surrounding quotes on items
    return [i.strip().strip('"').strip("'") for i in items]


def to_flow_sequence(items):
    # Keep items simple; quote only if contains space or colon
    out = []
    seen = set()
    for it in items:
        if not it:
            continue
        if it.lower() == 'vps':
            continue
        key = it
        if key in seen:
            continue
        seen.add(key)
        if re.search(r"\s|:|,", it):
            out.append(f'"{it}"')
        else:
            out.append(it)
    return '[' + ', '.join(out) + ']'


def extract_categories(lines, start_idx):
    """
    Given lines and index of a line that starts with 'categories:',
    return (values, end_idx) where end_idx is the index after the categories block.
    Handles block style (dash list) and flow style.
    """
    line = lines[start_idx]
    m = re.match(r"^(\s*)categories\s*:\s*(.*)$", line)
    if not m:
        return [], start_idx + 1
    indent = len(m.group(1))
    rest = m.group(2).strip()
    values = []
    if rest.startswith('['):
        # flow sequence on same line (may span, but assume single-line common case)
        values = parse_flow_sequence(rest)
        return values, start_idx + 1
    # Collect following dash list items until next top-level key or outdent
    i = start_idx + 1
    while i < len(lines):
        s = lines[i]
        if not s.strip():
            # blank line ends the block
            break
        # If new top-level key at column 0, stop
        if indent == 0 and TOP_LEVEL_KEY.match(s) and not s.startswith(' '):
            break
        # If this line is a list item with greater indent, collect
        m2 = re.match(r"^\s*-\s*(.*)$", s)
        if m2:
            item = m2.group(1).strip().strip('"').strip("'")
            # Trim trailing comments like # something
            item = item.split(' #')[0].strip()
            if item:
                values.append(item)
            i += 1
            continue
        # Non-list or lower indent ends the block
        if len(s) - len(s.lstrip(' ')) <= indent:
            break
        i += 1
    return values, i


def extract_tags(lines, start_idx):
    line = lines[start_idx]
    m = re.match(r"^(\s*)tags\s*:\s*(.*)$", line)
    if not m:
        return [], start_idx + 1
    rest = m.group(2).strip()
    if rest.startswith('['):
        return parse_flow_sequence(rest), start_idx + 1
    # block style list
    values = []
    i = start_idx + 1
    while i < len(lines):
        s = lines[i]
        if not s.strip():
            break
        if TOP_LEVEL_KEY.match(s) and not s.startswith(' '):
            break
        m2 = re.match(r"^\s*-\s*(.*)$", s)
        if m2:
            item = m2.group(1).strip().strip('"').strip("'")
            item = item.split(' #')[0].strip()
            if item:
                values.append(item)
            i += 1
            continue
        i += 1
    return values, i


def process_file(path: Path) -> bool:
    data = path.read_text(encoding='utf-8', errors='ignore').splitlines()
    if not data:
        return False
    # Find front matter
    if not FRONT_MATTER_START.match(data[0]):
        return False
    # Find end
    end_idx = None
    for i in range(1, min(len(data), 500)):
        if FRONT_MATTER_END.match(data[i]):
            end_idx = i
            break
    if end_idx is None:
        return False
    head = data[1:end_idx]
    tail = data[end_idx+1:]

    # Scan header for lines and collect categories and existing tags
    i = 0
    changed = False
    new_head = []
    collected_categories = []
    existing_tags = []
    while i < len(head):
        line = head[i]
        # categories
        if re.match(r"^\s*categories\s*:\s*", line):
            cats, j = extract_categories(head, i)
            collected_categories.extend(cats)
            i = j
            changed = True
            continue
        # tags
        if re.match(r"^\s*tags\s*:\s*", line):
            tags, j = extract_tags(head, i)
            existing_tags.extend(tags)
            # Skip old tags; we will rewrite into flow sequence
            i = j
            changed = True
            continue
        new_head.append(line)
        i += 1

    # Merge tags: existing + categories, drop 'vps', dedupe preserving order
    merged = []
    seen = set()
    for item in existing_tags + collected_categories:
        if not item:
            continue
        if item.lower() == 'vps':
            continue
        if item not in seen:
            merged.append(item)
            seen.add(item)

    # If we had categories or tags to normalize, add unified tags line
    if collected_categories or existing_tags:
        tags_line = f"tags: {to_flow_sequence(merged)}"
        # Place tags at top of header for consistency
        new_head.insert(0, tags_line)
        changed = True

    if not changed:
        return False

    new_data = []
    new_data.append('---')
    new_data.extend(new_head)
    new_data.append('---')
    new_data.extend(tail)
    path.write_text("\n".join(new_data) + ("\n" if data and data[-1].endswith('\n') else ""), encoding='utf-8')
    return True


def main():
    root = Path('.')
    md_files = list(root.rglob('*.md'))
    changed_count = 0
    for p in md_files:
        # Skip common non-front-matter files quickly by peeking first char
        try:
            with p.open('r', encoding='utf-8', errors='ignore') as f:
                first = f.readline()
            if not FRONT_MATTER_START.match(first):
                continue
        except Exception:
            continue
        if process_file(p):
            changed_count += 1
            print(f"Updated: {p}")
    print(f"Total updated: {changed_count}")


if __name__ == '__main__':
    main()

