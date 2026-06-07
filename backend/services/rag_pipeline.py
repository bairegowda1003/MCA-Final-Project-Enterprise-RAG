import os
from openai import OpenAI
from flashrank import Ranker, RerankRequest
from services.vector_store import query_chunks
from services.guardrails import check_input, validate_output

ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="/tmp/flashrank")

SYSTEM_PROMPT = """You are a professional research analyst working for an enterprise knowledge management system.

Your responsibilities:
1. Analyze ONLY the retrieved document context provided to you.
2. Never fabricate facts, statistics, or claims not present in the context.
3. Always cite sources by referencing document names and page numbers.
4. Produce structured, professional research reports.
5. If the context is insufficient, clearly state that.

You must NOT respond to requests unrelated to research analysis."""


def get_client(api_key: str) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )


def build_cot_prompt(query: str, context: str) -> str:
    """Full Chain-of-Thought reasoning prompt — 5 explicit steps."""
    return f"""Research Topic: {query}

Retrieved Document Context:
{context}

---
CHAIN-OF-THOUGHT REASONING — Follow each step carefully:

Step 1 — UNDERSTAND THE TOPIC
What is the core research question? What key concepts are involved?
Write your understanding in 2-3 sentences.

Step 2 — EXTRACT KEY EVIDENCE
From the retrieved context above, identify the most relevant facts, figures, and arguments.
List each piece of evidence with its source (document name and page number).

Step 3 — ASSESS EVIDENCE QUALITY
How strong is the evidence? Is it consistent across sources? Are there any contradictions?
Note the strength of each key finding.

Step 4 — SYNTHESIZE AND REASON
Connect the evidence. What patterns emerge? What conclusions can be drawn?
Think through the implications step by step.

Step 5 — GENERATE STRUCTURED REPORT
Now write the final research report using ONLY the evidence from above.

---
FINAL REPORT FORMAT:

1. Introduction
(2-3 sentences introducing the topic and scope)

2. Key Findings
(Bullet points — each with page reference in brackets)

3. Analysis
(2-3 paragraphs synthesizing the findings with reasoning)

4. Conclusion
(1-2 sentences summarizing the main takeaway)

5. Sources Referenced
(List: Document name — Page number — Brief description)
"""


def run_rag_pipeline(query: str, api_key: str) -> dict:
    # ── Step 1: Input Guardrail ──────────────────────────────────────────────
    guard = check_input(query)
    if not guard["safe"]:
        return {
            "success": False,
            "error": guard["reason"],
            "threat_type": guard["threat_type"],
            "fallback": False
        }

    # ── Step 2: Vector Search — top 20 chunks ───────────────────────────────
    try:
        chunks = query_chunks(query, n_results=20)
    except Exception as e:
        return {"success": False, "error": f"Vector search failed: {str(e)}", "fallback": False}

    if not chunks:
        return {
            "success": False,
            "error": "No relevant documents found. Please upload documents first.",
            "fallback": False
        }

    # ── Step 3: FlashRank Reranking — keep top 5 ────────────────────────────
    try:
        passages = [{"id": i, "text": c["text"]} for i, c in enumerate(chunks)]
        rerank_request = RerankRequest(query=query, passages=passages)
        reranked = ranker.rerank(rerank_request)
        top_indices = [r["id"] for r in reranked[:5]]
        top_chunks = [chunks[i] for i in top_indices]
    except Exception:
        top_chunks = chunks[:5]

    # ── Step 4: Build context with metadata ─────────────────────────────────
    context = ""
    for i, chunk in enumerate(top_chunks):
        page = chunk["metadata"].get("page_number", "?")
        fname = chunk["metadata"].get("filename", "document")
        context += f"\n[Source {i+1} — {fname}, Page {page}]\n{chunk['text']}\n"

    # ── Step 5: CoT Prompt ───────────────────────────────────────────────────
    user_prompt = build_cot_prompt(query, context)

    # ── Step 6: Call OpenRouter with fallback ────────────────────────────────
    try:
        client = get_client(api_key)
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1800,
            temperature=0.2,
        )
        answer = response.choices[0].message.content

        # ── Step 7: Output Validation ────────────────────────────────────────
        validation = validate_output(answer, top_chunks)
        if not validation["valid"]:
            return {
                "success": True,
                "fallback": True,
                "answer": None,
                "chunks": top_chunks,
                "validation": validation,
                "warning": "⚠️ AI output could not be validated. Showing raw retrieved sources instead."
            }

        return {
            "success": True,
            "fallback": False,
            "answer": answer,
            "chunks": top_chunks,
            "validation": validation,
            "warning": None
        }

    except Exception as e:
        # ── API Fallback — never crash, show raw chunks ──────────────────────
        return {
            "success": True,
            "fallback": True,
            "answer": None,
            "chunks": top_chunks,
            "validation": None,
            "warning": f"⚠️ AI Service Unavailable. Showing retrieved sources directly. Error: {str(e)}"
        }
