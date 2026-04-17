# CiteSight 🔍
### Generative Information Retrieval for Science - Web App & API

> A SaaS platform for citation-accurate scientific search, built on Retrieval-Augmented Generation (RAG).
> Every factual claim in CiteSight's answers is directly traceable to a real retrieved paper — hallucinated citations are architecturally impossible.
> 
> **Now featuring a beautiful web interface** for intuitive research exploration alongside a powerful REST API for developers.

**Live demo:** https://sc4052-cloud-project-citesight.onrender.com

> ⚠️ **First request may take ~30 seconds** — the free hosting tier sleeps after 15 minutes of inactivity. Just wait for it to wake up, then it responds instantly.

---

## What CiteSight Does

Most AI tools (ChatGPT, Gemini, etc.) generate research answers from memory — and frequently **fabricate citations**. Titles, authors, and DOIs that sound real but don't exist. Studies show citation accuracy of 43–71% across commercial AI research tools.

CiteSight fixes this by **retrieving real papers first**, then generating answers using only those retrieved papers as context. If CiteSight can't find a relevant paper, it tells you — it never invents one.

---

## ✨ Web Interface Features

CiteSight now includes a modern, user-friendly web interface alongside its API:

- **🏠 Home Page:** Professional dashboard with search functionality and quick action buttons
- **🔍 Smart Search:** Ask research questions directly through an intuitive search box
- **📚 Paper Management:** Browse all papers with organized metadata and abstracts
- **📥 Intelligent Fetching:** Fetch new papers from arXiv with duplicate detection and status indicators
- **❤️ Health Monitoring:** Real-time system status and knowledge base statistics
- **📱 Responsive Design:** Works seamlessly on desktop and mobile devices

The web interface makes CiteSight accessible to non-technical users while maintaining full API compatibility for developers.

---

## Web Interface — Try It Now

CiteSight now features a beautiful web interface! Open these URLs directly in your browser (replace the base URL with your own Render URL if self-hosting):

| What you want to do | URL |
|---|---|
| **Home Page** - Search questions, quick actions | `https://sc4052-cloud-project-citesight.onrender.com/` |
| Ask a research question | `https://sc4052-cloud-project-citesight.onrender.com/query?q=how+do+transformers+work` |
| Ask with more results | `https://sc4052-cloud-project-citesight.onrender.com/query?q=hallucination+in+llms&k=5` |
| Fetch real papers from arXiv | `https://sc4052-cloud-project-citesight.onrender.com/fetch?topic=large+language+models` |
| See all papers in knowledge base | `https://sc4052-cloud-project-citesight.onrender.com/papers` |
| Health check | `https://sc4052-cloud-project-citesight.onrender.com/health` |

### What You'll See

- **Home Page:** Professional interface with search box, quick action buttons, and knowledge base stats
- **Query Results:** Formatted answers with collapsible citations, relevance scores, and confidence indicators
- **Papers List:** Organized display of all papers with abstracts and metadata
- **Fetch Results:** Shows fetched papers with "Newly added" or "Already included" status badges
- **Health Dashboard:** System status and knowledge base statistics

### API Endpoints Still Available

The original JSON API endpoints are still functional for programmatic access:

```json
GET /query?q=your+question
GET /papers
GET /fetch?topic=topic+name
GET /health
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
├── app.py              # Full Flask application — retrieval engine + web interface
├── templates/          # HTML templates for web interface
│   ├── index.html      # Home page with search and quick actions
│   ├── query.html      # Query results with citations
│   ├── papers.html     # Papers list display
│   ├── fetch.html      # Fetch results with status indicators
│   └── health.html     # Health dashboard
├── requirements.txt    # Python dependencies (flask, requests, gunicorn)
├── render.yaml         # Render.com deployment config
├── Procfile            # Gunicorn startup instruction
└── README.md           # This file
```

---

## Run Locally

**Step 1 — Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 2 — Start the server**
```bash
python app.py
```

**Step 3 — Open your browser to the web interface**
```
http://localhost:5000/                    # Home page with search interface
http://localhost:5000/query?q=transformer+attention  # Direct query
http://localhost:5000/fetch?topic=large+language+models  # Fetch papers
```

The web interface provides an intuitive way to interact with CiteSight without needing to construct URLs manually. Use the search box on the home page or the quick action buttons for the best experience!

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

To expand the knowledge base with real papers from arXiv on any topic, use the web interface or call:
```
/fetch?topic=your+topic+here
```

The web interface provides visual feedback showing which papers are newly added vs. already included in your knowledge base.

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
