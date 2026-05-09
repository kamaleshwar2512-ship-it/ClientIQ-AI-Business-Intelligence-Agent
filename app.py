"""
app.py — Flask Web Server for ClientIQ Frontend
Exposes REST + SSE endpoints for the HTML UI
"""

import os, json, threading, queue, time, sys
from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS

# ── Load API key from environment (or .env file) ───────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
if not GROQ_API_KEY:
    print("[ERROR] GROQ_API_KEY not set. Add it to a .env file or set it as an environment variable.")
    sys.exit(1)

app = Flask(__name__, static_folder="static", template_folder="static")
CORS(app)

# ── SSE event queues keyed by job_id ──────────────────────────
_queues: dict[str, queue.Queue] = {}

def _push(job_id: str, event: str, data: dict):
    if job_id in _queues:
        _queues[job_id].put({"event": event, "data": data})

# ── Monkey-patch rich console so we capture output ─────────────
import io, re
from rich.console import Console as _RichConsole

class CaptureConsole(_RichConsole):
    def __init__(self, job_id, *a, **kw):
        super().__init__(file=io.StringIO(), *a, **kw)
        self._job_id = job_id

    def print(self, *args, **kwargs):
        super().print(*args, **kwargs)
        raw = self.file.getvalue()
        self.file.truncate(0); self.file.seek(0)
        # Strip ANSI
        clean = re.sub(r"\x1b\[[0-9;]*m", "", raw).strip()
        if clean:
            _push(self._job_id, "log", {"text": clean})

# ── Worker thread ──────────────────────────────────────────────
def _run_agent(job_id: str, mode: str, input_text: str):
    import core.agent as agent_module
    import core.report as report_module

    # Replace console in modules
    cap = CaptureConsole(job_id)
    agent_module.console = cap
    report_module.console = cap

    try:
        ag = agent_module.ClientIQAgent(api_key=GROQ_API_KEY)

        if mode == "company":
            _push(job_id, "status", {"text": "Extracting company info..."})
            result = ag.run(transcript=input_text)
            company_info = result["company_info"]
            sections = result["sections"]
            report_text = report_module.build_report(company_info, sections)
            path = report_module.save_report(report_text, company_info.get("company_name","Report"), "./reports")
            _push(job_id, "done", {
                "report": report_text,
                "path": path,
                "meta": company_info,
                "mode": "company"
            })

        else:  # startup
            _push(job_id, "status", {"text": "Parsing your business idea..."})
            result = ag.run_startup(user_input=input_text)
            idea_info = result["idea_info"]
            sections = result["sections"]
            report_text = report_module.build_startup_report(idea_info, sections)
            path = report_module.save_startup_report(report_text, idea_info.get("business_idea","startup"), "./reports")
            _push(job_id, "done", {
                "report": report_text,
                "path": path,
                "meta": idea_info,
                "mode": "startup"
            })

    except Exception as e:
        _push(job_id, "error", {"text": str(e)})
    finally:
        time.sleep(2)
        _queues.pop(job_id, None)


# ── Routes ─────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/start", methods=["POST"])
def start():
    body = request.json or {}
    mode = body.get("mode", "company")
    input_text = body.get("input", "").strip()

    if not input_text:
        return jsonify({"error": "Input text is required"}), 400

    job_id = f"job_{int(time.time()*1000)}"
    _queues[job_id] = queue.Queue()

    t = threading.Thread(target=_run_agent, args=(job_id, mode, input_text), daemon=True)
    t.start()
    return jsonify({"job_id": job_id})

@app.route("/api/stream/<job_id>")
def stream(job_id: str):
    def generate():
        if job_id not in _queues:
            yield f"data: {json.dumps({'event':'error','data':{'text':'Job not found'}})}\n\n"
            return
        q = _queues[job_id]
        while True:
            try:
                msg = q.get(timeout=60)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg["event"] in ("done", "error"):
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'event':'ping','data':{}})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    os.makedirs("reports", exist_ok=True)
    print("ClientIQ Web UI -> http://localhost:5000")
    app.run(debug=False, threaded=True, port=5000)
