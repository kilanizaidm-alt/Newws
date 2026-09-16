/* Independent publisher headlines and a permanent teaching glossary. */
(() => {
  const main = document.getElementById('main');
  const news = el('section'); news.id = 'publisher-news';
  news.append(el('h2','أخبار من المصادر / Publisher reports'));
  news.append(arabic(el('p','الأخبار الإنجليزية والعربية قائمتان مستقلتان؛ ليست الأخبار المتجاورة ترجمات لبعضها. تاريخ النشر من موجز الناشر، وقد يختلف عن تاريخ الحدث.','muted')));
  const status = arabic(el('p','جارٍ تحميل روابط الأخبار…','notice'));
  const columns = el('div',undefined,'parallel'); news.append(status,columns);
  main.prepend(news);
  const nav = document.querySelector('nav');
  const newsAnchor = el('a','أخبار المصادر'); newsAnchor.href='#publisher-news';nav.prepend(newsAnchor);
  const bank = el('section'); bank.id='reference-glossary';bank.append(el('h2','Detailed glossary / القاموس الصحفي المفصّل'));
  const bankNote=arabic(el('p','جارٍ تحميل القاموس…','muted'));bank.append(bankNote);
  const label=el('label','ابحث بالإنجليزية أو العربية / Search '), input=el('input');input.type='search';input.placeholder='inflation / تضخم';label.append(input);bank.append(label);
  const cards=el('div',undefined,'terms');bank.append(cards);
  document.getElementById('glossary').after(bank);
  const glossaryAnchor=el('a','القاموس المفصّل');glossaryAnchor.href='#reference-glossary';nav.append(glossaryAnchor);
  function detailCard(t){
    const card=el('article',undefined,'term');
    card.append(el('h3',t.english),el('p',t.part_of_speech||'','muted'),arabic(el('p',t.arabic,'equivalent')));
    if(t.meaning_ar)card.append(arabic(el('p',t.meaning_ar)));
    card.append(el('p',t.example_en,'example'),arabic(el('p',t.example_ar,'translation')));
    if(t.collocations){card.append(el('strong','Collocations / تراكيب شائعة'));card.append(el('p',t.collocations));}
    if(t.translation_note_ar)card.append(arabic(el('p',t.translation_note_ar,'note')));
    return card;
  }
  // Extend each dated lesson's glossary without mixing it with the fixed bank.
  const baseTerms=renderTerms;
  renderTerms=function(){baseTerms();const q=normalize($('search').value.trim());
    const selected=lesson.glossary.filter(t=>normalize(`${t.english} ${t.arabic} ${t.example_en} ${t.example_ar}`).includes(q));
    if(selected.length)$('terms').replaceChildren(...selected.map(detailCard));};
  const baseRender=render;
  render=function(data){baseRender(data);
    for(const id of ['stories','glossary','practice'])$(id).hidden=!!data.demo;
    if(data.demo){$('edition').textContent='Publisher reports & permanent glossary';
      $('notice').textContent='لم يتوافر درس إخباري مترجم بعد. أخبار المصادر والقاموس التدريبي متاحان. لن نعرض الأمثلة الخيالية كأخبار.';}
    else {$('glossary-title').textContent='قاموس هذا الدرس / This edition’s glossary';}
  };
  if(typeof lesson!=='undefined' && lesson)render(lesson);
  else for(const id of ['stories','glossary','practice'])$(id).hidden=true;
  const method=document.querySelector('.method');
  if(method)method.replaceChildren(el('summary','عن المصادر والترجمة / About sources'),arabic(el('p','روابط الناشرين تُحدّث بصورة مستقلة عن الترجمة. القاموس الثابت يتضمن أمثلة تدريبية مبتكرة، لا أخبارًا. عند توفر درس، تظهر معه تواريخه ومصادره وقاموسه. الترجمات تعليمية يراجعها الذكاء الاصطناعي؛ وليست معتمدة أو مراجَعة بشريًا. التغطية العربية الموازية ليست بالضرورة ترجمة للخبر الإنجليزي.')));
  fetch('data/reports.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(data=>{
    const age=Date.now()-Date.parse(data.fetched_at);
    status.textContent=`آخر جلب ناجح: ${new Date(data.fetched_at).toLocaleString('ar',{timeZone:'UTC'})} UTC. نافذة الجمع: 72 ساعة، مع تمييز آخر 24 ساعة. ${age>24*3600000?'هذه آخر نسخة محفوظة؛ لم يتم تأكيد تحديثها اليوم.':''} ${data.failed_feeds.length?'تعذّر جلب بعض المصادر.':''}`;
    for(const lang of ['en','ar']){
      const col=el('div',undefined,'reading');col.lang=lang;if(lang==='ar')col.dir='rtl';col.append(el('h3',lang==='en'?'English reporting':'تغطية عربية مستقلة'));
      const rows=data.reports.filter(r=>r.language===lang);
      if(!rows.length)col.append(el('p',lang==='en'?'No reports available.':'لا توجد تقارير متاحة.'));
      for(const r of rows){const a=el('article',undefined,'story');a.append(link(r.title,r.url));
        const hours=(Date.now()-Date.parse(r.published_at))/3600000;
        a.append(el('p',`${r.publisher} · ${displayDate(r.published_at)} · ${hours<=24?'آخر 24 ساعة':hours<=72?'أقدم من 24 ساعة':'نسخة قديمة محفوظة'}`,'muted'));col.append(a);}
      columns.append(col);
    }
  }).catch(()=>{status.textContent='تعذّر تحميل أخبار المصادر. لا نعرض أخبارًا قديمة بوصفها أخبار اليوم. القاموس أدناه مستقل ومتاح.';});
  fetch('data/glossary-bank.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(data=>{
    bankNote.textContent=`${data.note} تاريخ إعداد النسخة: ${data.reviewed_at}.`;
    const show=()=>{const q=normalize(input.value.trim());const rows=data.entries.filter(t=>normalize(Object.values(t).join(' ')).includes(q));cards.replaceChildren(...rows.map(detailCard));if(!rows.length)cards.append(el('p','لا توجد نتائج / No matches'));};
    input.addEventListener('input',show);show();
  }).catch(()=>{bankNote.textContent='تعذّر تحميل القاموس، حاول تحديث الصفحة.';});
})();
