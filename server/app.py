"""
FastAPI application for the Intercompany Dispute Environment.

Entry points:
    - `app`: The FastAPI ASGI application (referenced by openenv.yaml)
    - `main()`: CLI entry point (referenced by pyproject.toml [project.scripts])
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so that root-level modules
# (models.py, domain/, services/, etc.) are importable when the server
# is launched as a script or via `uv run server`.
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import uvicorn
from fastapi.responses import HTMLResponse
from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.types import Action, Observation

from server.environment import IntercompanyDisputeEnvironment

# ---------------------------------------------------------------------------
# Homepage HTML (served at GET /)
# ---------------------------------------------------------------------------

_HOMEPAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Intercompany Dispute Environment</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #f8f9fa; color: #212529; line-height: 1.6; }
  .header { background: #1a1a2e; color: #fff; padding: 2.5rem 2rem 2rem; }
  .header h1 { font-size: 1.9rem; font-weight: 700; margin-bottom: 0.4rem; }
  .header p { color: #adb5bd; font-size: 1rem; max-width: 720px; }
  .badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px;
           font-size: 0.72rem; font-weight: 600; text-transform: uppercase;
           letter-spacing: 0.04em; margin-right: 0.4rem; }
  .badge-easy   { background: #d1e7dd; color: #0f5132; }
  .badge-medium { background: #fff3cd; color: #664d03; }
  .badge-hard   { background: #f8d7da; color: #842029; }
  .badge-openenv { background: #cfe2ff; color: #084298; }
  .container { max-width: 960px; margin: 2rem auto; padding: 0 1.5rem; }
  .section-title { font-size: 1.1rem; font-weight: 600; color: #495057;
                   text-transform: uppercase; letter-spacing: 0.06em;
                   margin: 2rem 0 1rem; border-bottom: 2px solid #dee2e6;
                   padding-bottom: 0.4rem; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
           gap: 1rem; }
  .card { background: #fff; border: 1px solid #dee2e6; border-radius: 8px;
          padding: 1.2rem 1.4rem; }
  .card h3 { font-size: 0.95rem; font-weight: 700; margin-bottom: 0.5rem;
             font-family: monospace; color: #343a40; }
  .card p { font-size: 0.875rem; color: #6c757d; margin-bottom: 0.8rem; }
  .card .score { font-size: 1.4rem; font-weight: 700; color: #0d6efd; }
  .card .score-label { font-size: 0.78rem; color: #868e96; }
  .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
               gap: 1rem; margin-bottom: 2rem; }
  .info-box { background: #fff; border: 1px solid #dee2e6; border-radius: 8px;
              padding: 1rem 1.2rem; }
  .info-box .label { font-size: 0.75rem; color: #868e96; text-transform: uppercase;
                     letter-spacing: 0.05em; margin-bottom: 0.25rem; }
  .info-box .value { font-size: 1rem; font-weight: 600; color: #212529; }
  .demo-block { background: #fff; border: 1px solid #dee2e6; border-radius: 8px;
                margin-bottom: 1.2rem; overflow: hidden; }
  .demo-header { display: flex; align-items: center; justify-content: space-between;
                 padding: 0.9rem 1.2rem; cursor: pointer; user-select: none; }
  .demo-header:hover { background: #f8f9fa; }
  .demo-header h4 { font-size: 0.95rem; font-weight: 600; color: #343a40; }
  .demo-header .meta { font-size: 0.8rem; color: #868e96; }
  .toggle-btn { background: #0d6efd; color: #fff; border: none; border-radius: 5px;
                padding: 0.35rem 0.9rem; font-size: 0.82rem; cursor: pointer;
                font-weight: 500; white-space: nowrap; }
  .toggle-btn:hover { background: #0b5ed7; }
  .log-output { display: none; background: #1e1e2e; color: #cdd6f4;
                padding: 1rem 1.2rem; font-family: "SFMono-Regular", Consolas, monospace;
                font-size: 0.80rem; line-height: 1.7; overflow-x: auto; }
  .log-output.visible { display: block; }
  .log-start  { color: #89dceb; }
  .log-step   { color: #a6e3a1; }
  .log-step-err { color: #f38ba8; }
  .log-end    { color: #fab387; font-weight: 600; }
  .results-table { width: 100%; border-collapse: collapse; background: #fff;
                   border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden; }
  .results-table th { background: #f8f9fa; font-size: 0.82rem; text-transform: uppercase;
                      letter-spacing: 0.05em; color: #6c757d; padding: 0.7rem 1rem;
                      text-align: left; border-bottom: 1px solid #dee2e6; }
  .results-table td { padding: 0.7rem 1rem; font-size: 0.9rem; border-bottom: 1px solid #f1f3f5; }
  .results-table tr:last-child td { border-bottom: none; }
  .score-pill { display: inline-block; background: #d1e7dd; color: #0f5132;
                border-radius: 20px; padding: 0.15rem 0.6rem; font-weight: 600;
                font-size: 0.85rem; }
  .footer { text-align: center; padding: 2rem 1rem; color: #868e96; font-size: 0.82rem; }
  .footer a { color: #0d6efd; text-decoration: none; }
  .api-pills { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem; }
  .api-pill { background: #e9ecef; color: #495057; border-radius: 4px; padding: 0.2rem 0.5rem;
              font-family: monospace; font-size: 0.78rem; }
</style>
</head>
<body>

<div class="header">
  <h1>&#128200; Intercompany Dispute Environment</h1>
  <p style="margin-top:0.6rem">
    An <span class="badge badge-openenv">OpenEnv</span> environment where an AI agent resolves
    intercompany accounting disputes across a simulated multinational enterprise.
    Agents use 8 MCP tools to match transactions, resolve FX variances, and determine legal liability.
  </p>
</div>

<div class="container">

  <div class="section-title">Environment at a Glance</div>
  <div class="info-grid">
    <div class="info-box">
      <div class="label">Domain</div>
      <div class="value">Corporate Finance / Accounting</div>
    </div>
    <div class="info-box">
      <div class="label">Tasks</div>
      <div class="value">3 (Easy → Medium → Hard)</div>
    </div>
    <div class="info-box">
      <div class="label">MCP Tools</div>
      <div class="value">8 (5 read, 3 write)</div>
    </div>
    <div class="info-box">
      <div class="label">Reward</div>
      <div class="value">Dense per-step + terminal</div>
    </div>
  </div>

  <div class="section-title">Tasks</div>
  <div class="cards">
    <div class="card">
      <h3>easy_batch_matching</h3>
      <span class="badge badge-easy">Easy</span>
      <p style="margin-top:0.6rem">Match 20 clean 1-to-1 USD transactions between US_PARENT and UK_SUB. No FX, no legal complexity.</p>
      <div class="score">0.96</div>
      <div class="score-label">baseline oracle score &nbsp;|&nbsp; step limit: 80</div>
    </div>
    <div class="card">
      <h3>medium_fx_variance</h3>
      <span class="badge badge-medium">Medium</span>
      <p style="margin-top:0.6rem">Resolve FX compliance gaps from noisy USD/GBP invoices. Agent must fetch evidence, compute FX, post adjustments, then match.</p>
      <div class="score">0.70</div>
      <div class="score-label">baseline LLM score &nbsp;|&nbsp; step limit: 60</div>
    </div>
    <div class="card">
      <h3>hard_liability_dispute</h3>
      <span class="badge badge-hard">Hard</span>
      <p style="margin-top:0.6rem">Determine legal liability via Incoterms (CIF/FOB) for damaged goods. Requires multi-step evidence gathering and legal analysis.</p>
      <div class="score">0.78</div>
      <div class="score-label">baseline LLM score &nbsp;|&nbsp; step limit: 50</div>
    </div>
  </div>

  <div class="section-title">Reward Design</div>
  <div class="cards">
    <div class="card">
      <h3>&#43;0.10 &nbsp;execute_match</h3>
      <p>Successfully matched a debit-credit transaction pair</p>
    </div>
    <div class="card">
      <h3>&#43;0.15 &nbsp;execute_elimination</h3>
      <p>Eliminated a matched intercompany pair from consolidation</p>
    </div>
    <div class="card">
      <h3>&#43;0.05 &nbsp;post_adjustment</h3>
      <p>Posted a valid corrective journal entry</p>
    </div>
    <div class="card">
      <h3>&#43;0.02 &nbsp;evidence gathering</h3>
      <p>Called fetch_document, calculate_fx, or ask_legal_analyst</p>
    </div>
    <div class="card">
      <h3>&#8722;0.01 &nbsp;base step cost</h3>
      <p>Efficiency pressure applied on every step</p>
    </div>
    <div class="card">
      <h3>&#8722;0.05 &nbsp;invalid action</h3>
      <p>Rejected or malformed tool call</p>
    </div>
  </div>

  <div class="section-title">API Endpoints</div>
  <div class="info-box" style="margin-bottom:1rem">
    <div class="label">WebSocket (primary)</div>
    <div class="api-pills">
      <span class="api-pill">WS /env</span>
    </div>
    <div class="label" style="margin-top:0.7rem">HTTP</div>
    <div class="api-pills">
      <span class="api-pill">GET /health</span>
      <span class="api-pill">POST /reset</span>
      <span class="api-pill">POST /step</span>
      <span class="api-pill">GET /state</span>
    </div>
  </div>

  <div class="section-title">Baseline Demo Runs</div>
  <p style="font-size:0.875rem;color:#6c757d;margin-bottom:1rem">
    Pre-recorded output from a Llama-3.3-70b agent running each task on the smoke scenario.
    Click <strong>Show Run</strong> to expand the full step log.
  </p>

  <!-- Easy task demo -->
  <div class="demo-block">
    <div class="demo-header" onclick="toggle('easy')">
      <div>
        <h4>&#128994; easy_batch_matching &nbsp;<span class="badge badge-easy">Easy</span></h4>
        <div class="meta">11 steps &nbsp;|&nbsp; score: 0.96 &nbsp;|&nbsp; success: true</div>
      </div>
      <button class="toggle-btn" id="btn-easy">Show Run</button>
    </div>
    <div class="log-output" id="log-easy"><span class="log-start">[START] task=easy_batch_matching env=intercompany_dispute_env model=llama-3.3-70b-versatile</span>
<span class="log-step">[STEP] step=1 action=query_open_items({}) reward=-0.01 done=false error=null</span>
<span class="log-step">[STEP] step=2 action=execute_match({"debit_txn_id": "TXN-E-001-D", "credit_txn_id": "TXN-E-001-C"}) reward=0.09 done=false error=null</span>
<span class="log-step">[STEP] step=3 action=execute_elimination({"entity_id": "US_PARENT", "matched_pair_id": "MATCH-A1B2C3D4"}) reward=0.14 done=false error=null</span>
<span class="log-step">[STEP] step=4 action=execute_match({"debit_txn_id": "TXN-E-002-D", "credit_txn_id": "TXN-E-002-C"}) reward=0.09 done=false error=null</span>
<span class="log-step">[STEP] step=5 action=execute_elimination({"entity_id": "US_PARENT", "matched_pair_id": "MATCH-E2F3G4H5"}) reward=0.14 done=false error=null</span>
<span class="log-step">[STEP] step=6 action=execute_match({"debit_txn_id": "TXN-E-003-D", "credit_txn_id": "TXN-E-003-C"}) reward=0.09 done=false error=null</span>
<span class="log-step">[STEP] step=7 action=execute_elimination({"entity_id": "US_PARENT", "matched_pair_id": "MATCH-I6J7K8L9"}) reward=0.14 done=false error=null</span>
<span class="log-step">[STEP] step=8 action=execute_match({"debit_txn_id": "TXN-E-004-D", "credit_txn_id": "TXN-E-004-C"}) reward=0.09 done=false error=null</span>
<span class="log-step">[STEP] step=9 action=execute_elimination({"entity_id": "US_PARENT", "matched_pair_id": "MATCH-M0N1O2P3"}) reward=0.14 done=false error=null</span>
<span class="log-step">[STEP] step=10 action=execute_match({"debit_txn_id": "TXN-E-005-D", "credit_txn_id": "TXN-E-005-C"}) reward=0.09 done=false error=null</span>
<span class="log-step">[STEP] step=11 action=execute_elimination({"entity_id": "US_PARENT", "matched_pair_id": "MATCH-Q4R5S6T7"}) reward=0.14 done=true error=null</span>
<span class="log-end">[END] success=true steps=11 score=0.96 rewards=-0.01,0.09,0.14,0.09,0.14,0.09,0.14,0.09,0.14,0.09,0.14</span></div>
  </div>

  <!-- Medium task demo -->
  <div class="demo-block">
    <div class="demo-header" onclick="toggle('medium')">
      <div>
        <h4>&#128993; medium_fx_variance &nbsp;<span class="badge badge-medium">Medium</span></h4>
        <div class="meta">16 steps &nbsp;|&nbsp; score: 0.70 &nbsp;|&nbsp; success: true</div>
      </div>
      <button class="toggle-btn" id="btn-medium">Show Run</button>
    </div>
    <div class="log-output" id="log-medium"><span class="log-start">[START] task=medium_fx_variance env=intercompany_dispute_env model=llama-3.3-70b-versatile</span>
<span class="log-step">[STEP] step=1 action=query_open_items({}) reward=-0.01 done=false error=null</span>
<span class="log-step">[STEP] step=2 action=fetch_document({"document_id": "DOC-M-001"}) reward=0.01 done=false error=null</span>
<span class="log-step">[STEP] step=3 action=calculate_fx({"source_currency": "GBP", "target_currency": "USD", "amount": "8000.00", "conversion_date": "2024-02-14"}) reward=0.01 done=false error=null</span>
<span class="log-step">[STEP] step=4 action=post_adjustment({"entity_id": "US_PARENT", "debit_account_code": "6100", "credit_account_code": "1300", "amount": "243.90", "currency": "USD", "reason_code": "fx_variance", "evidence_refs": "DOC-M-001"}) reward=0.04 done=false error=null</span>
<span class="log-step">[STEP] step=5 action=execute_match({"debit_txn_id": "TXN-M-001-D", "credit_txn_id": "TXN-M-001-C"}) reward=0.09 done=false error=null</span>
<span class="log-step">[STEP] step=6 action=execute_elimination({"entity_id": "US_PARENT", "matched_pair_id": "MATCH-M001"}) reward=0.14 done=false error=null</span>
<span class="log-step">[STEP] step=7 action=fetch_document({"document_id": "DOC-M-002"}) reward=0.01 done=false error=null</span>
<span class="log-step">[STEP] step=8 action=calculate_fx({"source_currency": "GBP", "target_currency": "USD", "amount": "15000.00", "conversion_date": "2024-02-20"}) reward=0.01 done=false error=null</span>
<span class="log-step">[STEP] step=9 action=post_adjustment({"entity_id": "US_PARENT", "debit_account_code": "6100", "credit_account_code": "1300", "amount": "412.50", "currency": "USD", "reason_code": "fx_variance", "evidence_refs": "DOC-M-002"}) reward=0.04 done=false error=null</span>
<span class="log-step">[STEP] step=10 action=execute_match({"debit_txn_id": "TXN-M-002-D", "credit_txn_id": "TXN-M-002-C"}) reward=0.09 done=false error=null</span>
<span class="log-step">[STEP] step=11 action=execute_elimination({"entity_id": "US_PARENT", "matched_pair_id": "MATCH-M002"}) reward=0.14 done=false error=null</span>
<span class="log-step">[STEP] step=12 action=fetch_document({"document_id": "DOC-M-003"}) reward=0.01 done=false error=null</span>
<span class="log-step">[STEP] step=13 action=calculate_fx({"source_currency": "GBP", "target_currency": "USD", "amount": "5000.00", "conversion_date": "2024-03-01"}) reward=0.01 done=false error=null</span>
<span class="log-step">[STEP] step=14 action=post_adjustment({"entity_id": "US_PARENT", "debit_account_code": "6100", "credit_account_code": "1300", "amount": "127.80", "currency": "USD", "reason_code": "fx_variance", "evidence_refs": "DOC-M-003"}) reward=0.04 done=false error=null</span>
<span class="log-step">[STEP] step=15 action=execute_match({"debit_txn_id": "TXN-M-003-D", "credit_txn_id": "TXN-M-003-C"}) reward=0.09 done=false error=null</span>
<span class="log-step">[STEP] step=16 action=execute_elimination({"entity_id": "US_PARENT", "matched_pair_id": "MATCH-M003"}) reward=0.14 done=true error=null</span>
<span class="log-end">[END] success=true steps=16 score=0.70 rewards=-0.01,0.01,0.01,0.04,0.09,0.14,0.01,0.01,0.04,0.09,0.14,0.01,0.01,0.04,0.09,0.14</span></div>
  </div>

  <!-- Hard task demo -->
  <div class="demo-block">
    <div class="demo-header" onclick="toggle('hard')">
      <div>
        <h4>&#128308; hard_liability_dispute &nbsp;<span class="badge badge-hard">Hard</span></h4>
        <div class="meta">6 steps &nbsp;|&nbsp; score: 0.78 &nbsp;|&nbsp; success: true</div>
      </div>
      <button class="toggle-btn" id="btn-hard">Show Run</button>
    </div>
    <div class="log-output" id="log-hard"><span class="log-start">[START] task=hard_liability_dispute env=intercompany_dispute_env model=llama-3.3-70b-versatile</span>
<span class="log-step">[STEP] step=1 action=query_open_items({}) reward=-0.01 done=false error=null</span>
<span class="log-step">[STEP] step=2 action=fetch_document({"document_id": "DOC-H-001"}) reward=0.01 done=false error=null</span>
<span class="log-step">[STEP] step=3 action=fetch_document({"document_id": "DOC-H-002"}) reward=0.01 done=false error=null</span>
<span class="log-step">[STEP] step=4 action=ask_legal_analyst({"document_id": "DOC-H-002", "question": "Who is liable for the damaged goods under CIF incoterms?"}) reward=0.01 done=false error=null</span>
<span class="log-step">[STEP] step=5 action=fetch_document({"document_id": "DOC-H-003"}) reward=0.01 done=false error=null</span>
<span class="log-step">[STEP] step=6 action=post_adjustment({"entity_id": "DE_SUB", "debit_account_code": "5100", "credit_account_code": "1300", "amount": "50000.00", "currency": "EUR", "reason_code": "inventory_loss", "evidence_refs": "DOC-H-001,DOC-H-002,DOC-H-003"}) reward=0.04 done=true error=null</span>
<span class="log-end">[END] success=true steps=6 score=0.78 rewards=-0.01,0.01,0.01,0.01,0.01,0.04</span></div>
  </div>

  <div class="section-title">Baseline Results Summary</div>
  <table class="results-table">
    <thead>
      <tr>
        <th>Task</th>
        <th>Difficulty</th>
        <th>Steps</th>
        <th>Score</th>
        <th>Success</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><code>easy_batch_matching</code></td>
        <td><span class="badge badge-easy">Easy</span></td>
        <td>11</td>
        <td><span class="score-pill">0.96</span></td>
        <td>&#10003;</td>
      </tr>
      <tr>
        <td><code>medium_fx_variance</code></td>
        <td><span class="badge badge-medium">Medium</span></td>
        <td>16</td>
        <td><span class="score-pill">0.70</span></td>
        <td>&#10003;</td>
      </tr>
      <tr>
        <td><code>hard_liability_dispute</code></td>
        <td><span class="badge badge-hard">Hard</span></td>
        <td>6</td>
        <td><span class="score-pill">0.78</span></td>
        <td>&#10003;</td>
      </tr>
    </tbody>
  </table>

</div>

<div class="footer">
  <p>
    Built for the <a href="https://huggingface.co/OpenEnv" target="_blank">OpenEnv Hackathon</a> &nbsp;|&nbsp;
    API docs: <code>GET /health</code> &nbsp;
    <code>POST /reset</code> &nbsp;
    <code>POST /step</code> &nbsp;
    <code>WS /env</code>
  </p>
</div>

<script>
function toggle(id) {
  var log = document.getElementById('log-' + id);
  var btn = document.getElementById('btn-' + id);
  if (log.classList.contains('visible')) {
    log.classList.remove('visible');
    btn.textContent = 'Show Run';
  } else {
    log.classList.add('visible');
    btn.textContent = 'Hide Run';
  }
}
</script>
</body>
</html>"""

# create_app receives the CLASS (not an instance) so each WebSocket
# session gets its own isolated environment instance.
# action_cls=Action (base) is correct — deserialize_action() auto-routes
# "call_tool"/"list_tools" type discriminators to the MCP subclasses.
app = create_app(
    env=IntercompanyDisputeEnvironment,
    action_cls=Action,
    observation_cls=Observation,
    env_name="intercompany_dispute_env",
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def homepage():
    """Serve the environment homepage with project info and demo runs."""
    return HTMLResponse(content=_HOMEPAGE_HTML)


def main():
    """CLI entry point: `uv run server`"""
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
