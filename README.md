# CiteSight 🔍
### Generative Information Retrieval for Science

> A SaaS platform for citation-accurate scientific search, built on Retrieval-Augmented Generation (RAG).
> Every factual claim in CiteSight's answers is directly traceable to a real retrieved paper — hallucinated citations are architecturally impossible.

**Live demo:** https://citesight.onrender.com

> ⚠️ **First request may take ~30 seconds** — the free hosting tier sleeps after 15 minutes of inactivity. Just wait for it to wake up, then it responds instantly.

---

## What CiteSight Does

Most AI tools (ChatGPT, Gemini, etc.) generate research answers from memory — and frequently **fabricate citations**. Titles, authors, and DOIs that sound real but don't exist. Studies show citation accuracy of 43–71% across commercial AI research tools.

CiteSight fixes this by **retrieving real papers first**, then generating answers using only those retrieved papers as context. If CiteSight can't find a relevant paper, it tells you — it never invents one.

---

## Live API — Try It Now

Open these URLs directly in your browser (replace the base URL with your own Render URL if self-hosting):

| What you want to do | URL |
|---|---|
| Welcome + route list | `https://citesight.onrender.com/` |
| Ask a research question | `https://citesight.onrender.com/query?q=how+do+transformers+work` |
| Ask with more results | `https://citesight.onrender.com/query?q=hallucination+in+llms&k=5` |
| Fetch real papers from arXiv | `https://citesight.onrender.com/fetch?topic=large+language+models` |
| See all papers in knowledge base | `https://citesight.onrender.com/papers` |
| Health check | `https://citesight.onrender.com/health` |

### Example response from `/query`

```json
{
  "query": "what causes hallucination in language models",
  "retrieved_count": 3,
  "confidence": "high",
  "top_relevance": 0.529,
  "answer": "Based on the retrieved literature...\n\n[P005] Large language models exhibit a tendency to hallucinate — generating content that is factually incorrect...",
  "citations": [
    {
      "id": "P005",
      "title": "Hallucination in Large Language Models: A Survey",
      "authors": "Ji et al.",
      "year": 2023,
      "venue": "ACM Computing Surveys",
      "relevance_score": 0.529
    }
  ]
}
```

---

## How It Works

CiteSight follows a **Retrieve → Inject → Generate** pipeline:

```
User query
    ↓
TF-IDF vectorization
    ↓
Cosine similarity ranking against indexed papers
    ↓
Top-k most relevant papers selected
    ↓
Paper abstracts injected into LLM context
    ↓
Grounded answer — every claim labeled with a paper ID ✅
```

The key architectural guarantee: the LLM only sees retrieved papers. It **cannot** generate a claim about a paper that was not retrieved. Citation hallucination is structurally prevented, not just discouraged.

---

## Project Structure

```
citesight/
├── app.py              # Full Flask application — retrieval engine + API
├── requirements.txt    # Python dependencies (flask, requests, gunicorn)
├── render.yaml         # Render.com deployment config
├── Procfile            # Gunicorn startup instruction
└── README.md           # This file
```

---

## Run Locally

**Step 1 — Install dependencies**
```bash
pip install flask requests
```

**Step 2 — Start the server**
```bash
python app.py
```

**Step 3 — Open your browser**
```
http://localhost:5000/
http://localhost:5000/query?q=transformer+attention
http://localhost:5000/fetch?topic=large+language+models
```

---

## Deploy Your Own Instance (Free)

This app is ready to deploy on [Render.com](https://render.com) for free — no credit card required.

1. Fork or clone this repo to your own GitHub account
2. Go to [render.com](https://render.com) → sign in with GitHub
3. Click **New +** → **Web Service** → select this repo
4. Render auto-detects `render.yaml` and configures everything
5. Click **Deploy** — your live URL is ready in ~3 minutes

> **Note on free tier inactivity:** Render's free tier puts the server to sleep after **15 minutes of no requests**. The next request after sleeping takes ~30 seconds to respond while the server wakes up. After that, it responds instantly. This is normal behaviour for the free tier and is fine for demos and testing.
>
> You do **not** need to keep the server manually running — it stays deployed indefinitely. It just sleeps when idle. Anyone can wake it by making any request to the URL.

---

## Knowledge Base

CiteSight ships with 8 foundational AI/NLP papers pre-loaded:

| ID | Title | Authors | Year |
|---|---|---|---|
| P001 | Attention Is All You Need | Vaswani et al. | 2017 |
| P002 | BERT: Pre-training of Deep Bidirectional Transformers | Devlin et al. | 2019 |
| P003 | Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks | Lewis et al. | 2020 |
| P004 | GPT-4 Technical Report | OpenAI | 2023 |
| P005 | Hallucination in Large Language Models: A Survey | Ji et al. | 2023 |
| P006 | Scaling Laws for Neural Language Models | Kaplan et al. | 2020 |
| P007 | Chain-of-Thought Prompting Elicits Reasoning in LLMs | Wei et al. | 2022 |
| P008 | Constitutional AI: Harmlessness from AI Feedback | Bai et al. | 2022 |

To expand the knowledge base with real papers from arXiv on any topic, call:
```
/fetch?topic=your+topic+here
```

---

## API Reference

### `GET /query`
Ask a research question and receive a grounded answer with citations.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `q` | string | required | Your research question |
| `k` | integer | 3 | Number of papers to retrieve |

**Response fields:**
- `answer` — generated text, with each claim prefixed by `[PAPER_ID]`
- `citations` — array of retrieved papers with full metadata and relevance scores
- `confidence` — `"high"` (score > 0.3), `"medium"` (> 0.1), or `"low"`
- `retrieved_count` — number of papers returned

---

### `GET /fetch`
Pull real papers from arXiv and add them to the knowledge base.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `topic` | string | required | Topic to search on arXiv |
| `n` | integer | 5 | Number of papers to fetch |

---

### `GET /papers`
List all papers currently in the knowledge base.

---

### `GET /health`
Returns server status and total indexed paper count.

---

## References

This project addresses the provenance problem in AI-assisted scientific writing, as described in:

- Earp, B. D. et al. (2025). *LLM use in scholarly writing poses a provenance problem.* Nature Machine Intelligence.
- Gibney, E. (2026). *Open-source AI tool beats giant LLMs in literature reviews.* Nature.
- Venkit, P. N. et al. (2026). *DeepTRACE: Auditing Deep Research AI Systems.* arXiv:2509.04499.
- Lewis, P. et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* NeurIPS.
- Ji, Z. et al. (2023). *Survey of Hallucination in Natural Language Generation.* ACM Computing Surveys.

---

*Cloud Computing Project — Topic 5: Generative Information Retrieval for Science*
