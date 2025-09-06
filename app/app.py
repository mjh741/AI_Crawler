import os
import uuid
import threading
import json
import time
from flask import Flask, request, render_template, Response, send_file, redirect, url_for
from storage import Storage
from scanner import run_scan
from report import build_pdf_report

APP_NAME = os.getenv("BRAND_NAME", "AI Discoverability Scanner")
MAX_PAGES = int(os.getenv("MAX_PAGES", "10"))
MAX_DEPTH = int(os.getenv("MAX_DEPTH", "2"))
PAGE_TIMEOUT = int(os.getenv("PAGE_TIMEOUT_SEC", "25"))

app = Flask(__name__, template_folder="templates", static_folder="static")
storage = Storage()

jobs_dir = os.getenv("JOBS_DIR", "./jobs")
os.makedirs(jobs_dir, exist_ok=True)

def log_status(job_id, message):
    payload = {"ts": time.time(), "message": message}
    storage.append_status(job_id, json.dumps(payload))

def worker(job_id, url):
    try:
        log_status(job_id, f"Starting scan for {url}")
        results = run_scan(
            url=url,
            max_pages=MAX_PAGES,
            max_depth=MAX_DEPTH,
            page_timeout_sec=PAGE_TIMEOUT,
            log=lambda m: log_status(job_id, m)
        )
        storage.save_json(job_id, "results.json", results)
        log_status(job_id, "Building PDF report")
        pdf_path = build_pdf_report(job_id, results, storage)
        storage.save_artifact(job_id, "report.pdf", pdf_path)
        log_status(job_id, "Complete")
    except Exception as e:
        log_status(job_id, f"ERROR: {e}")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", app_name=APP_NAME, max_pages=MAX_PAGES, max_depth=MAX_DEPTH)

@app.route("/scan", methods=["POST"])
def scan():
    url = request.form.get("url","").strip()
    if not url:
        return redirect(url_for('index'))
    if not url.startswith("http"):
        url = "https://" + url
    job_id = str(uuid.uuid4())
    storage.init_job(job_id)
    t = threading.Thread(target=worker, args=(job_id, url), daemon=True)
    t.start()
    return redirect(url_for('status_page', job_id=job_id))

@app.route("/status/<job_id>", methods=["GET"])
def status_page(job_id):
    return render_template("status.html", job_id=job_id, app_name=APP_NAME)

@app.route("/events/<job_id>")
def events(job_id):
    def generate():
        last_index = 0
        while True:
            msgs = storage.read_status(job_id)
            if msgs and len(msgs) > last_index:
                for m in msgs[last_index:]:
                    yield f"data: {m}\n\n"
                last_index = len(msgs)
            time.sleep(1)
    return Response(generate(), mimetype="text/event-stream")

@app.route("/report/<job_id>.pdf")
def report(job_id):
    fpath = storage.get_artifact_path(job_id, "report.pdf")
    if not fpath or not os.path.exists(fpath):
        return "Report not ready.", 404
    return send_file(fpath, as_attachment=True, download_name=f"scan-report-{job_id}.pdf")

@app.route("/health")
def health():
    return {"status":"ok"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
