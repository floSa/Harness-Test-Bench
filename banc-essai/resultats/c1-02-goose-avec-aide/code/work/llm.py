import os, json, urllib.request, urllib.error, time

URL = os.environ['BANC_MODELE_URL'].rstrip('/') + '/v1/chat/completions'
MODEL = os.environ['BANC_MODELE']
KEY = os.environ['BANC_CLE_MODELE']

def chat(messages, max_tokens=16000, json_mode=True, temperature=0):
    body = {"model": MODEL, "messages": messages, "max_tokens": max_tokens,
            "temperature": temperature}
    if json_mode: body["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(URL, data=json.dumps(body, ensure_ascii=False).encode(),
        headers={"Content-Type":"application/json","Authorization":"Bearer "+KEY})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.load(r)
            m = d['choices'][0]['message']
            if m.get('content'):
                return m.get('content')
            print('EMPTY content finish=', d['choices'][0].get('finish_reason'), flush=True)
            time.sleep(2)
        except urllib.error.HTTPError as e:
            print('HTTP', e.code, e.read()[:300], flush=True); time.sleep(2*(attempt+1))
        except Exception as e:
            print('ERR', e, flush=True); time.sleep(2*(attempt+1))
    return None
