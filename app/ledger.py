"""Turn a spoken shop transcript (English / Hindi / Hinglish) into khata (ledger) entries.

Deterministic, dependency-free parsing so it runs instantly on-device and every entry can
be traced back to the words that produced it.
"""
import re
import sqlite3
import time

DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

CREDIT = ["credit", "udhaar", "udhar", "उधार", "उधर", "borrowed", "owes", "owe me", "baaki likh", "बाकी लिख"]
PAYMENT = ["paid", "pay ", "returned", "gave back", "cleared", "repaid", "deposited", "settled", "wapas", "वापस",
           "chukaye", "chukaya", "चुकाए", "चुकाया", "जमा", "दिए", "diye", "de diye", "लौटाए", "received from", "payment"]
SALE = ["sold", "bech", "becha", "बेचा", "बेचे", "बेच", "sale"]
QUERY = ["how much", "kitna", "कितना", "कितने", "balance", "what does", "what is", "kitne", "hisab", "हिसाब"]

STOP_NAMES = {"sold", "paid", "took", "gave", "received", "how", "what", "the", "and", "credit", "today", "he", "she",
              "rs", "rupees", "ten", "five", "one", "two", "sale", "bought", "returned", "cleared", "balance", "please"}
UNITS = {"kilo": "kg", "kilos": "kg", "kg": "kg", "kgs": "kg", "किलो": "kg", "litre": "L", "litres": "L", "liter": "L",
         "लीटर": "L", "packet": "pkt", "packets": "pkt", "पैकेट": "pkt", "dozen": "dozen", "दर्जन": "dozen",
         "piece": "pc", "pieces": "pc", "पीस": "pc"}
FILLER_ITEMS = {"of", "on", "for", "to", "in", "ka", "ki", "ke", "का", "की", "के", "worth", "rupees", "rs"}


def _norm(s: str) -> str:
    s = s.translate(DEV_DIGITS)
    s = re.sub(r"(?<=\d),(?=\d)", "", s)
    return s.replace("₹", " ₹ ")


def _amount(s: str):
    m = (re.search(r"₹\s*(\d+(?:\.\d+)?)", s)
         or re.search(r"(\d+(?:\.\d+)?)\s*(?:rupees?|rs\.?|rupaye|rupay|रुपये|रुपए|रुपया|रू)", s, re.I))
    if m:
        return float(m.group(1))
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)]
    return nums[-1] if nums else None


def _person(s: str):
    m = re.search(r"([ऀ-ॿ]+)\s+(?:ने|को|से|का|की|के)(?=\s|$)", s)
    if m and m.group(1) not in ("मैंने", "ये", "वो"):
        return m.group(1)
    for m in re.finditer(r"\b(?:to|from|by|for|of)\s+([A-Z][a-z]+)|\b([A-Z][a-z]+)\b(?=\s+(?:ne|ko|se|ka|ki|took|paid|owes|gave|bought|has|returned|cleared))", s):
        name = m.group(1) or m.group(2)
        if name.lower() not in STOP_NAMES:
            return name
    for w in re.findall(r"\b[A-Z][a-z]{2,}\b", s):
        if w.lower() not in STOP_NAMES:
            return w
    return None


def _item(s: str):
    m = re.search(r"(\d+(?:\.\d+)?)\s*(kilos?|kgs?|litres?|liters?|packets?|dozen|pieces?|किलो|लीटर|पैकेट|दर्जन|पीस)\s*(?:of\s+)?([A-Za-zऀ-ॿ]+)?", s, re.I)
    if not m:
        return None, None
    unit = UNITS.get(m.group(2).lower(), m.group(2))
    name = (m.group(3) or "").strip()
    if name.lower() in FILLER_ITEMS or name.lower() in UNITS:
        name = ""
    return f"{m.group(1)} {unit}", name or None


_CONS = {"क": "k", "ख": "kh", "ग": "g", "घ": "gh", "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ट": "t", "ठ": "th",
         "ड": "d", "ढ": "dh", "ण": "n", "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n", "प": "p", "फ": "f", "ब": "b",
         "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh", "ष": "sh", "स": "s", "ह": "h", "ड़": "d",
         "क़": "k", "ज़": "z", "फ़": "f"}
_VOW = {"अ": "a", "आ": "a", "इ": "i", "ई": "i", "उ": "u", "ऊ": "u", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "ऋ": "ri"}
_MATRA = {"ा": "a", "ि": "i", "ी": "i", "ु": "u", "ू": "u", "े": "e", "ै": "ai", "ो": "o", "ौ": "au", "ृ": "ri"}


