import os, json, time, re
from pathlib import Path
from datetime import datetime
import requests

API="https://opendart.fss.or.kr/api"
KEY=os.getenv("DART_API_KEY")
STOCK="014950"
START=2010
END=datetime.now().year
REPORTS={"11011":"annual","11012":"half","11013":"q1","11014":"q3"}
REPORT_LABEL={"11011":"Annual","11012":"Half-year","11013":"Q1","11014":"Q3"}
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
DOCS=ROOT/"docs"

if not KEY:
    raise SystemExit("DART_API_KEY secret is required.")

def get_json(path, params):
    p=dict(params); p["crtfc_key"]=KEY
    for i in range(3):
        r=requests.get(f"{API}/{path}",params=p,timeout=60)
        r.raise_for_status()
        x=r.json()
        if x.get("status")=="000": return x
        if x.get("status")=="013": return {"status":"013","message":x.get("message",""),"list":[]}
        if x.get("status")=="020" and i<2:
            time.sleep(2+i); continue
        raise RuntimeError(f"{path}: {x.get('status')} {x.get('message')}")
    return {"list":[]}

def corp_code():
    z=requests.get(f"{API}/corpCode.xml",params={"crtfc_key":KEY},timeout=90)
    z.raise_for_status()
    import zipfile,io,xml.etree.ElementTree as ET
    with zipfile.ZipFile(io.BytesIO(z.content)) as zz:
        root=ET.fromstring(zz.read("CORPCODE.xml"))
    for e in root.findall("list"):
        if (e.findtext("stock_code") or "").strip()==STOCK:
            return (e.findtext("corp_code") or "").strip()
    raise RuntimeError("삼익제약 종목코드 014950의 corp_code를 찾지 못했습니다.")

def num(v):
    if v is None: return None
    s=str(v).strip().replace(",","").replace(" ","")
    if s in ("","-","–","—"): return None
    s=s.replace("(","-").replace(")","")
    try: return float(s)
    except: return None

def choose_fs(rows):
    # Prefer consolidated statements; otherwise separate statements.
    # Some filings may omit fs_div in individual rows; never discard all rows.
    c=[x for x in rows if str(x.get("fs_div","")).upper()=="CFS"]
    if c: return c
    o=[x for x in rows if str(x.get("fs_div","")).upper()=="OFS"]
    if o: return o
    return rows

def account_map(rows):
    m={}
    for r in choose_fs(rows):
        key=(r.get("account_id") or r.get("account_nm") or "").strip()
        name=(r.get("account_nm") or "").strip()
        if not key: continue
        if key not in m: m[key]=dict(r)
        # Keep the row with a useful amount.
        if num(r.get("thstrm_amount")) is not None or num(r.get("thstrm_add_amount")) is not None:
            m[key]=dict(r)
        m[key]["account_nm"]=name
    return m

def find(m, names):
    for row in m.values():
        n=(row.get("account_nm") or "").replace(" ","")
        for target in names:
            if target.replace(" ","") in n:
                return row
    return None

def value(m,names,field="thstrm_amount"):
    r=find(m,names)
    return num(r.get(field)) if r else None

def income_value(m,names):
    # For interim income statements, use accumulated amount for YTD.
    r=find(m,names)
    if not r: return None
    return num(r.get("thstrm_add_amount")) if num(r.get("thstrm_add_amount")) is not None else num(r.get("thstrm_amount"))

