import io

path = 'D:\\eco_nojin\\services\\api_gateway\\routers\\auth.py'
with io.open(path, 'r', encoding='utf-8') as f:
    content = f.read()
print('ends with newline:', content.endswith(chr(10)))
print('last 60:', repr(content[-60:]))