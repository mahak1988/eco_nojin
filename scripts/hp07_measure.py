"""Measure HP-07 booklet: total lines, per-chapter sizes, dead-ends, asset counts."""
import re
import sys

PATH = r"D:\eco_nojin\کتابها\HP-07 مالچ زیستی.txt"
FLOORS = {1: 320, 2: 350, 3: 400, 4: 200, 5: 250, 6: 280, 7: 170,
          8: 200, 9: 350, 10: 450, 11: 280, 12: 250}

with open(PATH, encoding="utf-8") as fh:
    lines = fh.read().split("\n")
if lines and lines[-1] == "":
    lines.pop()

marks = []
for i, ln in enumerate(lines):
    m = re.match(r"^فصل\s+(\d+)\s+—\s", ln)
    if m:
        marks.append((int(m.group(1)), i))
ap = next((i for i, ln in enumerate(lines) if ln.startswith("پیوست الف —")), None)
farm = next((i for i, ln in enumerate(lines)
             if ln.startswith("راهنمای اجرایی کشاورز —")), None)

print(f"TOTAL_LINES\t{len(lines)}")
print("CHAPTER\tLINES\tFLOOR\tSTATUS")
for n, (num, start) in enumerate(marks):
    end = marks[n + 1][1] if n + 1 < len(marks) else (ap or len(lines))
    size = end - start
    floor = FLOORS.get(num, 0)
    print(f"{num}\t{size}\t{floor}\t{'OK' if size >= floor else 'SHORT by %d' % (floor - size)}")
if ap is not None:
    head = ap if farm is None else farm
    print(f"A\t{head - ap}\t200\t{'OK' if head - ap >= 200 else 'SHORT'}")
    if farm is not None:
        print(f"FARMER\t{len(lines) - farm}\t300\t"
              f"{'OK' if len(lines) - farm >= 300 else 'SHORT'}")

text = "\n".join(lines)
for token in ("فاقد شناسه", "تأییدنشده", "نیازمند خط پایه",
              "پیشنهاد شناسه جدید"):
    print(f"DEADEND[{token}]\t{text.count(token)}")
print(f"DEADEND[TOTAL]\t{text.count('فاقد شناسه') + text.count('تأییدنشده') + text.count('نیازمند خط پایه') + text.count('پیشنهاد شناسه جدید')}")
print(f"FIGURES\t{len(re.findall(r'^شکل ', text, re.M))}")
print(f"TABLES\t{len(re.findall(r'^جدول ', text, re.M))}")
print(f"MODELS\t{len(re.findall(r'مدل (یکم|دوم|سوم|چهارم|پنجم|ششم|هفتم|هشتم|نهم|دهم|یازدهم|دوازدهم) —', text))}")
print(f"RISK\t{len(set(re.findall(r'RR-07-\d+', text)))}")
print(f"PROTOCOLS\t{len(re.findall(r'پروتکل اندازه‌گیری', text))}")
print(f"DECISIONS\t{len(set(re.findall(r'تصمیم (\d+) داوری', text)))}")