def build_record(year, code, rows):
    m=account_map(rows)
    label=REPORT_LABEL[code]
    sales=income_value(m,["매출액","수익(매출액)","영업수익"])
    cogs=income_value(m,["매출원가"])
    op=income_value(m,["영업이익","영업이익(손실)"])
    ni=income_value(m,["당기순이익","당기순이익(손실)","분기순이익"])
    tax=income_value(m,["법인세비용","법인세비용(수익)"])
    pbt=income_value(m,["법인세비용차감전순이익","법인세비용차감전순이익(손실)"])
    assets=value(m,["자산총계"])
    liab=value(m,["부채총계"])
    equity=value(m,["자본총계"])
    cash=value(m,["현금및현금성자산","현금 및 현금성자산"])
    ar=value(m,["매출채권"])
    inv=value(m,["재고자산"])
    ap=value(m,["매입채무"])
    cfo=income_value(m,["영업활동현금흐름","영업활동으로인한현금흐름"])
    capex=income_value(m,["유형자산의취득","유형자산 취득","유형자산의 취득"])
    if capex is not None: capex=abs(capex)
    interest=income_value(m,["이자비용","금융원가"])
    depreciation=income_value(m,["감가상각비"])
    amortization=income_value(m,["무형자산상각비","무형자산 상각비"])
    debt=sum(x or 0 for x in [value(m,["단기차입금"]),value(m,["장기차입금"]),value(m,["유동성장기부채"]),value(m,["사채"]),value(m,["전환사채"])])
    shares=income_value(m,["가중평균유통보통주식수","기본주당이익 계산에 사용된 가중평균유통보통주식수"])
    days={"Annual":365,"Half-year":181,"Q1":90,"Q3":273}.get(label,90)
    # API gives YTD for interim IS; q3 standalone is derived later from Q3 YTD - H1.
    out={
      "year":year,"report_code":code,"report":label,"currency":"KRW",
      "revenue":sales,"gross_profit":(sales-cogs if sales is not None and cogs is not None else None),
      "cost_of_sales":cogs,"operating_income":op,"net_income":ni,
      "assets":assets,"liabilities":liab,"equity":equity,"cash":cash,
      "accounts_receivable":ar,"inventory":inv,"accounts_payable":ap,
      "operating_cash_flow":cfo,"capex":capex,"interest_expense":interest,
      "interest_bearing_debt":debt or None,"depreciation":depreciation,"amortization":amortization,"shares":shares,
      "tax_expense":tax,"pretax_income":pbt,
      "source_filing":rows[0].get("rcept_no") if rows else None,
      "source_url":f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rows[0].get('rcept_no')}" if rows and rows[0].get("rcept_no") else None,
      "raw_account_count":len(m)
    }
    if sales:
        out["operating_margin"]=round((op or 0)/sales*100,2) if op is not None else None
        out["net_margin"]=round((ni or 0)/sales*100,2) if ni is not None else None
        out["gross_margin"]=round((out["gross_profit"] or 0)/sales*100,2) if out["gross_profit"] is not None else None
    if equity not in (None,0) and liab is not None: out["debt_to_equity"]=round(liab/equity*100,2)
    if assets not in (None,0) and liab is not None: out["liabilities_to_assets"]=round(liab/assets*100,2)
    if ni is not None and cfo is not None and ni!=0: out["cfo_to_net_income"]=round(cfo/ni,2)
    out["free_cash_flow"]=cfo-capex if cfo is not None and capex is not None else None
    if op is not None:
        ebitda=op+(depreciation or 0)+(amortization or 0)
        out["ebitda"]=ebitda
        if debt is not None and cash is not None and ebitda: out["net_debt_to_ebitda"]=round((debt-cash)/ebitda,2)
    out["net_debt"]=debt-cash if debt is not None and cash is not None else None
    if debt is not None and cash is not None and op is not None:
        out["net_debt_to_operating_income"]=round((debt-cash)/op,2) if op else None
    if op is not None and interest not in (None,0): out["interest_coverage"]=round(op/interest,2)
    if pbt and tax is not None:
        tr=max(0,min(1,tax/pbt))
        nopat=op*(1-tr) if op is not None else None
        invested=(equity or 0)+(debt or 0)-(cash or 0) if equity is not None else None
        out["effective_tax_rate"]=round(tr*100,2)
        out["roic"]=round(nopat/invested*100,2) if nopat is not None and invested else None
    # Point-in-time ROE/ROA; average-balance adjustment is applied by dashboard/next-period logic.
    if equity not in (None,0) and ni is not None: out["roe"]=round(ni/equity*100,2)
    if assets not in (None,0) and ni is not None: out["roa"]=round(ni/assets*100,2)
    if ar is not None and sales not in (None,0): out["dso"]=round(ar/sales*days,1)
    if inv is not None and cogs not in (None,0): out["dio"]=round(inv/cogs*days,1)
    if ap is not None and cogs not in (None,0): out["dpo"]=round(ap/cogs*days,1)
    if all(out.get(k) is not None for k in ("dso","dio","dpo")): out["ccc"]=round(out["dso"]+out["dio"]-out["dpo"],1)
    if shares not in (None,0) and ni is not None: out["eps"]=round(ni/shares,2)
    return out

