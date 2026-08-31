from pathlib import Path
import shutil, sys
PATCH_ROOT=Path(__file__).resolve().parent
DELETIONS=[line.strip() for line in (PATCH_ROOT/"DELETIONS.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
if len(sys.argv)!=2:
    raise SystemExit("Usage: python apply_patch.py <target-root>")
target=Path(sys.argv[1]).resolve()
for rel in DELETIONS:
    p=target/rel
    if p.exists() and p.is_file(): p.unlink()
for src in PATCH_ROOT.rglob("*"):
    if not src.is_file(): continue
    rel=src.relative_to(PATCH_ROOT)
    if rel.as_posix() in {"apply_patch.py","PATCH_MANIFEST.txt","DELETIONS.txt"}: continue
    dst=target/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
print("Crystal Guild v1.5.0 Trails & Raids Beta 2 Bot patch applied.")
