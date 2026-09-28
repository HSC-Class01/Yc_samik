import os
import sys
import json
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
import io

DART_API_KEY = os.environ.get("DART_API_KEY")

if not DART_API_KEY:
    print("Error: DART_API_KEY environment variable is missing.")
    sys.exit(1)

# 삼익제약 종목코드: 014950
STOCK_CODE = "014950"
START_YEAR = 2010
END_YEAR = 2026

def get_corp_code(api_key, stock_code):
    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={api_key}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        zip_file = zipfile.ZipFile(io.BytesIO(response.read()))
        xml_data = zip_file.read("CORPCODE.xml")
        
    tree = ET.fromstring(xml_data)
    for list_tag in tree.findall("list"):
        code = list_tag.findtext("stock_code")
        if code and code.strip() == stock_code:
            return list_tag.findtext("corp_code").strip()
    return None

def fetch_financial_single(api_key, corp_code, bsn_year, reprt_code):
    url = f"https://opendart.fss.or.kr/api/fnlttSinglAcnt.json?crtfc_key={api_key}&corp_code={corp_code}&bsns_year={bsn_year}&reprt_code={reprt_code}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('status') == '000':
                return data.get('list', [])
    except Exception as e:
        print(f"Failed fetching {bsn_year} - {reprt_code}: {e}")
    return []

def main():
    print("Fetching Corp Code...")
    corp_code = get_corp_code(DART_API_KEY, STOCK_CODE)
    if not corp_code:
        print(f"Corp code for stock code {STOCK_CODE} not found.")
        sys.exit(1)

    reports = {
        "11011": "annual",    # 사업보고서
        "11012": "half",      # 반기보고서
        "11013": "quarter1",  # 1분기보고서
        "11014": "quarter3"   # 3분기보고서
    }

    results = {"annual": [], "half": [], "quarterly": []}

    for year in range(START_YEAR, END_YEAR + 1):
        for code, category in reports.items():
            print(f"Fetching data for Year: {year}, Code: {code}...")
            items = fetch_financial_single(DART_API_KEY, corp_code, str(year), code)
            
            if items:
                record = {"year": year, "report_code": code}
                for item in items:
                    account_nm = item.get("account_nm", "").strip()
                    amount = item.get("thstrm_amount", "0").replace(",", "")
                    try:
                        record[account_nm] = float(amount)
                    except ValueError:
                        record[account_nm] = 0.0
                
                sales = record.get("매출액", 0) or record.get("수익(매출액)", 0)
                op_income = record.get("영업이익", 0) or record.get("영업이익(손실)", 0)
                net_income = record.get("당기순이익", 0) or record.get("당기순이익(손실)", 0)
                assets = record.get("자산총계", 0)
                liabilities = record.get("부채총계", 0)
                equity = record.get("자본총계", 0)

                record["매출액"] = sales
                record["영업이익"] = op_income
                record["당기순이익"] = net_income
                record["영업이익률"] = round((op_income / sales * 100), 2) if sales else 0.0
                record["순이익률"] = round((net_income / sales * 100), 2) if sales else 0.0
                record["부채비율"] = round((liabilities / equity * 100), 2) if equity else 0.0

                if category == "annual":
                    results["annual"].append(record)
                elif category == "half":
                    results["half"].append(record)
                else:
                    results["quarterly"].append(record)

    os.makedirs("docs", exist_ok=True)
    with open("docs/data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("Data successfully saved to docs/data.json")

if __name__ == "__main__":
    main()
