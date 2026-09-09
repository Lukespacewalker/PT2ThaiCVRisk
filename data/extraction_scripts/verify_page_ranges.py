import fitz
import re

pdf_path = "ตรวจสุขภาพ รปภ. ปี 2569.pdf"

doc = fitz.open(pdf_path)

def search_title(keyword):
    matches = []
    for i in range(len(doc)):
        text = doc[i].get_text("text")
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        header = " ".join(lines[:3]) if lines else ""
        if keyword in header:
            matches.append((i+1, header[:60]))
    return matches

print("--- CBC Pages ---")
for p, h in search_title("เม็ดเลือด"):
    print(f"P.{p:3d}: {h}")

print("\n--- Occ Vision Pages ---")
for p, h in search_title("สมรรถภาพสายตาอาชีวอนามัย"):
    print(f"P.{p:3d}: {h}")

print("\n--- Audiogram Pages ---")
for p, h in search_title("สมรรถภาพการได้ยิน"):
    print(f"P.{p:3d}: {h}")

print("\n--- Spirometry Pages ---")
for p, h in search_title("สมรรถภาพการทำงานของปอด"):
    print(f"P.{p:3d}: {h}")
