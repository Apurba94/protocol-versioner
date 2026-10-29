"""File-based store: <root>/<protocol>/v001.md, v002.md ... plus history.json."""
import datetime
import difflib
import hashlib
import json
import os
import re


def _slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not s:
        raise ValueError("protocol name must contain letters or digits")
    return s


class ProtocolStore:
    def __init__(self, root="protocols", now=None):
        self.root = root
        self._now = now
        os.makedirs(root, exist_ok=True)

    def now(self):
        return (self._now or datetime.datetime.now()).isoformat(timespec="seconds")

    def _dir(self, name):
        return os.path.join(self.root, _slug(name))

    def _history(self, name):
        p = os.path.join(self._dir(name), "history.json")
        if not os.path.exists(p):
            raise KeyError("no protocol named %r" % name)
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)

    def _write_history(self, name, hist):
        with open(os.path.join(self._dir(name), "history.json"), "w", encoding="utf-8") as fh:
            json.dump(hist, fh, indent=1)

    def protocols(self):
        out = []
        for d in sorted(os.listdir(self.root)):
            if os.path.exists(os.path.join(self.root, d, "history.json")):
                h = self._history(d)
                out.append({"name": d, "title": h["title"], "versions": len(h["versions"]),
                            "updated": h["versions"][-1]["date"], "status": h.get("status", "active")})
        return out

    def add(self, name, text, author="", note="initial version", title=None):
        d = self._dir(name)
        if os.path.exists(os.path.join(d, "history.json")):
            raise ValueError("protocol %r exists; use update" % name)
        os.makedirs(d, exist_ok=True)
        title = title or (re.search(r"^#\s+(.+)$", text, re.M).group(1).strip() if re.search(r"^#\s+(.+)$", text, re.M) else name)
        hist = {"title": title, "status": "active", "versions": []}
        self._write_history(name, hist)
        return self._save_version(name, hist, text, author, note)

    def update(self, name, text, author="", note=""):
        if not note.strip():
            raise ValueError("a change note is required for every new version")
        hist = self._history(name)
        last = hist["versions"][-1]
        if hashlib.sha256(text.encode("utf-8")).hexdigest() == last["sha256"]:
            raise ValueError("text is identical to version %d" % last["version"])
        return self._save_version(name, hist, text, author, note)

    def _save_version(self, name, hist, text, author, note):
        v = len(hist["versions"]) + 1
        fn = "v%03d.md" % v
        with open(os.path.join(self._dir(name), fn), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        hist["versions"].append({"version": v, "file": fn, "date": self.now(), "author": author, "note": note,
                                 "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()})
        self._write_history(name, hist)
        return v

    def get(self, name, version=None):
        hist = self._history(name)
        vs = hist["versions"]
        meta = vs[-1] if version is None else next((x for x in vs if x["version"] == version), None)
        if meta is None:
            raise KeyError("protocol %r has no version %s" % (name, version))
        with open(os.path.join(self._dir(name), meta["file"]), encoding="utf-8") as fh:
            text = fh.read()
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != meta["sha256"]:
            raise ValueError("version %d of %r was modified on disk outside the tool" % (meta["version"], name))
        return text, meta

    def history(self, name):
        return self._history(name)["versions"]

    def diff(self, name, a, b):
        ta, _ = self.get(name, a)
        tb, _ = self.get(name, b)
        return "".join(difflib.unified_diff(ta.splitlines(True), tb.splitlines(True), "v%03d" % a, "v%03d" % b))

    def retire(self, name, reason=""):
        hist = self._history(name)
        hist["status"] = "retired"
        hist["retired_reason"] = reason
        self._write_history(name, hist)

    def export(self, name, version=None):
        """Protocol text with a controlled-document header (title, version, date, author, change note)."""
        hist = self._history(name)
        text, meta = self.get(name, version)
        header = ("> **%s** | version %d | %s | author: %s | status: %s\n> Change: %s\n\n" % (
            hist["title"], meta["version"], meta["date"][:10], meta["author"] or "-", hist.get("status", "active"),
            meta["note"]))
        return header + text
