##BP

from unicodedata import normalize

# copied from Quokka
def slugify(text, encoding=None,
            permitted_chars='abcdefghijklmnopqrstuvwxyz0123456789-'):
    if isinstance(text, str):
        text = text.decode(encoding or 'ascii')
    text = text.strip().replace(' ', '-').lower()
    text = normalize('NFKD', text).encode('ascii', 'ignore')
    text = ''.join(x if x in permitted_chars else '' for x in text)
    while '--' in text:
        text = text.replace('--', '-')
    return text

