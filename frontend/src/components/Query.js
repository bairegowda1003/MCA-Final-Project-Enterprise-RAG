import React, { useState } from "react";
const API = "http://localhost:8000";

export default function Query() {
  const [query, setQuery]         = useState("");
  const [loading, setLoading]     = useState(false);
  const [result, setResult]       = useState(null);
  const [error, setError]         = useState(null);
  const [generating, setGen]      = useState(false);
  const [reportUrl, setReportUrl] = useState(null);

  const run = async () => {
    if (!query.trim()) return;
    setLoading(true); setError(null); setResult(null); setReportUrl(null);
    try {
      const res  = await fetch(`${API}/query`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Query failed");
      if (!data.success) throw new Error(data.error || "Query failed");
      setResult(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const getPdf = async () => {
    if (!result?.answer) return;
    setGen(true);
    try {
      const res  = await fetch(`${API}/generate-report`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: query, answer: result.answer, chunks: result.chunks }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setReportUrl(`${API}${data.download_url}`);
    } catch (e) { setError(e.message); }
    finally { setGen(false); }
  };

  return (
    <div>
      {/* Search card */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title-lg">Research Query</div>
            <div className="card-sub">Enter a topic — the system retrieves evidence and generates a cited report</div>
          </div>
        </div>
        <div className="section-rule" />
        <div className="search-wrap">
          <input
            className="search-input"
            placeholder="e.g.  Machine learning in cybersecurity,  Deep learning architectures,  Cloud computing trends..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !loading && run()}
          />
          <button className="btn btn-primary" onClick={run} disabled={loading || !query.trim()}>
            {loading ? <><span className="spinner" /> Analyzing...</> : <>🔍 Generate</>}
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error">⚠ {error}</div>}
      {result?.warning && <div className="alert alert-warning">{result.warning}</div>}

      {/* Fallback mode */}
      {result?.fallback && result.chunks && (
        <div className="card">
          <div className="card-title" style={{ marginBottom: 14 }}>Retrieved Sources — Fallback Mode</div>
          <div className="source-list">
            {result.chunks.map((c, i) => (
              <div key={i} className="source-item">
                <div className="source-item-header">[{i+1}] {c.metadata.filename} — Page {c.metadata.page_number}</div>
                <div className="source-item-text">{c.text.substring(0, 220)}…</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Report */}
      {result?.answer && (
        <>
          <div className="card">
            <div className="card-header">
              <div className="card-title-lg">Research Report</div>
              <div className="report-actions">
                <button className="btn btn-primary btn-sm" onClick={getPdf} disabled={generating}>
                  {generating ? <><span className="spinner" /> Generating PDF...</> : "📄 Export PDF"}
                </button>
                {reportUrl && (
                  <a href={reportUrl} download className="btn btn-ghost btn-sm" style={{ textDecoration: "none" }}>
                    ⬇ Download
                  </a>
                )}
              </div>
            </div>
            <div className="section-rule" />
            <div className="report-box">{result.answer}</div>
          </div>

          <div className="card">
            <div className="card-title" style={{ marginBottom: 14 }}>Evidence Sources · {result.chunks?.length || 0} retrieved</div>
            <div className="source-list">
              {result.chunks?.map((c, i) => (
                <div key={i} className="source-item">
                  <div className="source-item-header">[{i+1}] {c.metadata.filename} — Page {c.metadata.page_number}</div>
                  <div className="source-item-text">{c.text.substring(0, 160)}…</div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
