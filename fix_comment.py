import subprocess, os
filepath = "conftest.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('//', '#')
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("[+] Fixed C++ comment syntax to Python.")
subprocess.run(["pytest", "tests/", "-v", "--tb=no", "-q"], shell=True)