import re

with open('public/b2b_validation_suite.html', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = re.compile(r'#(?:2563EB|1D4ED8|3B82F6|DBEAFE|EFF6FF|BFDBFE|93C5FD|60A5FA|1E40AF|1E3A8A|38BDF8|0284C7)', re.IGNORECASE)
blues = pattern.findall(text)
print('Remaining blue hexes:', len(blues))
print('Any termelt in text?', 'termelt' in text.lower())
for img in re.finditer(r'<img[^>]+>', text):
    m = re.search(r'src="([^"]+)"', img.group(0))
    if m:
        print('Image src starts with:', m.group(1)[:35], 'length:', len(m.group(1)))
