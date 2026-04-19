from flask import Flask, jsonify
from utils.db_client import get_results_with_datetime_analysis, get_all_tags

app = Flask(__name__)

@app.route("/api/results/<tag>")
def get_results(tag):
    """Retorna resultados de uma rodovia."""
    results = get_results_with_datetime_analysis(tag)
    return jsonify(results)

@app.route("/api/tags")
def get_tags():
    """Retorna todas as rodovias."""
    tags = get_all_tags()
    return jsonify({"tags": tags})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)