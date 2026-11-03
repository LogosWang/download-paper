"""Merge per-subfolder RIS files into a master RIS and a Zotero RDF with collection hierarchy.
Usage: build_zotero.py <base_dir> <collection_name> [<subdir>=<Display Name> ...]"""
import sys, os, re, glob, html
B = sys.argv[1]; NAME = sys.argv[2]; names = dict(a.split("=",1) for a in sys.argv[3:])
def parse(ris):
    recs=[]; cur={}
    for line in open(ris, encoding="utf-8"):
        m=re.match(r"^([A-Z][A-Z0-9])  - ?(.*)$", line.rstrip("\n"))
        if not m: continue
        k,v=m.groups()
        if k=="ER": recs.append(cur); cur={}; continue
        cur.setdefault(k,[]).append(v)
    return recs
master=[]; subs=[]
for sub in sorted(d for d in os.listdir(B) if os.path.isdir(os.path.join(B,d)) and not d.startswith((".","_"))):
    ris=glob.glob(os.path.join(B,sub,"*.ris"))
    if not ris: continue
    recs=parse(ris[0]); subs.append((sub,recs))
    master.append(open(ris[0],encoding="utf-8").read().rstrip()+"\n")
open(os.path.join(B,NAME+".ris"),"w",encoding="utf-8").write("\n".join(master))
# Zotero RDF
E=html.escape; out=[]; n=0
def item_rdf(r, iid):
    global n
    au="".join(f'<rdf:li><foaf:Person><foaf:surname>{E(a.split(",")[0].strip())}</foaf:surname><foaf:givenName>{E(a.split(",",1)[1].strip() if "," in a else "")}</foaf:givenName></foaf:Person></rdf:li>' for a in r.get("AU",[]))
    jn=r.get("T2",[""])[0]; issn="".join(f'<dc:identifier>ISSN {E(s)}</dc:identifier>' for s in r.get("SN",[]))
    vol=r.get("VL",[""])[0]; iss=r.get("IS",[""])[0]; pages=r.get("SP",[""])[0]; doi=r.get("DO",[""])[0]; yr=r.get("PY",[""])[0]
    ty=r.get("TY",["JOUR"])[0]; ztype={"JOUR":"journalArticle","THES":"thesis","BOOK":"book"}.get(ty,"journalArticle")
    bibcls={"JOUR":"bib:Article","THES":"bib:Thesis","BOOK":"bib:Book"}.get(ty,"bib:Article")
    atts=""
    for i,p in enumerate(r.get("L1",[])):
        n+=1; aid=f"#att_{iid}_{i}"; rel=os.path.relpath(p,B)
        out.append(f'<z:Attachment rdf:about="{aid}"><z:itemType>attachment</z:itemType><rdf:resource rdf:resource="{E(rel)}"/><dc:title>{E(os.path.basename(p))}</dc:title><z:linkMode>1</z:linkMode><link:type>application/pdf</link:type></z:Attachment>')
        atts+=f'<link:link rdf:resource="{aid}"/>'
    part=f'<dcterms:isPartOf><bib:Journal><dc:title>{E(jn)}</dc:title>{issn}{f"<prism:volume>{E(vol)}</prism:volume>" if vol else ""}{f"<prism:number>{E(iss)}</prism:number>" if iss else ""}</bib:Journal></dcterms:isPartOf>' if ty=="JOUR" else ""
    return (f'<{bibcls} rdf:about="#item_{iid}"><z:itemType>{ztype}</z:itemType>{part}<bib:authors><rdf:Seq>{au}</rdf:Seq></bib:authors>'
            f'{atts}<dc:title>{E(r.get("TI",[""])[0])}</dc:title>{f"<dc:identifier>DOI {E(doi)}</dc:identifier>" if doi else ""}'
            f'{f"<dcterms:identifier>{E(r.get(chr(85)+chr(82),[chr(0)])[0])}</dcterms:identifier>" if False else ""}'
            f'{f"<dc:date>{E(yr)}</dc:date>" if yr else ""}{f"<bib:pages>{E(pages)}</bib:pages>" if pages else ""}</{bibcls}>')
iid=0; colls=[]; top_parts=[]
for sub,recs in subs:
    parts=[]
    for r in recs:
        iid+=1; out.append(item_rdf(r,iid)); parts.append(f'<dcterms:hasPart rdf:resource="#item_{iid}"/>')
    cid=f"#coll_{sub}"; colls.append(f'<z:Collection rdf:about="{cid}"><dc:title>{E(names.get(sub,sub))}</dc:title>{"".join(parts)}</z:Collection>'); top_parts.append(f'<dcterms:hasPart rdf:resource="{cid}"/>')
colls.append(f'<z:Collection rdf:about="#coll_top"><dc:title>{E(NAME)}</dc:title>{"".join(top_parts)}</z:Collection>')
rdf=('<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:z="http://www.zotero.org/namespaces/export#" xmlns:dcterms="http://purl.org/dc/terms/" '
     'xmlns:bib="http://purl.org/net/biblio#" xmlns:foaf="http://xmlns.com/foaf/0.1/" xmlns:link="http://purl.org/rss/1.0/modules/link/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:prism="http://prismstandard.org/namespaces/1.2/basic/">\n'
     + "\n".join(out+colls) + "\n</rdf:RDF>\n")
open(os.path.join(B,NAME+".rdf"),"w",encoding="utf-8").write(rdf)
print("master RIS records:", sum(len(r) for _,r in subs), "| RDF items:", iid, "attachments:", n, "| collections:", len(colls))
for s,r in subs: print(f"  {s}: {len(r)}")