def main():
    cc=corp_code()
    all_records=[]
    unavailable=[]
    raw_root=DATA/"raw"
    for year in range(START,END+1):
        if year<2015:
            unavailable.append({"year":year,"reason":"OpenDART 정기보고서 재무정보 API는 2015년 이후 제공"})
            continue
        for code,label in REPORTS.items():
            try:
                x=get_json("fnlttSinglAcntAll.json",{"corp_code":cc,"bsns_year":str(year),"reprt_code":code,"fs_div":"CFS"})
                rows=x.get("list",[])
                if not rows:
                    x=get_json("fnlttSinglAcntAll.json",{"corp_code":cc,"bsns_year":str(year),"reprt_code":code,"fs_div":"OFS"})
                    rows=x.get("list",[])
                if rows:
                    p=raw_root/str(year)
                    p.mkdir(parents=True,exist_ok=True)
                    (p/f"{label}.json").write_text(json.dumps({"year":year,"report_code":code,"corp_code":cc,"list":rows},ensure_ascii=False,indent=2),encoding="utf-8")
                    record=build_record(year,code,rows)
                    core=[record.get(k) for k in ("revenue","operating_income","net_income","assets","liabilities","equity")]
                    if any(v is not None for v in core):
                        all_records.append(record)
                    else:
                        unavailable.append({"year":year,"report":label,"reason":"DART 응답은 존재하지만 핵심 재무계정 정규화 실패"})
                else:
                    unavailable.append({"year":year,"report":label,"reason":"DART 응답 데이터 없음"})
            except Exception as e:
                unavailable.append({"year":year,"report":label,"reason":str(e)})
            time.sleep(0.15)

    # Derive standalone Q3 from YTD Q3 minus H1 for income/cash-flow items where possible.
    by={(r["year"],r["report"]):r for r in all_records}
    for r in list(all_records):
        if r["report"]!="Q3": continue
        h=by.get((r["year"],"Half-year"))
        if not h: continue
        for k in ["revenue","gross_profit","cost_of_sales","operating_income","net_income","operating_cash_flow","capex","interest_expense","tax_expense","pretax_income"]:
            if r.get(k) is not None and h.get(k) is not None:
                r[f"{k}_ytd"]=r[k]
                r[k]=r[k]-h[k]
        if r.get("revenue"):
            r["operating_margin"]=round(r.get("operating_income",0)/r["revenue"]*100,2)
            r["net_margin"]=round(r.get("net_income",0)/r["revenue"]*100,2)
        r["period_note"]="Q3 standalone derived as Q3 YTD minus H1 YTD for flow items"
    # Growth based on same report category.
    for r in all_records:
        prev=by.get((r["year"]-1,r["report"]))
        if prev:
            for base,key in [("revenue","revenue_growth"),("operating_income","operating_income_growth"),("net_income","net_income_growth")]:
                a,b=r.get(base),prev.get(base)
                r[key]=round((a-b)/abs(b)*100,2) if a is not None and b not in (None,0) else None

    if not all_records:
        raise RuntimeError("No usable financial records were collected. Check DART_API_KEY and account mapping.")
    all_records.sort(key=lambda x:(x["year"],["Annual","Half-year","Q1","Q3"].index(x["report"])))
    for r in all_records:
        r["year_period"]=f'{r["year"]} {r["report"]}'
    out={
      "company":{"name":"삼익제약","stock_code":STOCK,"corp_code":cc},
      "updated_at":datetime.now().astimezone().isoformat(),
      "api_coverage":{"requested_start":START,"api_financial_start":2015,"latest_year":END},
      "records":all_records,
      "unavailable":unavailable,
      "peers":[
        {"name":"삼익제약","stock_code":"014950","note":"기준기업"},
        {"name":"동구바이오제약","stock_code":"006620","note":"피부과·비뇨기과 중심 전문의약품"},
        {"name":"신일제약","stock_code":"012790","note":"의약품 제조·판매"},
        {"name":"진양제약","stock_code":"007370","note":"제네릭·의약품 위탁생산(CMO), 순환기·소화기·당뇨 관련 의약품"}
      ]
    }
    DATA.mkdir(exist_ok=True)
    DOCS.mkdir(exist_ok=True)
    (DATA/"financial_data.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    (DOCS/"data.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Saved {len(all_records)} records; unavailable={len(unavailable)}")

if __name__=="__main__": main()
