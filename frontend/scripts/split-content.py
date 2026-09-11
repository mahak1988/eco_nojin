#!/usr/bin/env python3
"""Split content/site.ts into per-section files."""
from __future__ import annotations

import re
from pathlib import Path

FRONTEND_ROOT = Path(__file__).resolve().parents[1]
SITE_FILE = FRONTEND_ROOT / "src" / "content" / "site.ts"
SECTIONS_DIR = FRONTEND_ROOT / "src" / "content" / "sections"
TYPES_FILE = SECTIONS_DIR / "types.ts"


def extract_object(text: str, start_marker: str) -> tuple[str, int]:
    """Extract an object starting with `start_marker` using brace counting.
    Returns (object_text, end_position).
    """
    start_match = re.search(start_marker, text)
    if not start_match:
        raise SystemExit(f"Could not find '{start_marker}'")
    
    start = start_match.end()
    brace_count = 1
    in_string = False
    string_char = None
    
    for i in range(start, len(text)):
        char = text[i]
        
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
                    return text[start:i], i + 1
    
    raise SystemExit(f"Could not extract object starting with '{start_marker}'")


def extract_key_value(text: str, key: str) -> str | None:
    """Extract the value for a top-level key from a SiteContent object text."""
    # Use brace-aware scanning to find only top-level keys
    brace_count = 0
    in_string = False
    string_char = None
    i = 0
    
    while i < len(text):
        char = text[i]
        
        if in_string:
            if char == '\\':
                i += 1
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
            elif brace_count == 0 and char == '\n':
                # Check if this line starts with the key
                line_start = i + 1
                # Skip leading whitespace
                j = line_start
                while j < len(text) and text[j] == ' ':
                    j += 1
                # Check if the line starts with the key followed by ':'
                if text[j:j+len(key)+1] == f"{key}:":
                    # Found the key at top level
                    value_start = j + len(key) + 1
                    # Skip whitespace after ':'
                    while value_start < len(text) and text[value_start] == ' ':
                        value_start += 1
                    # Now extract the value
                    start = value_start
                    brace_count_val = 0
                    bracket_count = 0
                    k = start - 1
                    in_string_val = False
                    string_char_val = None
                    
                    while k < len(text) - 1:
                        k += 1
                        c = text[k]
                        
                        if in_string_val:
                            if c == '\\':
                                k += 1
                                continue
                            if c == string_char_val:
                                in_string_val = False
                        else:
                            if c in ('"', "'", '`'):
                                in_string_val = True
                                string_char_val = c
                            elif c == '{':
                                brace_count_val += 1
                            elif c == '}':
                                brace_count_val -= 1
                                if brace_count_val == 0 and bracket_count == 0:
                                    return text[start:k+1]
                            elif c == '[':
                                bracket_count += 1
                            elif c == ']':
                                bracket_count -= 1
                                if bracket_count == 0 and brace_count_val == 0:
                                    return text[start:k+1]
                            elif c == ',' and brace_count_val == 0 and bracket_count == 0:
                                return text[start:k]
                    
                    return text[start:]
        
        i += 1
    
    return None


def main() -> None:
    content = SITE_FILE.read_text(encoding="utf-8")
    
    # Extract fa object
    fa_text, fa_end = extract_object(content, r"\nconst fa: SiteContent = \{")
    
    # Extract en object (search after fa)
    en_text, _ = extract_object(content[fa_end:], r"\nconst en: SiteContent = \{")
    
    # Read types from types.ts
    types_section = TYPES_FILE.read_text(encoding="utf-8")
    
    # Extract only top-level keys from SiteContent interface
    # Find the SiteContent interface block
    site_content_match = re.search(r"export interface SiteContent \{(.*?)\n\}", types_section, re.DOTALL)
    if not site_content_match:
        raise SystemExit("Could not find SiteContent interface in types.ts")
    
    site_content_body = site_content_match.group(1)
    
    # Extract top-level keys (indented with 2 spaces, not inside nested braces)
    keys = re.findall(r"^\s{2}(\w+):\s*\{", site_content_body, re.MULTILINE)
    simple_keys = re.findall(r"^\s{2}(\w+):\s*(?:string|number|boolean|IconKey|TimelineItem\[\]|BlogPost\[\]|FaqItem\[\]|LegalPageContent);", site_content_body, re.MULTILINE)
    all_keys = sorted(set(keys + simple_keys))
    
    print(f"Found {len(all_keys)} sections: {', '.join(all_keys)}")
    
    SECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    barrel = "// Auto-generated barrel export for content sections\n"
    barrel += "// Do not edit manually — run scripts/split-content.py instead\n\n"
    barrel += "export type {\n  SiteContent,\n  Lang,\n  IconKey,\n  LegalSection,\n  LegalPageContent,\n  BlogPost,\n  FaqItem,\n  TimelineItem,\n} from './types';\n\n"
    
    for key in all_keys:
        fa_val = extract_key_value(fa_text, key)
        en_val = extract_key_value(en_text, key)
        
        if fa_val is None or en_val is None:
            section_file = SECTIONS_DIR / f"{key}.ts"
            if section_file.exists():
                print(f"  Preserved manual section: sections/{key}.ts")
                barrel += f"export {{ {key} }} from './{key}';\n"
                continue
            print(f"  Warning: could not extract {key}")
            continue
        
        section_content = f"""import type {{ SiteContent }} from './types';

export interface {key.capitalize()}Content {{
  fa: SiteContent['{key}'];
  en: SiteContent['{key}'];
}}

export const {key} = {{
  fa: {fa_val.strip()},
  en: {en_val.strip()},
}} as const;

export type {key.capitalize()}Lang = 'fa' | 'en';
"""
        
        (SECTIONS_DIR / f"{key}.ts").write_text(section_content, encoding="utf-8")
        barrel += f"export {{ {key} }} from './{key}';\n"
        print(f"  Created sections/{key}.ts")
    
    # Write barrel
    (SECTIONS_DIR / "index.ts").write_text(barrel, encoding="utf-8")
    print("Created sections/index.ts")
    
    # Generate site.ts barrel that reconstructs fa, en, and content
    imports = "\n".join([f"import {{ {key} }} from './sections/{key}';" for key in all_keys])
    fa_construct = "const fa = {\n"
    en_construct = "const en = {\n"
    for key in all_keys:
        fa_construct += f"  {key}: {key}.fa,\n"
        en_construct += f"  {key}: {key}.en,\n"
    fa_construct += "} as const as unknown as SiteContent;\n"
    en_construct += "} as const as unknown as SiteContent;\n"
    
    new_site = f"""// Auto-generated barrel export — run scripts/split-content.py to regenerate
import type {{ SiteContent, Lang, IconKey, LegalSection, LegalPageContent, BlogPost, FaqItem, TimelineItem }} from './sections/types';
export type {{ SiteContent, Lang, IconKey, LegalSection, LegalPageContent, BlogPost, FaqItem, TimelineItem }};

{imports}

{fa_construct}
{en_construct}

export const content: Record<Lang, SiteContent> = {{ fa, en }};
"""
    SITE_FILE.write_text(new_site, encoding="utf-8")
    print("Updated content/site.ts as barrel export with reconstructed fa/en/content")
    print("\nDone!")


if __name__ == "__main__":
    main()
