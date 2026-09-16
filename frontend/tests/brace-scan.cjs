const fs = require("fs");
const src = fs.readFileSync(process.argv[2], "utf8");
let line = 1, i = 0, mode = "code", stack = [];
const pairs = { "{": "}", "(": ")", "[": "]" };
const SQ = String.fromCharCode(39), DQ = String.fromCharCode(34), BS = String.fromCharCode(92);
while (i < src.length) {
  const ch = src[i], prev = src[i - 1];
  if (mode === "code") {
    if (ch === "/" && src[i + 1] === "/") { mode = "line"; i++; continue; }
    if (ch === "/" && src[i + 1] === "*") { mode = "block"; i++; continue; }
    if (ch === SQ || ch === DQ || ch === "`") { mode = "str:" + ch; i++; continue; }
    if (ch === "{" || ch === "(" || ch === "[") { stack.push({ c: ch, l: line }); i++; continue; }
    if (ch === "}" || ch === ")" || ch === "]") {
      const o = stack.pop();
      if (!o || pairs[o.c] !== ch) { console.log("MISMATCH line", line, "got", JSON.stringify(ch), "expected close of", o && o.c, "from line", o && o.l); process.exit(0); }
      i++; continue;
    }
    i++; continue;
  }
  if (mode === "line") { if (ch === "\n") { mode = "code"; line++; } i++; continue; }
  if (mode === "block") { if (ch === "/" && prev === "*") mode = "code"; if (ch === "\n") line++; i++; continue; }
  const q = mode.slice(4);
  if (ch === q && prev !== BS) { mode = "code"; i++; continue; }
  if (ch === "\n" && q !== "`") { mode = "code"; line++; i++; continue; }
  if (ch === "\n") line++;
  i++;
}
console.log("END. unclosed:", JSON.stringify(stack));