"""Conservative cleanup of copied Chatwork display metadata; never mutate sources."""
import re
import unicodedata


def _normalize_label(value):
    normalized = ' '.join(unicodedata.normalize('NFKC', value or '').split()).casefold()
    return re.sub(r'\s+\)', ')', re.sub(r'\(\s+', '(', normalized))


def clean_message_body(body, sender_name=''):
    name = _normalize_label(sender_name)
    lines = (body or '').replace('\r\n', '\n').replace('\r', '\n').split('\n')
    result = []
    sender_kept = False
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        normalized = _normalize_label(line)
        # Only an exact sender label, or the copied bilingual sender/company label.
        label = normalized
        company = 'b productions company limited'
        if label.endswith(company):
            label = label[:-len(company)].strip()
        is_sender = bool(name) and (label == name or (
            label.endswith('(' + name + ')') and len(label) < len(name) + 80))
        if is_sender:
            if not sender_kept:
                display = re.sub(r'\s*B\s+PRODUCTIONS\s+COMPANY\s+LIMITED\s*$', '', line, flags=re.IGNORECASE).strip()
                result.append(display)
                sender_kept = True
            index += 1
            continue
        # Remove known copied reaction/count pairs, never bare numeric lines.
        if normalized in {'roger', 'bow'} and index + 1 < len(lines) and re.fullmatch(r'\d+', lines[index + 1].strip()):
            index += 2
            continue
        result.append(lines[index])
        index += 1
    return '\n'.join(result).strip()


def deduplicate_copied_sender_header(body, sender_name=''):
    """Remove *only* repeated copied Chatwork author headings at message start.

    This is for human-readable Excel cells.  The exact source in the database
    remains unchanged.  Unrelated message text/spacing/line endings stay intact.
    """
    if not isinstance(body, str) or not sender_name:
        return body
    lines = body.splitlines(keepends=True)
    if len(lines) < 2:
        return body
    name = _normalize_label(sender_name)

    def author_heading(line):
        label = _normalize_label(line.strip())
        company = 'b productions company limited'
        if label.endswith(company):
            label = label[:-len(company)].strip()
        return bool(label and (label == name or (
            label.endswith('(' + name + ')') and len(label) < len(name) + 80)))

    if not author_heading(lines[0]):
        return body
    index = 1
    while index < len(lines) and author_heading(lines[index]):
        index += 1
    return lines[0] + ''.join(lines[index:]) if index > 1 else body
