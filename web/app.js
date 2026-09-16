"use strict";
const $ = id => document.getElementById(id);
let lesson, loadNumber = 0;
function el(tag, text, cls) { const n = document.createElement(tag); if(text !== undefined)n.textContent=text; if(cls)n.className=cls; return n; }
function arabic(node){node.lang="ar";node.dir="rtl";return node;}
function link(label, url){const n=el("a",label);try{const u=new URL(url);if(u.protocol!=="https:")return el("span",label);n.href=u.href;n.target="_blank";n.rel="noopener noreferrer";return n;}catch{return el("span",label);}}
function displayDate(value){if(!value)return "Undated";const d=new Date(value);return Number.isNaN(d.valueOf())?"Undated":d.toLocaleDateString("en-GB",{year:"numeric",month:"short",day:"numeric",timeZone:"UTC"});}
function render(data){
 lesson=data; $("attempt").value=""; $("search").value="";
 $("edition").textContent=data.demo?"Preview edition · Fictional practice material":`${displayDate(data.generated_at)} · ${data.stories.length} stories · English → العربية`;
 $("notice").textContent=data.demo?"Preview lesson — these examples are fictional, not today's news. Live editions will appear after the daily updater is activated.":`${data.coverage_note} Published ${displayDate(data.generated_at)}. ${Date.now()-Date.parse(data.generated_at)>48*3600000?"This is the last available edition; it is more than 48 hours old.":""}`;
 $("story-list").replaceChildren();
 data.stories.forEach((s,i)=>{
  const article=el("article",undefined,"story"), top=el("div",undefined,"story-top");top.append(el("strong",`${String(i+1).padStart(2,"0")} / ${s.topic}`),el("span",data.demo?"Fictional example":displayDate(s.published_at)));article.append(top);
  const pair=el("div",undefined,"parallel");
  for(const lang of ["en","ar"]){const reading=el("div",undefined,"reading");reading.lang=lang;if(lang==="ar")reading.dir="rtl";reading.append(el("span",lang==="en"?"ENGLISH / LEARNING SUMMARY":"العربية / ترجمة تعليمية مراجَعة","language"),el("h3",s[`headline_${lang}`]),el("p",s[`summary_${lang}`]));pair.append(reading);}article.append(pair);
  const sources=el("div",undefined,"sources");for(const source of s.sources||[])sources.append(link(`${source.language==="ar"?"Arabic reference":"English source"} · ${source.publisher}`,source.url));article.append(sources);
  article.append(el("p",s.reference_note,"verification"));const note=el("div",undefined,"note");note.append(el("strong","Translation desk · "),document.createTextNode(s.translation_note));article.append(note);$("story-list").append(article);
 });
 renderTerms(); $("exercise-en").textContent=data.exercise.english;$("exercise-ar").textContent=data.exercise.arabic;$("tips").replaceChildren(...data.exercise.tips.map(t=>el("li",t)));document.querySelector(".exercise details").open=false;
}
function normalize(t){return t.toLowerCase().normalize("NFKD").replace(/[\u064b-\u065f\u0670\u0640]/g,"").replace(/[أإآ]/g,"ا");}
function renderTerms(){const q=normalize($("search").value.trim());const rows=lesson.glossary.filter(t=>normalize(`${t.english} ${t.arabic} ${t.example_en} ${t.example_ar}`).includes(q));$("term-count").textContent=`${rows.length} of ${lesson.glossary.length} expressions`;$("terms").replaceChildren();for(const t of rows){const card=el("article",undefined,"term");card.append(el("h3",t.english),arabic(el("p",t.arabic,"equivalent")),el("p",t.example_en,"example"),arabic(el("p",t.example_ar,"translation")));$("terms").append(card);}if(!rows.length)$("terms").append(el("p","No matching expressions. Try another English or Arabic word.","muted"));}
async function load(path){const request=++loadNumber;try{if(!/^data\/(latest|editions\/\d{4}-\d{2}-\d{2})\.json$/.test(path))throw Error("Invalid edition");const r=await fetch(path,{cache:"no-cache"});if(!r.ok)throw Error("Could not load");const data=await r.json();if(request===loadNumber)render(data);}catch{if(request===loadNumber)$("notice").textContent="This edition could not be loaded. Please try again later. Your last displayed lesson has been kept.";}}
$("search").addEventListener("input",()=>{if(lesson)renderTerms();});$("editions").addEventListener("change",e=>load(e.target.value));
load("data/latest.json");
fetch("data/editions.json",{cache:"no-cache"}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(rows=>{const latest=el("option","Latest edition");latest.value="data/latest.json";$("editions").replaceChildren(latest);for(const r of rows){if(!/^\d{4}-\d{2}-\d{2}$/.test(r.date))continue;const o=el("option",displayDate(r.date));o.value=`data/editions/${r.date}.json`;$("editions").append(o);}}).catch(()=>{});
