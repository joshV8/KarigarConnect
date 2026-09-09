"""
Full AI Pipeline Test — using a real online image.
Tests Gates 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 against the live AI service.
"""
import argparse
import atexit
import json
import os
import subprocess
import sys
import time
import requests

PIPELINE_SCRIPT = r'''
parser = argparse.ArgumentParser(description="Run the Full AI Pipeline Integration Test.")
parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of the AI service")
parser.add_argument("--image", default="test_pottery_online.jpg", help="Path to test image")
parser.add_argument("--start-server", action="store_true", help="Automatically start uvicorn if not running")
args = parser.parse_args()

BASE = args.base_url.rstrip("/")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Resolve image path relative to script directory if needed
IMG = args.image
if not os.path.exists(IMG):
    alt = os.path.join(SCRIPT_DIR, IMG)
    if os.path.exists(alt):
        IMG = alt

server_proc = None

def check_server_online(url: str, timeout: float = 2.0) -> bool:
    try:
        r = requests.get(f"{url}/health", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False

# Ensure server is running
if not check_server_online(BASE):
    if args.start_server:
        print(f"Starting server in background for integration test (uvicorn app.main:app on 127.0.0.1:8000)...")
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=SCRIPT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        atexit.register(lambda: server_proc.terminate() if server_proc else None)
        # Wait for server to become healthy
        started = False
        for _ in range(30):
            time.sleep(0.5)
            if check_server_online(BASE, timeout=1.0):
                started = True
                break
        if not started:
            print(f"[ERROR] Server failed to start within 15 seconds.")
            if server_proc:
                server_proc.terminate()
            sys.exit(1)
        print("Server is healthy and ready!\n")
    else:
        print("\n" + "=" * 60)
        print("[ERROR] Cannot connect to the AI Service at " + BASE)
        print("=" * 60)
        print("The backend server is not currently running.")
        print("\nTo run this test:")
        print("  Option 1: Start the server manually in another terminal:")
        print("      uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print(f"      python {os.path.basename(__file__)}")
        print("\n  Option 2: Use --start-server to launch it automatically:")
        print(f"      python {os.path.basename(__file__)} --start-server")
        print("=" * 60 + "\n")
        sys.exit(1)

SEP = "=" * 60

def pretty(label, val):
    print(f"  {label:<14}: {val}")

print(SEP)
print("FULL AI PIPELINE TEST — Online Image")
print(SEP)
print(f"Image: {IMG}  ({os.path.getsize(IMG):,} bytes)")
print()

# ── Gate 1: Health ────────────────────────────────────────────
print("[Gate 1] Health check...")
r = requests.get(BASE + "/health")
pretty("Status", r.status_code)
pretty("Body", r.json())
print()

# ── Gate 2: Image Validation ──────────────────────────────────
print("[Gate 2] Image validation...")
with open(IMG, "rb") as f:
    r = requests.post(BASE + "/image/validate", files={"image": (IMG, f, "image/jpeg")})
pretty("Status", r.status_code)
try:
    body = r.json()
    print(f"  Body: {json.dumps(body, indent=4, ensure_ascii=False)}")
except Exception:
    print(f"  Raw: {r.text[:200]}")
print()

# ── Gate 3: Background Removal ────────────────────────────────
print("[Gate 3] Background removal...")
with open(IMG, "rb") as f:
    r = requests.post(BASE + "/image/remove-background", files={"image": (IMG, f, "image/jpeg")})
ct = r.headers.get("content-type", "")
pretty("Status", r.status_code)
pretty("Size", f"{len(r.content):,} bytes")
pretty("Content-Type", ct)
if r.status_code == 200:
    with open("result_no_bg.png", "wb") as out:
        out.write(r.content)
    pretty("Saved", "result_no_bg.png")
else:
    print(f"  Error: {r.text[:200]}")
print()

# ── Gate 4: Image Enhancement ─────────────────────────────────
print("[Gate 4] Image enhancement...")
with open(IMG, "rb") as f:
    r = requests.post(BASE + "/image/enhance", files={"image": (IMG, f, "image/jpeg")})
pretty("Status", r.status_code)
pretty("Size", f"{len(r.content):,} bytes")
if r.status_code == 200:
    with open("result_enhanced.jpg", "wb") as out:
        out.write(r.content)
    pretty("Saved", "result_enhanced.jpg")
print()

# ── Gate 5: Product Vision ────────────────────────────────────
print("[Gate 5] Product vision / attribute extraction...")
with open(IMG, "rb") as f:
    r = requests.post(BASE + "/vision/analyze", files={"image": (IMG, f, "image/jpeg")})
pretty("Status", r.status_code)
vision = {}
try:
    vision = r.json()
    for key in ["product_name", "category", "material", "color", "craft_type", "style", "confidence"]:
        pretty(key.replace("_", " ").title(), vision.get(key))
    feats = vision.get("visible_features")
    if feats:
        pretty("Features", feats)
except Exception:
    print(f"  Raw: {r.text[:300]}")
print()

# ── Gate 6: Speech-to-Text ────────────────────────────────────
print("[Gate 6] Speech-to-Text (Whisper AI)...")
voice_file = os.path.join(SCRIPT_DIR, "real_speech.wav")
transcribed_text = None
if os.path.exists(voice_file):
    with open(voice_file, "rb") as f:
        r = requests.post(BASE + "/speech/transcribe", files={"audio": ("real_speech.wav", f, "audio/wav")})
    pretty("Status", r.status_code)
    try:
        sp = r.json()
        transcribed_text = sp.get("text")
        pretty("Transcribed", transcribed_text)
        pretty("Language", sp.get("language"))
        pretty("Confidence", sp.get("confidence"))
    except Exception:
        print(f"  Raw: {r.text[:300]}")
else:
    print("  [SKIP] real_speech.wav not found")
print()

# ── Gate 7: Translation ───────────────────────────────────────
print("[Gate 7] Translation (Marathi -> English + Hindi)...")
marathi_text = "ही बांबूपासून बनवलेली हाताने विणलेली टोपली आहे."
r = requests.post(BASE + "/ai/translate", json={"text": marathi_text, "source_language": "mr"})
pretty("Status", r.status_code)
try:
    t = r.json()
    pretty("Original", t.get("original"))
    pretty("English", t.get("translations", {}).get("en"))
    pretty("Hindi", t.get("translations", {}).get("hi", "")[:80])
except Exception:
    print(f"  Raw: {r.text[:300]}")
print()

# ── Gate 8: AI Description ────────────────────────────────────
print("[Gate 8] AI product description...")
pname = vision.get("product_name") or "Handcrafted Product"
pcat  = vision.get("category") or "Handicrafts"
pmat  = vision.get("material") or "Natural Material"
desc_payload = {
    "product_name": pname,
    "category": pcat,
    "material": pmat,
    "artisan_notes": "Beautifully handcrafted by local artisan",
    "language": "en"
}
r = requests.post(BASE + "/ai/describe", json=desc_payload)
pretty("Status", r.status_code)
desc_en = {}
try:
    desc_en = r.json()
    pretty("Title", desc_en.get("title"))
    desc_text = desc_en.get("description", "")
    pretty("Description", desc_text[:120] + ("..." if len(desc_text) > 120 else ""))
except Exception:
    print(f"  Raw: {r.text[:300]}")
print()

# ── Gate 9: SEO Metadata ──────────────────────────────────────
print("[Gate 9] SEO metadata...")
seo_payload = {
    "title": desc_en.get("title") or pname,
    "description": desc_en.get("description") or "Handcrafted artisan product",
    "category": pcat,
    "attributes": {"material": pmat, "craft_type": vision.get("craft_type", "")}
}
r = requests.post(BASE + "/ai/seo", json=seo_payload)
pretty("Status", r.status_code)
try:
    seo = r.json()
    pretty("SEO Title", seo.get("seo_title"))
    pretty("Keywords", seo.get("keywords"))
except Exception:
    print(f"  Raw: {r.text[:300]}")
print()

# ── Gate 10: Pricing ──────────────────────────────────────────
print("[Gate 10] Price recommendation...")
price_payload = {
    "raw_material_cost": 200.0,
    "labour_cost": 300.0,
    "packaging_cost": 60.0,
    "other_cost": 40.0,
    "category": pcat,
    "material": pmat,
    "quality": "standard",
    "demand": "medium"
}
r = requests.post(BASE + "/ai/price", json=price_payload)
pretty("Status", r.status_code)
try:
    p = r.json()
    pretty("Recommended", f"INR {p.get('recommended')}")
    pretty("Min-Max", f"INR {p.get('minimum')} – {p.get('maximum')}")
    expl = p.get("explanation", "")
    pretty("Explanation", expl[:120] + ("..." if len(expl) > 120 else ""))
except Exception:
    print(f"  Raw: {r.text[:300]}")
print()

# ── Gate 11: Full Catalog ─────────────────────────────────────
print("[Gate 11] Full catalog generation (entire pipeline)...")
t0 = time.time()
with open(IMG, "rb") as f:
    r = requests.post(
        BASE + "/ai/generate-catalog",
        files={"image": (IMG, f, "image/jpeg")},
        data={
            "raw_material_cost": "200",
            "labour_cost": "300",
            "packaging_cost": "60",
            "other_cost": "40",
            "artisan_notes": "Beautiful handcrafted artisan product",
            "skip_bg_removal": "false"
        }
    )
elapsed = time.time() - t0
pretty("Status", f"{r.status_code}  ({elapsed:.1f}s)")
try:
    cat = r.json()
    prod = cat.get("product", {})
    desc = cat.get("description", {})
    seo2 = cat.get("seo", {})
    pri  = cat.get("pricing", {})
    imgs = cat.get("images", {})
    pretty("Product Name", prod.get("name"))
    pretty("Category", prod.get("category"))
    pretty("Material", prod.get("material"))
    en_text = desc.get("english", "")
    pretty("English Desc", en_text[:100] + ("..." if len(en_text) > 100 else ""))
    hi_text = desc.get("hindi", "")
    pretty("Hindi Desc", hi_text[:80] + ("..." if len(hi_text) > 80 else ""))
    pretty("SEO Title", seo2.get("title"))
    pretty("Keywords", seo2.get("keywords"))
    pretty("Price INR", pri.get("recommended"))
    pretty("Range", f"{pri.get('minimum')} – {pri.get('maximum')}")
    orig_len = len(imgs.get("original", ""))
    proc_len = len(imgs.get("processed", ""))
    pretty("Original URI", f"data:image/...  ({orig_len:,} chars)")
    pretty("Processed URI", f"data:image/...  ({proc_len:,} chars)")
except Exception:
    print(f"  Error: {r.text[:400]}")
print()

# ── Gate 12: Async ────────────────────────────────────────────
print("[Gate 12] Async catalog job + polling...")
with open(IMG, "rb") as f:
    r = requests.post(
        BASE + "/ai/generate-catalog-async",
        files={"image": (IMG, f, "image/jpeg")},
        data={"raw_material_cost": "200", "labour_cost": "300", "skip_bg_removal": "true"}
    )
pretty("Submit", r.status_code)
try:
    job = r.json()
    job_id = job.get("job_id")
    pretty("Job ID", job_id)
    pretty("Initial Status", job.get("status"))
    for i in range(40):
        time.sleep(0.5)
        pr = requests.get(f"{BASE}/ai/status/{job_id}")
        pd = pr.json()
        if pd.get("status") == "completed":
            result_name = pd.get("result", {}).get("product", {}).get("name", "?")
            pretty("Completed in", f"{(i+1)*0.5:.1f}s")
            pretty("Result name", result_name)
            break
        elif pd.get("status") == "failed":
            pretty("Failed", pd.get("error"))
            break
        else:
            print(f"  Polling... ({(i+1)*0.5:.1f}s)", end="\r")
except Exception as e:
    print(f"  Error: {e}")

print()
print(SEP)
print("ALL GATES TESTED AGAINST LIVE IMAGE")
print(SEP)

if server_proc:
    print("\nShutting down background test server...")
    try:
        server_proc.terminate()
        server_proc.wait(timeout=5)
    except Exception:
        pass
'''


def main() -> None:
    """Run the manual, live pipeline probe.

    Keeping its executable code here makes this module safe for pytest to
    import during test discovery: imports must not parse CLI flags, launch a
    server, make network requests, or write result images.
    """
    exec(compile(PIPELINE_SCRIPT, __file__, "exec"), globals(), globals())


if __name__ == "__main__":
    main()
