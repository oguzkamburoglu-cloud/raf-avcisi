#!/usr/bin/env python3
"""Checks store text lengths (name 30, subtitle 30, short description 80, keywords 100) in store/*.md."""
import re, pathlib, sys
LIM = [(r"\*\*(Ad|Name|Nombre|Nom|Nome|Название|Uygulama adı)[^*]*\*\*", 30),
       (r"\*\*(Alt başlık|Subtitle|Untertitel|Subtítulo|Sous-titre|Подзаголовок)[^*]*\*\*", 30),
       (r"\*\*(Kısa açıklama|Short description|Kurzbeschreibung|Descripción breve|Description courte|Descrição curta|Краткое описание)[^*]*\*\*", 80),
       (r"\*\*(Anahtar kelimeler|Keywords|Palabras clave|Mots-clés|Palavras-chave|Ключевые слова)[^*]*\*\*", 100)]
bad = 0
for f in sorted(pathlib.Path(__file__).resolve().parent.parent.glob("store/MAGAZA_METINLERI*.md")):
    lines = f.read_text(encoding="utf-8").split("\n")
    for i, l in enumerate(lines):
        for rx, lim in LIM:
            m = re.match(rx + r"\s*(.*)$", l)
            if not m: continue
            val = m.group(2).strip() or (lines[i + 1].strip() if i + 1 < len(lines) else "")
            n = len(val)
            ok = n <= lim
            bad += not ok
            print(f"{'OK ' if ok else 'UZUN'} {n:3}/{lim} {f.name}: {val[:60]}")
sys.exit(1 if bad else 0)
