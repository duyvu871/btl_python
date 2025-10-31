import re
import unicodedata

CTRL = r"\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F\u200B\u200C\u200D\u2060"
CTRL_RE = re.compile(f"[{CTRL}]")
DASH_RE = re.compile(r"[\u2010-\u2015\u2212]")  # – — − …
HRULE_RE = re.compile(r"^\s*[-_*]{3,}\s*$", re.MULTILINE)  # --- ___ *** (hr)
BULLET_LINE_RE = re.compile(r"^\s*([-*•]\s+)+", re.MULTILINE)

def sanitize_one(s: str) -> str:
    s = "" if s is None else str(s)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = HRULE_RE.sub(" ", s)                 # bỏ dòng gạch dài
    s = BULLET_LINE_RE.sub("", s)            # bỏ bullet đầu dòng
    s = s.replace("\n", " ")          # newline -> space
    s = DASH_RE.sub("-", s)                  # unify dash
    s = CTRL_RE.sub(" ", s)                  # bỏ control chars
    s = re.sub(r"\s+", " ", s).strip()
    return s or " "

def sanitize_batch(xs): return [sanitize_one(x) for x in xs]
