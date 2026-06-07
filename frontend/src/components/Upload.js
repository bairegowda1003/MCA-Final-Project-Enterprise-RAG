import React, { useState, useRef } from "react";
const API = "http://localhost:8000";

export default function Upload() {
  const [file, setFile]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);
  const [error, setError]     = useState(null);
  const [drag, setDrag]       = useState(false);
  const ref = useRef();

  const pick = (f) => {
    if (!f) return;
    if (!f.name.endsWith(".pdf")) { setError("Only PDF files are supported."); return; }
    setFile(f); setResult(null); setError(null);
  };

  const upload = async () => {
    if (!file) return;
    setLoading(true); setError(null); setResult(null);
    const form = new FormData();
    form.append("file", file);
    try {
      const res  = await fetch(`${API}/upload`, { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      setResult(data); setFile(null);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title-lg">Upload Document</div>
            <div className="card-sub">PDF files are automatically chunked and indexed into ChromaDB</div>
          </div>
        </div>
        <div className="section-rule" />

        <div
          className={`upload-zone ${drag ? "dragging" : ""}`}
          onClick={() => ref.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files[0]); }}
        >
          <div className="upload-icon-wrap">{file ? "📄" : "⬆"}</div>
          {file ? (
            <><div className="upload-title">{file.name}</div><div className="upload-sub">{(file.size/1024/1024).toFixed(2)} MB — ready to index</div></>
          ) : (
            <><div className="upload-title">Drop your PDF here</div><div className="upload-sub">or click to browse your files<br/>Supports large documents — 5000+ pages handled automatically</div></>
          )}
          <input ref={ref} type="file" accept=".pdf" className="upload-input" onChange={(e) => pick(e.target.files[0])} />
        </div>

        {file && (
          <div style={{ marginTop: 16 }}>
            <button className="btn btn-primary" onClick={upload} disabled={loading}>
              {loading ? <><span className="spinner" /> Indexing into ChromaDB...</> : "⬆ Upload & Index Document"}
            </button>
          </div>
        )}
        {loading && <div className="progress-track"><div className="progress-fill" style={{ width: "100%" }} /></div>}
      </div>

      {result && (
        <div className="alert alert-success">
          ✅ <span><strong>{result.filename}</strong> indexed — {result.pages} pages · {result.chunks_added} chunks stored</span>
        </div>
      )}
      {error && <div className="alert alert-error">⚠ {error}</div>}

      <div className="card">
        <div className="card-title" style={{ marginBottom: 14 }}>Usage Tips</div>
        <div className="tips-list">
          {["Upload multiple PDFs to build a rich knowledge base — more pages = better retrieval",
            "After uploading, go to Research tab and enter any topic to generate a cited report",
            "Large files (100+ pages) take 20–30 seconds to index — please wait for confirmation",
            "Manage or replace documents anytime from the Library tab without rebuilding the index"
          ].map((t, i) => (
            <div key={i} className="tip-item"><div className="tip-dot" /><span>{t}</span></div>
          ))}
        </div>
      </div>
    </div>
  );
}
