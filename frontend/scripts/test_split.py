import re
from pathlib import Path

content = Path('src/content/site.ts').read_text(encoding='utf-8')

# Find fa object
fa_match = re.search(r'\nconst fa: SiteContent = \{(.*?)\n\};\s*\nconst en:', content, re.DOTALL)
if fa_match:
    print("Found fa object")
    fa_text = fa_match.group(1)
    print("First 200 chars of fa_text:")
    print(repr(fa_text[:200]))
else:
    print("Could not find fa object with regex")

# Try brace counting method
fa_start_match = re.search(r'\nconst fa: SiteContent = \{', content)
if fa_start_match:
    fa_start = fa_start_match.end()
    brace_count = 0
    in_string = False
    string_char = None
    fa_end = fa_start
    
    for i in range(fa_start, len(content)):
        char = content[i]
        if in_string:
            if char == '\\':
                continue
            if char == string_char:
                in_string = False
        else:
            if char in ('"', "'", '`'):
                in_string = True
                string_char = char
            elif char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    fa_end = i + 1
                    break
    
    fa_text = content[fa_start:fa_end]
    print("\nFound fa object with brace counting")
    print("First 200 chars of fa_text:")
    print(repr(fa_text[:200]))
    print("\nLooking for 'meta' in fa_text:")
    match = re.search(r'(?:^|\n)\s*meta\s*:\s*', fa_text)
    print("Match:", match)
    if match:
        print("After match:", repr(fa_text[match.end():match.end()+50]))
else:
    print("Could not find 'const fa: SiteContent = {'")
