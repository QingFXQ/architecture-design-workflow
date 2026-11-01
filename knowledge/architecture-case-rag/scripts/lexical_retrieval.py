"""Offline, transparent text retrieval. Not a semantic or image-understanding model."""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any, Mapping, Sequence
from semantic_index import extract_sections

# Small design vocabulary for optional recall; all matches remain visible.
GROUPS = [
    ("高差", "坡地", "台地", "台阶", "下沉", "退台", "地形"),
    ("滨水", "临水", "湖岸", "水岸", "河岸", "湖畔"),
    ("夜间", "独立开放", "独立运营", "独立入口", "门禁", "闭馆", "分时开放", "24小时"),
    ("开放楼梯", "内梯", "楼梯", "挑空", "竖向联系", "垂直交通"),
    ("后勤", "馆员", "服务流线", "书流", "采编", "卸货"),
    ("遮阳", "百叶", "西晒", "日照"),
]
STOP = {"如何","设计","建筑","空间","方案","处理","组织","可以","一个","一些","联系","公共","同时","需要","问题","通过"}
UNKNOWN = re.compile(r"未提供|未说明|资料不足|无法核实|尚不明确")

def query_terms(query: str) -> set[str]:
    q = query.casefold().strip()
    terms = set(re.findall(r"[a-z][a-z0-9_-]{2,}|\d+(?:\.\d+)?", q))
    for chunk in re.findall(r"[\u4e00-\u9fff]+", q):
        for size in (2,3,4):
            terms.update(chunk[i:i+size] for i in range(max(0,len(chunk)-size+1)))
    terms.difference_update(STOP)
    for group in GROUPS:
        if any(term in q for term in group):
            terms.update(group)
    return terms

def evidence_parts(text: str) -> tuple[str, list[str]]:
    # Keep unknown statements as gaps rather than positive evidence.
    sentences = [x.strip() for x in re.split(r"(?<=[。！？；])|\n+", text) if x.strip()]
    gaps = [x for x in sentences if UNKNOWN.search(x)]
    return "\n".join(x for x in sentences if not UNKNOWN.search(x)), gaps

def retrieve(records: Sequence[Mapping[str,Any]], rag_root: Path, query: str, maximum: int=5) -> list[dict]:
    terms = query_terms(query)
    if not terms: return []
    operational = {"夜间", "独立开放", "独立运营", "独立入口", "门禁", "闭馆", "分时开放", "24小时"}
    operation_focus = any(term in query for term in ("夜间", "独立开放", "独立运营", "门禁", "闭馆"))
    results=[]
    for record in records:
        path=(rag_root/str(record.get("path",""))).resolve()
        if not path.is_relative_to(rag_root.resolve()) or not path.is_file():
            continue
        sections=extract_sections(record,path.read_text(encoding="utf-8-sig"))
        if operation_focus and not any(term in evidence_parts(section["text"])[0]
                for section in sections for term in operational):
            continue
        matches=[]; all_gaps=[]
        for section in sections:
            positive,gaps=evidence_parts(section["text"]);all_gaps.extend(gaps)
            qtext=positive.casefold()
            matched=sorted(term for term in terms if term in qtext)
            if not matched: continue
            score=sum(min(len(term),6) for term in matched)
            if operation_focus:
                score += sum(len(term)*4 for term in matched if term in operational - {"夜间"})
            if section["section"] in {"circulation","plan_to_section","program_to_plan","indoor_outdoor"}:score*=1.15
            matches.append((score,section["section"],positive,matched))
        if not matches:continue
        matches.sort(key=lambda x:(-x[0],x[1]))
        selected=matches[:3]
        result=dict(record)
        result.update({
            "score":round(selected[0][0]+sum(x[0]*.2 for x in selected[1:]),3),
            "retrieval_mode":"lexical",
            "query":query,
            "evidence_sections":[x[1] for x in selected],
            "evidence_texts":[x[2] for x in selected],
            "matched_terms":sorted({t for x in selected for t in x[3]}),
            "evidence_gaps":list(dict.fromkeys(all_gaps)),
            "visual_evidence_checked":False,
        })
        results.append(result)
    return sorted(results,key=lambda x:(-x["score"],str(x.get("id",""))))[:maximum]
