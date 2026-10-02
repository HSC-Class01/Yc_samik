const $=id=>document.getElementById(id);
const fmt=(v,d=0)=>v==null||Number.isNaN(Number(v))?"—":Number(v).toLocaleString("ko-KR",{maximumFractionDigits:d});
const pct=v=>v==null?"—":fmt(v,2)+"%";
const latest=(rows,report)=>rows.filter(r=>r.report===report).sort((a,b)=>a.year-b.year).at(-1);
let charts=[];
fetch("data.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw Error("data.json load failed");return r.json()}).then(data=>{
 const rows=data.records||[], annual=rows.filter(r=>r.report==="Annual"), half=rows.filter(r=>r.report==="Half-year"), q=rows.filter(r=>r.report==="Q1"||r.report==="Q3");
 const a=annual.at(-1)||rows.at(-1), prev=annual.length>1?annual.at(-2):null;
 $("coverage").textContent=`재무 API: ${data.api_coverage?.api_financial_start}~${data.api_coverage?.latest_year}`;
 $("updated").textContent="업데이트: "+(data.updated_at?new Date(data.updated_at).toLocaleString("ko-KR"):"—");
 const k=[["최근 매출액",fmt(a?.revenue),"원"],["영업이익률",pct(a?.operating_margin),"최근 Annual"],["ROE",pct(a?.roe),"최근 Annual"],["영업현금흐름",fmt(a?.operating_cash_flow),"원"]];
 $("kpis").innerHTML=k.map(x=>`<div class="card kpi"><div class="label">${x[0]}</div><div class="value">${x[1]}</div><div class="sub">${x[2]}</div></div>`).join("");
 renderCharts(annual); renderTable("annual",annual); renderTable("half",half); renderTable("quarterly",q); renderPeers(data.peers||[]);
}).catch(e=>{document.querySelector("main").insertAdjacentHTML("beforeend",`<div class="card" style="margin-top:20px">데이터를 불러오지 못했습니다: ${e.message}</div>`)});
function renderCharts(rows){
 const labels=rows.map(r=>r.year), revenue=rows.map(r=>r.revenue), op=rows.map(r=>r.operating_income), ni=rows.map(r=>r.net_income);
 charts.push(new Chart($("trend"),{type:"line",data:{labels,datasets:[{label:"매출액",data:revenue,tension:.25},{label:"영업이익",data:op,tension:.25},{label:"순이익",data:ni,tension:.25}]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:"index",intersect:false},plugins:{legend:{position:"bottom"}},scales:{y:{ticks:{callback:v=>fmt(v)}}}}}));
 charts.push(new Chart($("margin"),{type:"line",data:{labels,datasets:[{label:"영업이익률",data:rows.map(r=>r.operating_margin),tension:.25},{label:"순이익률",data:rows.map(r=>r.net_margin),tension:.25}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom"}},scales:{y:{ticks:{callback:v=>v+"%"}}}}}));
 charts.push(new Chart($("cash"),{type:"bar",data:{labels,datasets:[{label:"영업현금흐름",data:rows.map(r=>r.operating_cash_flow)},{label:"FCF",data:rows.map(r=>r.free_cash_flow)}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom"}}}}));
 charts.push(new Chart($("risk"),{type:"line",data:{labels,datasets:[{label:"부채비율",data:rows.map(r=>r.debt_to_equity),tension:.25},{label:"ROA",data:rows.map(r=>r.roa),tension:.25},{label:"ROE",data:rows.map(r=>r.roe),tension:.25}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom"}},scales:{y:{ticks:{callback:v=>v+"%"}}}}}));
}
const cols=[
 ["year_period","기간"],["revenue","매출액"],["gross_profit","매출총이익"],["operating_income","영업이익"],["net_income","당기순이익"],
 ["operating_margin","영업이익률"],["net_margin","순이익률"],["operating_cash_flow","CFO"],["free_cash_flow","FCF"],["net_debt","순차입금"],["ebitda","EBITDA"],["net_debt_to_ebitda","순차입금/EBITDA"],
 ["debt_to_equity","부채비율"],["interest_coverage","이자보상배율"],["roic","ROIC"],["roe","ROE"],["roa","ROA"],["ccc","CCC"],["eps","EPS"]
];
function renderTable(id,rows){
 let h="<thead><tr>"+cols.map(c=>`<th>${c[1]}</th>`).join("")+"</tr></thead><tbody>";
 for(const r of rows.slice().reverse()) h+="<tr>"+cols.map(([k])=>`<td>${k.includes("margin")||["debt_to_equity","roic","roe","roa"].includes(k)?pct(r[k]):k==="interest_coverage"||k==="net_debt_to_ebitda"?fmt(r[k],2):k==="ccc"?fmt(r[k],1):k==="eps"?fmt(r[k],2):fmt(r[k])}</td>`).join("")+"</tr>";
 $(id).innerHTML=h+"</tbody>";
}
function renderPeers(rows){
 $("peers").innerHTML="<thead><tr><th>기업명</th><th>종목코드</th><th>비교 목적</th></tr></thead><tbody>"+rows.map(r=>`<tr><td>${r.name}</td><td>${r.stock_code}</td><td>${r.note}</td></tr>`).join("")+"</tbody>";
}