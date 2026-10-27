#!/usr/bin/env python3
"""Заполняет план книги (plan/parts/part_NN.json) из Markdown-файла plan/plan.md.

Формат plan.md:

    # Часть 1 | Название части
    Синопсис части (один или несколько абзацев).

    ## 1 | Название главы | точка зрения
    Содержание главы: 3–5 предложений.
    - сцена: кто хочет чего → что мешает → чем кончилось
    - ...
    => крючок в конце главы

Номера глав сквозные. Поля function и target_pages берутся из каркаса
(book_plan.py skeleton), остальное перезаписывается из plan.md.

  plan_from_md.py <dir> [--md путь]
"""
import argparse
import json
import os
import re
import sys


def parse(text):
    parts, cur_part, cur_ch = [], None, None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        m = re.match(r"^#\s+Часть\s+(\d+)\s*\|\s*(.+)$", line)
        if m:
            cur_part = {"num": int(m.group(1)), "title": m.group(2).strip(), "synopsis": [], "chapters": []}
            parts.append(cur_part)
            cur_ch = None
            continue
        m = re.match(r"^##\s+(\d+)\s*\|\s*([^|]+?)\s*(?:\|\s*(.+))?$", line)
        if m:
            if cur_part is None:
                sys.exit("глава %s вне части" % m.group(1))
            cur_ch = {"num": int(m.group(1)), "title": m.group(2).strip(), "pov": (m.group(3) or "").strip(),
                      "summary": [], "scenes": [], "ends_with": ""}
            cur_part["chapters"].append(cur_ch)
            continue
        s = line.strip()
        if cur_ch is None:
            if cur_part is not None:
                cur_part["synopsis"].append(s)
            continue
        if s.startswith("- "):
            cur_ch["scenes"].append(s[2:].strip())
        elif s.startswith("=>"):
            cur_ch["ends_with"] = s[2:].strip()
        else:
            cur_ch["summary"].append(s)
    return parts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir")
    ap.add_argument("--md")
    a = ap.parse_args()
    md = a.md or os.path.join(a.dir, "plan", "plan.md")
    parts = parse(open(md, encoding="utf-8").read())
    pdir = os.path.join(a.dir, "plan", "parts")
    total = 0
    for p in parts:
        path = os.path.join(pdir, "part_%02d.json" % p["num"])
        if not os.path.exists(path):
            sys.exit("нет %s — сначала book_plan.py skeleton" % path)
        data = json.load(open(path, encoding="utf-8"))
        data["title"] = p["title"]
        data["synopsis"] = " ".join(p["synopsis"])
        by_num = {c["num"]: c for c in data["chapters"]}
        for c in p["chapters"]:
            if c["num"] not in by_num:
                sys.exit("глава %d не входит в часть %d по каркасу" % (c["num"], p["num"]))
            ch = by_num[c["num"]]
            ch["title"] = c["title"]
            ch["pov"] = c["pov"]
            ch["summary"] = " ".join(c["summary"])
            ch["scenes"] = c["scenes"]
            ch["ends_with"] = c["ends_with"]
            ch.pop("beats", None)
            total += 1
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write("\n")
    print("План обновлён из %s: частей %d, глав %d" % (md, len(parts), total))


if __name__ == "__main__":
    main()
