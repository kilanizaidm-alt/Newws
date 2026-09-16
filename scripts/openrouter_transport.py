"""Pinned free model with safe, useful diagnostics and bounded transport."""
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from functools import lru_cache

MODEL='nex-agi/nex-n2.5-mini:free'
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

@lru_cache(maxsize=1)
def verify_free_model():
    req=urllib.request.Request('https://openrouter.ai/api/v1/models',headers={'Accept':'application/json'})
    with urllib.request.build_opener(NoRedirect()).open(req,timeout=20) as response:
        raw=response.read(5000001)
    if len(raw)>5000000:raise ValueError('catalog_too_large')
    model=next((m for m in json.loads(raw)['data'] if m['id']==MODEL),None)
    if not model:raise ValueError('pinned_model_unavailable')
    pricing=model.get('pricing',{})
    if pricing.get('prompt') is None or pricing.get('completion') is None or any(float(v)!=0 for v in pricing.values() if isinstance(v,(str,int,float))):
        raise ValueError('free_pricing_not_confirmed')
    reasoning=model.get('reasoning',{})
    if reasoning.get('mandatory') or 'none' not in reasoning.get('supported_efforts',[]):
        raise ValueError('reasoning_off_not_supported')
    return True


def worker():
    # stdin/stdout are private parent-child pipes, never workflow logs.
    body=json.load(sys.stdin)
    payload={'model':MODEL,'messages':body['messages'],'max_tokens':6000,
             'reasoning':{'effort':'none'},'response_format':{'type':'json_object'}}
    request=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
        data=json.dumps(payload,ensure_ascii=False).encode(),method='POST',
        headers={'Content-Type':'application/json','Authorization':'Bearer '+body['key']})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request,timeout=90) as response:
            raw=response.read(2000001)
        if len(raw)>2000000:raise ValueError()
        result=json.loads(raw)
        if result.get('error'):
            code=result['error'].get('code')
            print(json.dumps({'failure':'provider_error','http':code if isinstance(code,int) else None}));return
        choice=result['choices'][0]
        usage=result.get('usage',{})
        print(json.dumps({'finish':choice.get('finish_reason'),
            'content':choice.get('message',{}).get('content'),
            'completion_tokens':usage.get('completion_tokens'),
            'reasoning_tokens':usage.get('completion_tokens_details',{}).get('reasoning_tokens')},ensure_ascii=False))
    except urllib.error.HTTPError as error:
        print(json.dumps({'failure':'http_error','http':error.code}))
    except Exception:
        print(json.dumps({'failure':'transport_error'}))


def generate(key,prompt,system):
    verify_free_model()
    try:
        proc=subprocess.run([sys.executable,__file__,'worker'],input=json.dumps({'key':key,
            'messages':[{'role':'system','content':system},{'role':'user','content':prompt}]}),
            text=True,capture_output=True,timeout=180,check=True)
    except subprocess.TimeoutExpired:
        raise ValueError('request_wall_timeout') from None
    except subprocess.SubprocessError:
        raise ValueError('request_process_failed') from None
    result=json.loads(proc.stdout)
    reason=result.get('finish')
    safe=reason if reason in ('stop','length','content_filter','error','tool_calls') else 'unknown'
    counts={k:v for k,v in result.items() if k in ('completion_tokens','reasoning_tokens','http') and isinstance(v,int)}
    print('Model='+MODEL+' finish='+safe+' '+json.dumps(counts),flush=True)
    if result.get('failure'):raise ValueError('provider_request_failed')
    if reason!='stop':raise ValueError('completion_'+safe)
    text=result.get('content')
    if not isinstance(text,str) or key in text:raise ValueError('invalid_content')
    text=re.sub(r'^```(?:json)?\s*|\s*```$','',text.strip())
    return json.loads(text)

if __name__=='__main__': worker()
