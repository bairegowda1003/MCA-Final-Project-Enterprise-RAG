import React, { useState, useEffect, useRef } from "react";
const API = "http://localhost:8000";

export default function Documents() {
  const [docs, setDocs]             = useState([]);
  const [total, setTotal]           = useState(0);
  const [loading, setLoading]       = useState(true);
  const [msg, setMsg]               = useState(null);
  const [err, setErr]               = useState(null);
  const updRef = useRef();

  const load = async () => {
    try {
      const r = await fetch(`${API}/documents`);
      const d = await r.json();
      setDocs(d.documents || []); setTotal(d.total_chunks || 0);
    } catch { setErr("Cannot reach backend. Is it running on port 8000?"); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const del = async (id, name) => {
    if (!window.confirm(`Delete "${name}" from the knowledge base?`)) return;
    await fetch(`${API}/document/${id}`, { method: "DELETE" });
    setMsg(`✅ "${name}" removed.`); load();
  };

  const upd = async (id) => {
    const f = updRef.current?.files[0];
    if (!f) return;
    const form = new FormData(); form.append("file", f);
    const r = await fetch(`${API}/document/${id}`, { method: "PUT", body: form });
    const d = await r.json();
    setMsg(`✅ Updated — ${d.message}`); load();
  };

  return (
    <div>
      <div className="stats-row">
        <div className="stat-box"><div className="stat-num">{docs.length}</div><div className="stat-label">Documents</div></div>
        <div className="stat-box"><div className="stat-num">{total.toLocaleString()}</div><div className="stat-label">Total Chunks</div></div>
        <div className="stat-box"><div className="stat-num" style={{ fontSize: 22 }}>{total > 0 ? "Active" : "Empty"}</div><div className="stat-label">Index Status</div></div>
      </div>

      {msg && <div className="alert alert-success">{msg}</div>}
      {err && <div className="alert alert-error">⚠ {err}</div>}

      <div className="card">
        <div className="card-header">
          <div className="card-title-lg">Knowledge Base</div>
          <button className="btn btn-ghost btn-sm" onClick={load}>↻ Refresh</button>
        </div>
        <div className="section-rule" />
        {loading ? (
          <div style={{ color: "var(--text3)", fontFamily: "var(--mono)", fontSize: 13, padding: "20px 0", textAlign: "center" }}>Loading documents…</div>
        ) : docs.length === 0 ? (
          <div className="alert alert-info">No documents indexed yet. Go to Upload tab to add PDFs.</div>
        ) : (
          <div className="doc-list">
            {docs.map((doc) => (
              <div key={doc.document_id} className="doc-item">
                <div className="doc-file-icon">📄</div>
                <div className="doc-meta">
                  <div className="doc-name">{doc.filename}</div>
                  <div className="doc-id">ID: {doc.document_id}</div>
                </div>
                <div className="doc-actions">
                  <label className="btn btn-ghost btn-sm" style={{ cursor: "pointer" }}>
                    🔄 Replace
                    <input type="file" accept=".pdf" style={{ display: "none" }} ref={updRef} onChange={() => upd(doc.document_id)} />
                  </label>
                  <button className="btn btn-danger btn-sm" onClick={() => del(doc.document_id, doc.filename)}>🗑 Delete</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-title" style={{ marginBottom: 14 }}>CRUD Operations</div>
        <div className="tips-list">
          {[
            "Add — Upload tab → PDF gets chunked and indexed into ChromaDB vector store",
            "Read — Research tab → semantic search across all indexed documents",
            "Update — Replace button → old chunks removed, new chunks indexed automatically",
            "Delete — Removes all vector embeddings for that document from ChromaDB"
          ].map((t, i) => (
            <div key={i} className="tip-item"><div className="tip-dot" /><span>{t}</span></div>
          ))}
        </div>
      </div>
    </div>
  );
}
