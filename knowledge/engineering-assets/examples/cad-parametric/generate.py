"""Generate a bounded, editable architectural DXF teaching sample, not a DWG.
Uses ezdxf; --render additionally needs its PyMuPDF drawing backend.
Rebuilds only named files in a dedicated, marked output directory.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import ezdxf

OWNER = "multica-arch-studio/cad-parametric/v1"
HERE = Path(__file__).resolve().parent

def load_params(path):
    p = json.loads(Path(path).read_text(encoding="utf-8"))
    if p.get("units") != "mm":
        raise ValueError("This sample requires explicit mm parameters")
    for key in ("width", "depth", "wall", "column", "window_width", "door_width", "preview_scale"):
        if isinstance(p.get(key), bool) or not isinstance(p.get(key), (float, int)) or not math.isfinite(p[key]) or p[key] <= 0:
            raise ValueError("Positive finite parameter required: " + key)
    if p["width"] < 10000 or p["depth"] < 6000 or p["wall"] >= min(p["width"], p["depth"]) / 10:
        raise ValueError("Use a representative building scale, not arbitrary degenerate inputs")
    return p

def openings(p):
    w, d, ww, door = p["width"], p["depth"], p["window_width"], p["door_width"]
    rows = {
        "south": [w * i / 12 for i in (1,2,3,4,5,7,8,9,10,11)],
        "north": [w * (i + .5) / 10 for i in range(10)],
    }
    data = []
    for row, centres in rows.items():
        spans = [(c - ww / 2, c + ww / 2) for c in centres]
        if row == "south": spans.append(((w-door)/2, (w+door)/2))
        spans.sort()
        if spans[0][0] <= p["wall"] or spans[-1][1] >= w-p["wall"]:
            raise ValueError("An opening reaches a corner")
        if any(a[1] + p["wall"] / 2 > b[0] for a,b in zip(spans, spans[1:])):
            raise ValueError("Openings overlap or leave insufficient sample wall piers")
        for i,c in enumerate(centres, 1):
            data.append({"id": row+"-"+str(i), "row": row, "left": c-ww/2,
                         "right": c+ww/2, "y": 0 if row=="south" else d})
    return data

def remaining(width, spans):
    cursor = 0.0
    for a,b in sorted(spans):
        if a > cursor: yield cursor,a
        cursor = b
    if cursor < width: yield cursor,width

def rect(layout, x0, y0, x1, y1, layer):
    return layout.add_lwpolyline([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],
                                close=True, dxfattribs={"layer":layer})

def build(p, out):
    marker = out / ".asset-owner.json"
    filenames = ("sample.dxf", "sample.pdf", "sample.png", "windows.csv", "verification.json")
    if out.exists() and (any((out/name).exists() for name in filenames)):
        if not marker.exists() or json.loads(marker.read_text(encoding="utf-8")).get("owner") != OWNER:
            raise ValueError("Refusing to overwrite unowned outputs: " + str(out))
    out.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"owner":OWNER})+"\n",encoding="utf-8")
    w,d,t,c = p["width"],p["depth"],p["wall"],p["column"]
    holes = openings(p)
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.header["$LWDISPLAY"] = True
    doc.linetypes.new("ARCH_CENTER", dxfattribs={"description":"centre", "pattern":[1200,700,-150,200,-150]})
    for name,weight,colour in [
        ("A_WALL",25,7),("S_COLUMN_CUT",50,7),("A_WINDOW",13,7),("A_DOOR",18,7),
        ("A_GRID",9,8),("A_DIM",13,7),("A_NOTE",13,7)]:
        doc.layers.new(name, dxfattribs={"lineweight":weight, "color":colour,
                                         "linetype":"ARCH_CENTER" if name=="A_GRID" else "CONTINUOUS"})
    m = doc.modelspace()
    for row,y in (("south",0),("north",d-t)):
        spans = [(h["left"],h["right"]) for h in holes if h["row"]==row]
        if row=="south":spans.append(((w-p["door_width"])/2,(w+p["door_width"])/2))
        for a,b in remaining(w,spans):rect(m,a,y,b,y+t,"A_WALL")
    rect(m,0,t,t,d-t,"A_WALL");rect(m,w-t,t,w,d-t,"A_WALL")
    block = doc.blocks.new("ARCH_WINDOW")
    ww = p["window_width"]
    rect(block,0,0,ww,t,"0")
    for y in (t/3,2*t/3):
        block.add_line((0,y),(ww,y),dxfattribs={"layer":"0","color":0})
    for h in holes:
        at = (h["left"],0) if h["row"]=="south" else (h["right"],d)
        h["insert"] = list(at);h["rotation"] = 0 if h["row"]=="south" else 180
        m.add_blockref("ARCH_WINDOW",at,dxfattribs={"layer":"A_WINDOW","rotation":h["rotation"]})
    door_x = (w-p["door_width"])/2
    m.add_line((door_x,t),(door_x,t+p["door_width"]),dxfattribs={"layer":"A_DOOR"})
    m.add_arc((door_x,t),p["door_width"],0,90,dxfattribs={"layer":"A_DOOR"})
    xs=[c, w/3,2*w/3,w-c];ys=[c,d/2,d-c]
    for x in xs:
        m.add_line((x,-600),(x,d+700),dxfattribs={"layer":"A_GRID"})
    for y in ys:
        m.add_line((-600,y),(w+600,y),dxfattribs={"layer":"A_GRID"})
    for i,x in enumerate(xs,1):
        m.add_circle((x,d+700),160,dxfattribs={"layer":"A_GRID"})
        m.add_text(str(i),dxfattribs={"height":180,"insert":(x-50,d+630),"layer":"A_NOTE"})
    for i,y in enumerate(ys):
        m.add_circle((-600,y),160,dxfattribs={"layer":"A_GRID"})
        m.add_text(chr(65+i),dxfattribs={"height":180,"insert":(-660,y-65),"layer":"A_NOTE"})
    for x in xs:
        for y in ys:
            points=[(x-c/2,y-c/2),(x+c/2,y-c/2),(x+c/2,y+c/2),(x-c/2,y+c/2)]
            rect(m,*points[0],*points[2],"S_COLUMN_CUT")
            m.add_solid([points[0],points[1],points[3],points[2]],dxfattribs={"layer":"S_COLUMN_CUT"})
    override={"dimtxt":230,"dimasz":160,"dimexo":150,"dimexe":100,"dimgap":80,"dimlfac":1,
              "dimtad":1,"dimdec":0,"dimclrd":7,"dimclre":7,"dimclrt":7}
    m.add_linear_dim(base=(0,-1300),p1=(0,0),p2=(w,0),angle=0,
                     override=override,dxfattribs={"layer":"A_DIM"}).render()
    m.add_linear_dim(base=(-1400,0),p1=(0,0),p2=(0,d),angle=90,
                     override=override,dxfattribs={"layer":"A_DIM"}).render()
    m.add_text("EDITABLE CAD SAMPLE / mm",dxfattribs={"height":220,"insert":(0,d+1400),"layer":"A_NOTE"})
    m.add_text("20 shared windows / real wall gaps / structural cuts",
               dxfattribs={"height":160,"insert":(0,d+1050),"layer":"A_NOTE"})
    doc.saveas(out/"sample.dxf")
    with (out/"windows.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=["id","row","left","right","y","insert","rotation"])
        writer.writeheader();writer.writerows(holes)
    return holes

def verify(p, path, holes):
    doc = ezdxf.readfile(path);m=doc.modelspace()
    audit=doc.audit()
    if audit.has_errors or audit.has_fixes:
        raise ValueError("DXF audit required errors/fixes: "+str((len(audit.errors),len(audit.fixes))))
    refs=list(m.query('INSERT[name=="ARCH_WINDOW"]'))
    assert len(refs)==20 and len(list(doc.blocks["ARCH_WINDOW"]))==3
    assert len(m.query('SOLID[layer=="S_COLUMN_CUT"]'))==12
    assert doc.units==ezdxf.units.MM
    coordinates=sorted((round(e.dxf.insert.x,6),round(e.dxf.insert.y,6),e.dxf.rotation) for e in refs)
    expected=sorted((round(h["insert"][0],6),round(h["insert"][1],6),h["rotation"]) for h in holes)
    assert coordinates==expected and all(e.dxf.layer=="A_WINDOW" for e in refs)
    for h in holes:
        middle=(h["left"]+h["right"])/2
        for wall in m.query('LWPOLYLINE[layer=="A_WALL"]'):
            pts=list(wall.get_points("xy"))
            x0,x1=min(x for x,y in pts),max(x for x,y in pts)
            y0,y1=min(y for x,y in pts),max(y for x,y in pts)
            y=p["wall"]/2 if h["row"]=="south" else p["depth"]-p["wall"]/2
            assert not (x0 < middle < x1 and y0 < y < y1), "Window opening blocked"
    dimensions=sorted(round(float(e.get_measurement()),5) for e in m.query("DIMENSION"))
    assert dimensions==sorted([p["width"],p["depth"]])
    assert all(e.override().get("dimlfac",1)==1 for e in m.query("DIMENSION"))
    return {"state":"offline-tested","units":"mm","window_instances":len(refs),
            "window_definitions":1,"column_cuts":12,"dimensions_mm":dimensions,
            "wall_openings_clear":True,"audit_errors":len(audit.errors),"audit_fixes":len(audit.fixes),
            "entity_counts":dict(sorted(Counter(e.dxftype() for e in m).items())),
            "host_verified":False,"dwg_verified":False}

def render(dxf_path,out,p):
    from ezdxf.addons.drawing import Frontend,RenderContext,layout,pymupdf as drawing_pdf
    from ezdxf.addons.drawing.config import Configuration,BackgroundPolicy,ColorPolicy
    import pymupdf
    doc=ezdxf.readfile(dxf_path);backend=drawing_pdf.PyMuPdfBackend()
    config=Configuration(background_policy=BackgroundPolicy.WHITE,color_policy=ColorPolicy.BLACK)
    Frontend(RenderContext(doc),backend,config=config).draw_layout(doc.modelspace())
    page=layout.Page(210,148,layout.Units.mm,margins=layout.Margins.all(8))
    settings=layout.Settings(scale=1/p["preview_scale"],fit_page=False)
    pdf_bytes=backend.get_pdf_bytes(page,settings=settings)
    (out/"sample.pdf").write_bytes(pdf_bytes)
    # The recorder transforms its content during PDF export. Rasterize that
    # actual PDF instead of reusing the transformed backend for a second export.
    with pymupdf.open(stream=pdf_bytes,filetype="pdf") as preview:
        preview[0].get_pixmap(dpi=150).save(str(out/"sample.png"))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--params",type=Path,default=HERE/"params.json")
    ap.add_argument("--out-dir",type=Path,default=HERE/"out")
    ap.add_argument("--render",action="store_true")
    args=ap.parse_args()
    p=load_params(args.params);out=args.out_dir.resolve()
    holes=build(p,out);report=verify(p,out/"sample.dxf",holes)
    if args.render:render(out/"sample.dxf",out,p)
    else:
        # These exact files belong to this sample (build checked the owner).
        for name in ("sample.pdf","sample.png"):
            (out/name).unlink(missing_ok=True)
    report["parameters"]=p
    report["files"]={file.name:{"bytes":file.stat().st_size,
        "sha256":hashlib.sha256(file.read_bytes()).hexdigest()}
        for file in [out/"sample.dxf",out/"windows.csv",*[out/x for x in ("sample.pdf","sample.png") if args.render]]}
    (out/"verification.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0

if __name__=="__main__":
    sys.exit(main())
