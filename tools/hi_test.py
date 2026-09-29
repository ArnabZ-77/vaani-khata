import asyncio, sys, os, edge_tts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))
from asr import Whisper, load_wav
from ledger import Khata
S = [("रमेश ने पाँच सौ रुपये उधार लिए।", "hi-IN-SwaraNeural"),
     ("सुनीता ने दो सौ रुपये वापस दिए।", "hi-IN-MadhurNeural"),
     ("मोहन को दो किलो चीनी नब्बे रुपये में बेची।", "hi-IN-SwaraNeural"),
     ("रमेश का कितना बाकी है?", "hi-IN-MadhurNeural"),
     ("Ramesh ne teen sau rupaye udhaar liye", "hi-IN-SwaraNeural"),
     ("Sunita ko do sau rupaye udhaar diye aur Mohan ne sau rupaye wapas diye", "hi-IN-MadhurNeural")]
async def gen(i, t, v):
    p = f"tools/hi_{i}.mp3"; await edge_tts.Communicate(t, v).save(p); return p
w = Whisper(); k = Khata()
for i, (t, v) in enumerate(S):
    p = asyncio.run(gen(i, t, v))
    text, lang, st = w.transcribe(load_wav(p), "hi")
    e, a = k.apply(text)
    print(f"\nSAID : {t}\nHEARD: {text}  [{lang}, {st['total_ms']:.0f} ms]\nENTRY: {[(x['kind'],x['person'],x['amount'],x['qty'],x['item']) for x in e]} {a}")
print("\nBALANCES", k.balances())
