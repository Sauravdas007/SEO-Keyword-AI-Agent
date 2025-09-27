"""
Flask API wrapper for the SEO Keyword Research Agent.
Endpoint: /keywords
- GET: query param 'seed' required, 'n' optional (default 50).
- POST: JSON body with {"seed": "...", "n": 50}
"""
from flask import Flask, request, jsonify
import os
from agent.generator import generate_candidates

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"ok", "version": "0.2.0"})

@app.route("/keywords", methods=["GET","POST"])
def keywords():
    if request.method == "GET":
        seed = request.args.get("seed", "").strip()
        n = int(request.args.get("n", 50))
    else:
        data = request.get_json() or {}
        seed = (data.get("seed") or data.get("keyword") or "").strip()
        n = int(data.get("n") or 50)
    if not seed:
        return jsonify({"error": "Provide 'seed' parameter (query or JSON)"}), 400
    try:
        results = generate_candidates(seed, n=n, use_cache=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"seed": seed, "n": n, "results": results})
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
