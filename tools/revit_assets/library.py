"""Collect and query native Revit assets, without opening or changing Revit.

Large files and generated metadata live under --root / REVIT_ASSET_ROOT.
Requires olefile for native metadata; Pillow only for contact sheets.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import struct
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

DEFAULT_ROOT = Path(os.environ.get("REVIT_ASSET_ROOT", str(Path.home() / ".cache" / "architecture-design-workflow" / "revit-assets")))
CONFIG = Path(__file__).resolve().parents[2] / "knowledge/engineering-assets/revit-library/sources.json"
KINDS = {".rfa": "family", ".rft": "family_template", ".rte": "project_template", ".rvt": "project"}
MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")
ALIASES = {
    "Doors": "门 门族 单扇 双扇", "Windows": "窗 窗族 固定窗",
    "Furniture": "家具 桌 椅 沙发 书柜", "Furniture System": "办公家具",
    "Columns": "柱 建筑柱", "Structural Columns": "结构柱 承重柱 钢柱 混凝土柱",
    "Structural Framing": "结构梁 钢梁 混凝土梁", "Structural Trusses": "桁架",
    "Structural Foundations": "基础", "Curtain Wall Panels": "幕墙 面板 玻璃",
    "Curtain Panel By Pattern": "幕墙 图案面板", "Profiles": "轮廓 扶手 线脚",
    "Railings": "栏杆 扶手 楼梯", "Titleblocks": "图框 图签 图纸",
    "Annotations": "注释 标注 标高 符号 标签", "Detail Items": "详图 二维",
    "Casework": "橱柜 书柜 柜体", "Openings": "洞口 开洞",
    "Mass": "体量 概念", "Planting": "植物 树木", "Site": "场地 停车",
    "Lighting": "灯具 照明", "Plumbing": "卫生 洁具 马桶 洗手盆",
    "Electrical": "电气", "Mechanical": "暖通 设备", "Fire Protection": "消防",
    "Structural Precast": "预制结构", "结构预制": "预制结构",
}
ATOM = "{http://www.w3.org/2005/Atom}"
PART = "{urn:schemas-autodesk-com:partatom}"


def dependency(root):
    sys.path.insert(0, str(root / "tools/python-libs"))
    try:
        import olefile
    except ImportError as exc:
        raise SystemExit("Install olefile into ROOT/tools/python-libs; see README.") from exc
    return olefile


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def native_check(path):
    with path.open("rb") as f:
        if f.read(8) != MAGIC:
            raise ValueError(f"Not a Revit compound-file container: {path.name}")


def basic_info(data):
    # The format field is near the beginning; later dates are build/save dates.
    heads = [data[i:160].decode("utf-16-le", errors="ignore") for i in (0, 1)]
    years = [int(m.group()) for s in heads for m in re.finditer(r"(?<!\d)20[0-4]\d(?!\d)", s)]
    text = "\n".join(data[i:].decode("utf-16-le", errors="ignore") for i in (0, 1))
    build = re.search(r"20\d{6}_\d{4}\(x64\)", text)
    return {"revit_year": years[0] if years else None, "build": build.group() if build else None}


def partatom_info(data):
    tree = ET.fromstring(data)
    category = None
    for c in tree.findall(ATOM + "category"):
        if c.findtext(ATOM + "scheme") == "adsk:revit:grouping":
            category = c.findtext(ATOM + "term")
    family = tree.find(PART + "family")
    types, type_parameters = [], {}
    if family is not None:
        for p in family.findall(PART + "part"):
            title = p.findtext(ATOM + "title")
            if title:
                types.append(title)
                type_parameters[title] = [
                    {"name": child.attrib.get("displayName", child.tag.split("}")[-1]),
                     "value": child.text or "", "units": child.attrib.get("units"),
                     "parameter_type": child.attrib.get("typeOfParameter")}
                    for child in p if child.tag != ATOM + "title"
                ]
    return {"family_name": tree.findtext(ATOM + "title"), "category": category,
            "types": list(dict.fromkeys(types)), "type_parameters": type_parameters}


def preview_png(data):
    start = data.find(b"\x89PNG\r\n\x1a\n")
    if start < 0:
        return None
    pos = start + 8
    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        end = pos + 12 + length
        if end > len(data):
            return None
        if data[pos + 4:pos + 8] == b"IEND":
            return data[start:end]
        pos = end
    return None


def inspect_native(path, root, digest):
    olefile = dependency(root)
    native_check(path)
    meta = {"revit_year": None, "build": None, "family_name": None,
            "category": None, "types": [], "type_parameters": {}, "preview": None}
    with olefile.OleFileIO(str(path)) as ole:
        if not ole.exists("BasicFileInfo"):
            raise ValueError("Missing Revit BasicFileInfo stream")
        meta.update(basic_info(ole.openstream("BasicFileInfo").read()))
        if ole.exists("PartAtom"):
            try:
                meta.update(partatom_info(ole.openstream("PartAtom").read()))
            except (ET.ParseError, UnicodeError):
                meta["partatom_warning"] = "unreadable"
        if ole.exists("RevitPreview4.0"):
            png = preview_png(ole.openstream("RevitPreview4.0").read())
            if png:
                target = root / "previews" / (digest + ".png")
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    target.write_bytes(png)
                meta["preview"] = str(target.relative_to(root))
    return meta


def load_sources(config):
    return json.loads(config.read_text(encoding="utf-8"))["sources"]


def collect_local(root, sources):
    collected = []
    for src in sources:
        if src["method"] != "local-copy":
            continue
        base = Path(src["local_path"])
        if not base.is_dir():
            print(f"SKIP unavailable local source: {src['id']}", flush=True)
            continue
        accepted = set(src.get("extensions", KINDS))
        count = 0
        for original in sorted(base.rglob("*")):
            suffix = original.suffix.lower()
            auxiliary = src.get("copy_type_catalogs", False) and suffix in {".txt", ".csv"}
            if not original.is_file() or (suffix not in accepted and not auxiliary):
                continue
            relative = original.relative_to(base)
            if src.get("include") and str(relative).replace("\\", "/") not in src["include"]:
                continue
            dest = root / "originals" / src["id"] / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            # Hash both sides before skipping, so same-size corruption is repaired.
            if not dest.exists() or original.stat().st_size != dest.stat().st_size or sha256(original) != sha256(dest):
                shutil.copy2(original, dest)
            count += 1
        collected.append({"source": src["id"], "files": count})
        print(f"COPY {src['id']}: {count} files (native + requested companion files)", flush=True)
    return collected


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)


def download(url, dest, native=False):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https":
        raise ValueError("Only HTTPS sources are supported")
    quoted = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, urllib.parse.quote(urllib.parse.unquote(parsed.path)), parsed.query, ""))
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if native:
            native_check(dest)
        return {"path": str(dest), "state": "existing", "bytes": dest.stat().st_size}
    part = dest.with_name(dest.name + ".part")
    try:
        request = urllib.request.Request(quoted, headers={"User-Agent": "Mozilla/5.0 (compatible; RevitAssetLibrary/1.0; local research)"})
        with urllib.request.urlopen(request, timeout=75) as r, part.open("wb") as f:
            expected = int(r.headers["Content-Length"]) if r.headers.get("Content-Length") else None
            total = 0
            while block := r.read(1024 * 1024):
                f.write(block)
                total += len(block)
            if expected is not None and total != expected:
                raise ValueError(f"Incomplete response: {total}/{expected}")
        if native:
            native_check(part)
        part.replace(dest)
        return {"path": str(dest), "state": "downloaded", "bytes": total}
    except Exception:
        part.unlink(missing_ok=True)
        raise


def collect_web(root, sources):
    results = []
    for src in sources:
        if src["method"] not in {"official-links", "reference-downloads"}:
            continue
        try:
            items = list(src.get("downloads", []))
            if src["method"] == "official-links":
                page = root / "sources" / (src["id"] + ".html")
                download(src["url"], page)
                parser = Links()
                parser.feed(page.read_text(encoding="utf-8"))
                for href in parser.links:
                    url = urllib.parse.urljoin(src["url"], href)
                    if src["match"] in urllib.parse.unquote(url) and url.lower().endswith(".rvt"):
                        if urllib.parse.urlsplit(url).hostname not in src["allowed_hosts"]:
                            raise ValueError("Unexpected download host")
                        items.append({"url": url, "name": urllib.parse.unquote(url.rsplit("/", 1)[1])})
                items = list({i["url"]: i for i in items}.values())
                if len(items) != src["expected_files"]:
                    raise ValueError(f"Official link count changed: {len(items)}")
            for item in items:
                dest = root / ("references" if src["method"] == "reference-downloads" else "originals") / src["id"] / item["name"]
                try:
                    result = download(item["url"], dest, native=dest.suffix.lower() in KINDS)
                    result.update(source=src["id"], url=item["url"])
                    results.append(result)
                    print(f"GET {dest.name}: {result['state']} {result['bytes']:,} B", flush=True)
                except Exception as e:
                    results.append({"source": src["id"], "url": item["url"], "error": str(e)})
                    print(f"FAILED {item['name']}: {e}", flush=True)
        except Exception as e:
            results.append({"source": src["id"], "error": str(e)})
    target = root / "manifests/downloads.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return results


def connect(root):
    db = root / "database/revit-assets.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    return con


def build(root, sources):
    con = connect(root)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY, title TEXT, url TEXT, method TEXT, rights TEXT, details_json TEXT);
    CREATE TABLE IF NOT EXISTS assets(id TEXT PRIMARY KEY, source_id TEXT, relative_path TEXT UNIQUE,
      name TEXT, kind TEXT, category TEXT, category_basis TEXT, revit_year INTEGER, build TEXT,
      family_name TEXT, sha256 TEXT, bytes INTEGER, preview TEXT, verification TEXT,
      search_text TEXT, FOREIGN KEY(source_id) REFERENCES sources(id));
    CREATE TABLE IF NOT EXISTS family_types(asset_id TEXT, name TEXT, PRIMARY KEY(asset_id,name));
    CREATE TABLE IF NOT EXISTS type_parameters(asset_id TEXT, type_name TEXT, parameters_json TEXT, PRIMARY KEY(asset_id,type_name));
    CREATE TABLE IF NOT EXISTS auxiliary_files(relative_path TEXT PRIMARY KEY, source_id TEXT, asset_id TEXT, bytes INTEGER, sha256 TEXT);
    CREATE TABLE IF NOT EXISTS reference_files(relative_path TEXT PRIMARY KEY, source_id TEXT, bytes INTEGER, sha256 TEXT, pages INTEGER);
    CREATE TABLE IF NOT EXISTS candidates(id TEXT PRIMARY KEY, details_json TEXT);
    """)
    con.execute("DELETE FROM sources")
    con.execute("DELETE FROM candidates")
    for src in sources:
        con.execute("INSERT INTO sources VALUES(?,?,?,?,?,?)", (src["id"], src["title"], src["url"], src["method"], src["rights"], json.dumps(src, ensure_ascii=False)))
        if src["method"] == "candidate":
            con.execute("INSERT INTO candidates VALUES(?,?)", (src["id"], json.dumps(src, ensure_ascii=False)))
    con.execute("DELETE FROM assets")
    con.execute("DELETE FROM family_types")
    con.execute("DELETE FROM type_parameters")
    con.execute("DELETE FROM auxiliary_files")
    con.execute("DELETE FROM reference_files")
    failures, counts, inventory = [], {}, []
    for n, path in enumerate(sorted((root / "originals").rglob("*"))):
        if not path.is_file() or path.suffix.lower() not in KINDS:
            continue
        relative = path.relative_to(root)
        source_id = relative.parts[1]
        if source_id not in {s["id"] for s in sources}:
            failures.append({"path": str(relative), "error": "source not registered"})
            continue
        try:
            digest = sha256(path)
            meta = inspect_native(path, root, digest)
            category = meta["category"]
            basis = "PartAtom" if category else "directory-inferred"
            inferred = relative.parts[2] if len(relative.parts) > 3 else ""
            category = category or inferred or KINDS[path.suffix.lower()]
            labels = ALIASES.get(category, "") + " " + ALIASES.get(inferred, "")
            kind = KINDS[path.suffix.lower()]
            label_kind = {"family": "族 RFA", "project": "工程 项目 RVT", "project_template": "工程模板 样板 RTE", "family_template": "族样板 RFT"}[kind]
            aid = hashlib.sha256(str(relative).encode("utf-8")).hexdigest()[:20]
            rec = dict(id=aid, source_id=source_id, relative_path=str(relative), name=path.name, kind=kind,
                       category=category, category_basis=basis, revit_year=meta["revit_year"], build=meta["build"],
                       family_name=meta["family_name"], sha256=digest, bytes=path.stat().st_size, preview=meta["preview"],
                       verification="native-container-verified", search_text=" ".join([str(relative), label_kind, category, labels, *meta["types"]]))
            cols = list(rec)
            con.execute(f"INSERT INTO assets ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})", list(rec.values()))
            con.executemany("INSERT INTO family_types VALUES(?,?)", [(aid, t) for t in meta["types"]])
            con.executemany("INSERT INTO type_parameters VALUES(?,?,?)", [(aid, t, json.dumps(v, ensure_ascii=False)) for t, v in meta["type_parameters"].items()])
            inventory.append({**{k: v for k, v in rec.items() if k != "search_text"}, "type_count": len(meta["types"])})
            counts[kind] = counts.get(kind, 0) + 1
        except Exception as e:
            failures.append({"path": str(relative), "error": str(e)})
        if sum(counts.values()) and sum(counts.values()) % 500 == 0:
            print(f"INDEX {sum(counts.values())} native assets", flush=True)
    native_paths = {str((root / i["relative_path"]).with_suffix("")): i["id"] for i in inventory}
    for path in sorted((root / "originals").rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".txt", ".csv"}:
            continue
        rel = path.relative_to(root)
        con.execute("INSERT INTO auxiliary_files VALUES(?,?,?,?,?)", (str(rel), rel.parts[1], native_paths.get(str(path.with_suffix(""))), path.stat().st_size, sha256(path)))
    for path in sorted((root / "references").rglob("*.pdf")):
        try:
            import fitz
            with fitz.open(path) as document:
                pages = len(document)
            rel = path.relative_to(root)
            con.execute("INSERT INTO reference_files VALUES(?,?,?,?,?)", (str(rel), rel.parts[1], path.stat().st_size, sha256(path), pages))
        except Exception as e:
            failures.append({"path": str(path.relative_to(root)), "error": str(e)})
    con.commit()
    con.execute("PRAGMA optimize")
    summary = {"generated_on": datetime.now().date().isoformat(), "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "root": str(root), "database": str(root / "database/revit-assets.sqlite"),
               "counts": counts, "files": len(inventory), "bytes": sum(i["bytes"] for i in inventory),
               "years": [dict(r) for r in con.execute("SELECT revit_year,COUNT(*) AS files FROM assets GROUP BY revit_year")],
               "family_types": con.execute("SELECT COUNT(*) FROM family_types").fetchone()[0],
               "previews": sum(bool(i["preview"]) for i in inventory), "errors": failures,
               "type_catalogs_and_auxiliary": con.execute("SELECT COUNT(*) FROM auxiliary_files").fetchone()[0],
               "reference_pdfs": con.execute("SELECT COUNT(*) FROM reference_files").fetchone()[0],
               "host_verified": False, "host_note": "Offline OLE/BasicFileInfo/PartAtom checks only; no project opened or changed in Revit."}
    out = root / "manifests"
    out.mkdir(exist_ok=True)
    (out / "verification.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "assets.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out / "inventory.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(inventory[0]) if inventory else ["id"])
        w.writeheader()
        w.writerows(inventory)
    con.close()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def query(root, words, kind=None, revit=None, limit=12):
    # The query is parameterized; multi-word searches require every term.
    con = connect(root)
    where, params = [], []
    for word in words.split():
        where.append("search_text LIKE ? ESCAPE '\\'")
        params.append("%" + word.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%")
    if kind:
        where.append("kind=?")
        params.append(kind)
    if revit:
        where.append("revit_year IS NOT NULL AND revit_year<=?")
        params.append(revit)
    rows = con.execute("SELECT id,name,kind,category,revit_year,relative_path,preview,verification,source_id FROM assets" +
                       (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY name LIMIT ?", params + [limit]).fetchall()
    result = [{**dict(row), "path": str(root / row["relative_path"])} for row in rows]
    con.close()
    return result


def stage(root, asset_id, destination, revit=2021):
    """Copy one compatible original with its same-stem catalog; never overwrite a changed file."""
    con = connect(root)
    row = con.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
    if row is None:
        raise ValueError("Unknown asset ID")
    if row["revit_year"] is None or row["revit_year"] > revit:
        raise ValueError("Version unknown or newer than target Revit")
    destination = destination.resolve()
    if destination.is_relative_to((root / "originals").resolve()):
        raise ValueError("Working copies cannot be written into originals")
    files = [(root / row["relative_path"], row["sha256"])]
    files += [(root / a["relative_path"], a["sha256"]) for a in con.execute("SELECT * FROM auxiliary_files WHERE asset_id=?", (asset_id,))]
    con.close()
    for source, digest in files:
        if sha256(source) != digest:
            raise ValueError(f"Original changed since indexing: {source.name}")
        dest = destination / source.name
        if dest.exists() and sha256(dest) != digest:
            raise ValueError(f"Refusing to overwrite a changed working copy: {dest}")
    destination.mkdir(parents=True, exist_ok=True)
    for source, digest in files:
        dest = destination / source.name
        if not dest.exists():
            shutil.copy2(source, dest)
    return {"asset_id": asset_id, "paths": [str(destination / f.name) for f, _ in files], "note": "Working copies; originals unchanged. Project links need companion models copied separately."}


def export_browser(root):
    con = connect(root)
    rows = [dict(r) for r in con.execute("""SELECT id,name,kind,category,revit_year,relative_path,preview,search_text,source_id FROM assets
      ORDER BY CASE kind WHEN 'project_template' THEN 0 WHEN 'project' THEN 1 WHEN 'family' THEN 2 ELSE 3 END,
      CASE category WHEN 'Doors' THEN 0 WHEN 'Windows' THEN 1 WHEN 'Furniture' THEN 2
        WHEN 'Structural Columns' THEN 3 WHEN 'Structural Framing' THEN 4 WHEN 'Title Blocks' THEN 5 ELSE 10 END,category,name""")]
    references = [dict(r) for r in con.execute("SELECT relative_path,pages FROM reference_files ORDER BY relative_path")]
    candidates = [json.loads(r[0]) for r in con.execute("SELECT details_json FROM candidates ORDER BY id")]
    con.close()
    payload = json.dumps(rows, ensure_ascii=False).replace("<", "\\u003c")
    reference_html = "<details><summary>比赛参考与待申请模型（与原生文件分开）</summary><ul>"
    for ref in references:
        reference_html += f'<li><a href="{html.escape(ref["relative_path"].replace(chr(92), "/"), quote=True)}">{html.escape(Path(ref["relative_path"]).name)}</a> · {ref["pages"]} 页参考 PDF</li>'
    for candidate in candidates:
        reference_html += f'<li><a href="{html.escape(candidate["url"], quote=True)}">{html.escape(candidate["title"])}</a> · 尚无已取得原生模型</li>'
    reference_html += "</ul></details>"
    page = '''<!doctype html><html lang="zh"><meta charset="utf-8"><title>Revit 原生工程与族库</title>
<style>body{font:16px system-ui;margin:32px;color:#263b42;background:#f6f5f0}h1{font-size:28px}header{position:sticky;top:0;background:#f6f5f0;padding:12px 0;z-index:1}input,select{font:inherit;padding:10px;margin:4px;border:1px solid #aaa}#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(235px,1fr));gap:16px}article{background:white;padding:16px;border:1px solid #ddd;overflow-wrap:anywhere}img{width:100%;height:150px;object-fit:contain}a{color:#155e63}small{display:block;color:#59676c;margin:8px 0}button{padding:10px}p{max-width:1000px;line-height:1.6}</style>
<h1>Revit 原生工程与族库</h1><p>官方安装内容与官方下载样例。已核文件容器、版本与可提取元数据；尚未逐个在 Revit 打开。版本筛选会排除无法被选定宿主打开的较新版文件。原件保留，使用时另存工作副本。原件与预览只供本机使用，不作为可自由转售／再分发的授权。</p>
__REFERENCES__
<header><input id="q" placeholder="搜索：窗、家具、门、梁、工程模板…"><select id="kind"><option value="">全部类型</option><option value="project">工程 RVT</option><option value="project_template">工程模板 RTE</option><option value="family">族 RFA</option><option value="family_template">族样板 RFT</option></select><select id="ver"><option value="2021">Revit 2021 格式兼容</option><option value="2024">Revit 2024 格式兼容</option><option value="">全部／不筛版本</option></select><span id="count"></span></header><div id="grid"></div><button id="more">再显示 60 个</button>
<script>const data=__DATA__;let visible=60;const q=document.getElementById('q'),kind=document.getElementById('kind'),ver=document.getElementById('ver'),grid=document.getElementById('grid');function render(){const terms=q.value.toLocaleLowerCase().trim().split(/\\s+/).filter(Boolean);const result=data.filter(x=>(!kind.value||x.kind===kind.value)&&(!ver.value||(x.revit_year&&x.revit_year<=+ver.value))&&terms.every(t=>x.search_text.toLocaleLowerCase().includes(t)));document.getElementById('count').textContent=result.length+' 项';grid.replaceChildren();for(const x of result.slice(0,visible)){let a=document.createElement('article');if(x.preview){let im=document.createElement('img');im.src=x.preview.replaceAll('\\\\','/');im.loading='lazy';a.append(im)}let link=document.createElement('a');link.href=x.relative_path.replaceAll('\\\\','/');link.textContent=x.name;a.append(link);for(const t of [x.category+' · '+x.kind+' · Revit '+(x.revit_year||'未知'),x.source_id,'ID: '+x.id,x.relative_path]){let s=document.createElement('small');s.textContent=t;a.append(s)}grid.append(a)}}for(const e of [q,kind,ver])e.addEventListener('input',()=>{visible=60;render()});document.getElementById('more').onclick=()=>{visible+=60;render()};render();</script></html>'''.replace("__DATA__", payload).replace("__REFERENCES__", reference_html)
    (root / "浏览原生工程与族库.html").write_text(page, encoding="utf-8")
    return len(rows)


def contact_sheets(root):
    """Representative embedded previews, not a substitute for a host drawing check."""
    from PIL import Image, ImageDraw, ImageFont
    font_path = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts/msyh.ttc"
    font = ImageFont.truetype(str(font_path), 17) if font_path.exists() else ImageFont.load_default()
    con = connect(root)
    choices = []
    for cat in ("Doors", "Windows", "Furniture", "Structural Columns", "Structural Framing", "Curtain Wall Panels", "Title Blocks", "Profiles"):
        choices += list(con.execute("SELECT * FROM assets WHERE kind='family' AND category=? AND preview IS NOT NULL ORDER BY bytes DESC LIMIT 3", (cat,)))
    groups = {"族文件预览抽查": choices, "原生工程预览抽查": list(con.execute("SELECT * FROM assets WHERE kind='project' AND preview IS NOT NULL ORDER BY source_id,name"))}
    con.close()
    outputs = []
    for title, rows in groups.items():
        cols, w, h = 4, 360, 260
        sheet = Image.new("RGB", (cols * w, 60 + ((len(rows) + cols - 1) // cols) * h), "#f5f5f2")
        draw = ImageDraw.Draw(sheet)
        draw.text((20, 15), title + " · 文件内嵌预览", font=font, fill="#273a40")
        for n, row in enumerate(rows):
            x, y = (n % cols) * w, 60 + (n // cols) * h
            im = Image.open(root / row["preview"]).convert("RGBA")
            im.thumbnail((w - 20, h - 70))
            white = Image.new("RGBA", im.size, "white")
            white.alpha_composite(im)
            sheet.paste(white.convert("RGB"), (x + (w - im.width) // 2, y))
            label = row["name"]
            lines = [label[i:i + 33] for i in range(0, len(label), 33)][:2]
            draw.text((x + 10, y + h - 65), "\n".join(lines), font=font, fill="#263b42")
            draw.text((x + 10, y + h - 22), "Revit " + str(row["revit_year"]), font=font, fill="#59676c")
        target = root / "previews" / (title + ".jpg")
        sheet.save(target, quality=90)
        outputs.append(str(target))
    return outputs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    p.add_argument("--sources", type=Path, default=CONFIG)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("collect-local")
    sub.add_parser("collect-web")
    sub.add_parser("build")
    sub.add_parser("browser")
    sub.add_parser("contact-sheets")
    st = sub.add_parser("stage")
    st.add_argument("--id", required=True)
    st.add_argument("--dest", required=True, type=Path)
    st.add_argument("--revit", type=int, default=2021)
    ty = sub.add_parser("types")
    ty.add_argument("--id", required=True)
    search = sub.add_parser("search")
    search.add_argument("query", nargs="?", default="")
    search.add_argument("--kind", choices=list(KINDS.values()))
    search.add_argument("--revit", type=int, default=2021)
    search.add_argument("--all-versions", action="store_true")
    search.add_argument("--limit", type=int, default=12)
    a = p.parse_args()
    a.root.mkdir(parents=True, exist_ok=True)
    if a.command == "collect-local":
        collect_local(a.root, load_sources(a.sources))
    elif a.command == "collect-web":
        collect_web(a.root, load_sources(a.sources))
    elif a.command == "build":
        build(a.root, load_sources(a.sources))
    elif a.command == "browser":
        print({"browser_assets": export_browser(a.root)})
    elif a.command == "contact-sheets":
        print(json.dumps(contact_sheets(a.root), ensure_ascii=False))
    elif a.command == "stage":
        print(json.dumps(stage(a.root, a.id, a.dest, a.revit), ensure_ascii=False, indent=2))
    elif a.command == "types":
        con = connect(a.root)
        result = [{"name": r[0], "parameters": json.loads(r[1])} for r in con.execute("SELECT type_name,parameters_json FROM type_parameters WHERE asset_id=? ORDER BY type_name", (a.id,))]
        con.close()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(query(a.root, a.query, a.kind, None if a.all_versions else a.revit, a.limit), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