def canon(name: str) -> str:
    """Canonical key so 'रमेश', 'Ramesh' and 'ramesh' map to the same customer."""
    if not name:
        return ""
    out, chars = [], list(name)
    for i, ch in enumerate(chars):
        nxt = chars[i + 1] if i + 1 < len(chars) else ""
        if ch in _CONS:
            out.append(_CONS[ch])
            if nxt not in _MATRA and nxt != "्" and nxt != "" and nxt not in ("ं", "ँ"):
                out.append("a")  # inherent schwa (dropped at word end)
        elif ch in _VOW:
            out.append(_VOW[ch])
        elif ch in _MATRA:
            out.append(_MATRA[ch])
        elif ch in ("ं", "ँ"):
            out.append("n")
        elif ch != "्":
            out.append(ch.lower())
    key = "".join(out).replace("ee", "i").replace("oo", "u")
    key = re.sub(r"(.)\1+", r"\1", key)  # collapse doubled letters: sunita / suneeta / sunnita
    return key.replace("w", "v").replace("ph", "f")


def _has(s: str, words):
    return any(w in s for w in words)


def parse(transcript: str):
    """Returns a list of dicts: {kind, person, amount, item, qty, source}."""
    entries = []
    for sent in re.split(r"[.।?!\n]+|\s+and then\s+", _norm(transcript)):
        sent = sent.strip()
        if not sent:
            continue
        low = sent.lower()
        raw_q = _has(low, QUERY)
        amt = _amount(sent)
        person = _person(sent)
        qty, item = _item(sent)
        if raw_q and (person or amt is None):
            kind = "query"
        elif _has(low, SALE) and not _has(low, CREDIT):
            kind = "sale"
        elif _has(low, PAYMENT) and not _has(low, CREDIT):
            kind = "payment"
        elif _has(low, CREDIT):
            kind = "credit"
        elif _has(low, SALE):
            kind = "credit"
        elif amt is not None and person:
            kind = "payment" if "paid" in low else "credit"
        else:
            continue
        if kind != "query" and amt is None:
            continue
        entries.append({"kind": kind, "person": person, "amount": amt, "qty": qty, "item": item, "source": sent})
    return entries


class Khata:
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("""CREATE TABLE IF NOT EXISTS entries(
            id INTEGER PRIMARY KEY, ts REAL, kind TEXT, person TEXT, amount REAL, qty TEXT, item TEXT, source TEXT)""")

    def _display_name(self, person):
        """Reuse the first spelling seen for this customer so scripts/spellings merge."""
        if not person:
            return person
        key = canon(person)
        for (p,) in self.db.execute("SELECT DISTINCT person FROM entries WHERE person IS NOT NULL").fetchall():
            if canon(p) == key:
                return p
        return person

    def add(self, e):
        e = {**e, "person": self._display_name(e["person"])}
        self.db.execute("INSERT INTO entries(ts,kind,person,amount,qty,item,source) VALUES(?,?,?,?,?,?,?)",
                        (time.time(), e["kind"], e["person"], e["amount"], e["qty"], e["item"], e["source"]))
        self.db.commit()

    def balances(self):
        rows = self.db.execute("""SELECT person, SUM(CASE kind WHEN 'credit' THEN amount WHEN 'payment' THEN -amount ELSE 0 END)
                                  FROM entries WHERE person IS NOT NULL GROUP BY person""").fetchall()
        return {p: b for p, b in rows if b is not None}

    def balance(self, person):
        return self.balances().get(self._display_name(person), 0.0)

    def recent(self, n=30):
        cur = self.db.execute("SELECT id,ts,kind,person,amount,qty,item,source FROM entries ORDER BY id DESC LIMIT ?", (n,))
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

    def sales_total(self):
        return self.db.execute("SELECT COALESCE(SUM(amount),0) FROM entries WHERE kind='sale'").fetchone()[0]

    def apply(self, transcript):
        """Parse transcript, store non-query entries, answer queries. Returns (entries, answers)."""
        entries, answers = parse(transcript), []
        for e in entries:
            if e["kind"] == "query":
                who = e["person"]
                answers.append({"person": who, "balance": self.balance(who) if who else None})
            else:
                self.add(e)
        return entries, answers


if __name__ == "__main__":
    tests = [
        "Ramesh took 500 rupees on credit. Sunita paid 200 rupees. Sold 10 kilos of rice to Mohan for 600 rupees.",
        "रमेश ने 500 रुपये उधार लिए। सुनीता ने 200 रुपये दिए।",
        "Ramesh ne 300 rupaye udhaar liye. How much does Ramesh owe?",
        "Mohan ko 2 kilo चीनी बेची 90 रुपये में",
        "रमेश का कितना बाकी है?",
    ]
    for t in tests:
        k = Khata()
        e, a = k.apply(t)
        print(t, "\n ", [(x['kind'], x['person'], x['amount'], x['qty'], x['item']) for x in e], a, k.balances())
