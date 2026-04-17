import re
import math
import json
import time
import urllib.request
import urllib.parse
import requests
from collections import Counter, defaultdict
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Patch jsonify to always pretty-print JSON responses
original_jsonify = jsonify
def jsonify(*args, **kwargs):
    response = original_jsonify(*args, **kwargs)
    response.set_data(json.dumps(response.get_json(), indent=2, sort_keys=False).encode('utf-8'))
    return response

# Start with a small hardcoded knowledge base of influential papers in ML/NLP.
PAPERS = [
    {
        "id": "P001", "title": "Attention Is All You Need",
        "authors": "Vaswani et al.", "year": 2017, "venue": "NeurIPS",
        "abstract": (
            "We propose a new simple network architecture, the Transformer, based solely on "
            "attention mechanisms, dispensing with recurrence and convolutions entirely. "
            "Experiments on two machine translation tasks show these models are superior in quality, "
            "more parallelizable, and require significantly less time to train. The Transformer achieves "
            "28.4 BLEU on the WMT 2014 English-to-German translation task."
        ),
    },
    {
        "id": "P002", "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "authors": "Devlin et al.", "year": 2019, "venue": "NAACL",
        "abstract": (
            "We introduce BERT, which stands for Bidirectional Encoder Representations from Transformers. "
            "Unlike recent language representation models, BERT is designed to pre-train deep bidirectional "
            "representations from unlabeled text. BERT obtains new state-of-the-art results on eleven NLP "
            "tasks, including pushing the GLUE score to 80.5%."
        ),
    },
    {
        "id": "P003", "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "authors": "Lewis et al.", "year": 2020, "venue": "NeurIPS",
        "abstract": (
            "We explore a general-purpose fine-tuning recipe for retrieval-augmented generation (RAG) "
            "models where the parametric memory is a pre-trained seq2seq model and the non-parametric "
            "memory is a dense vector index of Wikipedia. RAG models generate more specific, diverse, "
            "and factual language than a state-of-the-art parametric-only seq2seq baseline."
        ),
    },
    {
        "id": "P004", "title": "GPT-4 Technical Report",
        "authors": "OpenAI", "year": 2023, "venue": "arXiv",
        "abstract": (
            "We report the development of GPT-4, a large multimodal model which accepts image and text "
            "inputs and produces text outputs. GPT-4 exhibits human-level performance on various "
            "professional and academic benchmarks, including scoring in the top 10% on the bar exam."
        ),
    },
    {
        "id": "P005", "title": "Hallucination in Large Language Models: A Survey",
        "authors": "Ji et al.", "year": 2023, "venue": "ACM Computing Surveys",
        "abstract": (
            "Large language models (LLMs) have shown impressive capabilities but also exhibit a "
            "tendency to hallucinate — generating content that is factually incorrect or not grounded "
            "in the provided sources. This survey categorizes hallucination into intrinsic and extrinsic "
            "types and reviews mitigation strategies including retrieval augmentation and RLHF."
        ),
    },
    {
        "id": "P006", "title": "Scaling Laws for Neural Language Models",
        "authors": "Kaplan et al.", "year": 2020, "venue": "arXiv",
        "abstract": (
            "We study empirical scaling laws for language model performance on the cross-entropy loss. "
            "The loss scales as a power-law with model size, dataset size, and the amount of compute "
            "used for training, with some trends spanning more than seven orders of magnitude."
        ),
    },
    {
        "id": "P007", "title": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
        "authors": "Wei et al.", "year": 2022, "venue": "NeurIPS",
        "abstract": (
            "We explore how generating a chain of thought — a series of intermediate reasoning steps — "
            "significantly improves the ability of large language models to perform complex reasoning "
            "tasks, including arithmetic, commonsense, and symbolic reasoning."
        ),
    },
    {
        "id": "P008", "title": "Constitutional AI: Harmlessness from AI Feedback",
        "authors": "Bai et al.", "year": 2022, "venue": "arXiv",
        "abstract": (
            "We propose Constitutional AI (CAI), a method for training AI systems to be helpful, "
            "harmless, and honest using a set of principles and AI-generated feedback, reducing "
            "reliance on human labels for harmful outputs."
        ),
    },
]

# To fetch real papers, we call the arXiv API. This function handles that logic.

def fetch_from_arxiv(topic: str, max_results: int = 5) -> list:
    """
    Search arXiv for papers matching `topic`.
    Returns a list of paper dicts ready to add to PAPERS.

    How it works:
      - We call the free arXiv API: https://export.arxiv.org/api/query
      - It returns XML with paper titles, authors, abstracts, IDs
      - We parse it and add papers to our knowledge base
    """
    print(f"[arXiv] Fetching papers for topic: '{topic}'...")

    # Build the arXiv API URL
    encoded_topic = urllib.parse.quote(topic)
    url = (
        f"https://export.arxiv.org/api/query"
        f"?search_query=all:{encoded_topic}"
        f"&start=0"
        f"&max_results={max_results}"
        f"&sortBy=relevance"
    )

    headers = {
        'User-Agent': 'CiteSight/1.0 (tanj0314@student.edu.sg)' 
    }


    xml_data = None
    # Retry loop: attempt the request up to 3 times if rate-limited
    for attempt in range(3):
        try:
            # arXiv policy: Wait 3 seconds between requests
            time.sleep(3) 
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()  # Raise an exception for bad status codes
            xml_data = response.text
            break # Success! Exit the retry loop
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"[arXiv] Rate limited (429). Waiting longer... (Attempt {attempt+1})")
                time.sleep(5) # Extra wait on 429
                continue
            return {"error": f"arXiv HTTP Error {e.response.status_code}: {e.response.reason}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Could not reach arXiv: {str(e)}"}

    if not xml_data:
        return {"error": "Failed to retrieve data after retries."}

    # Parse the XML response — we use simple regex since it's structured
    entries = re.findall(r"<entry>(.*?)</entry>", xml_data, re.DOTALL)

    fetched = []
    existing_titles = {p["title"].lower() for p in PAPERS}

    for i, entry in enumerate(entries):
        # Extract fields using regex
        title_match   = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
        summary_match = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
        year_match    = re.search(r"<published>(\d{4})", entry)
        id_match      = re.search(r"<id>.*?abs/([^<]+)</id>", entry)

        # Extract all author names
        author_names  = re.findall(r"<name>(.*?)</name>", entry)

        if not title_match or not summary_match:
            continue

        title    = title_match.group(1).strip().replace("\n", " ")
        abstract = summary_match.group(1).strip().replace("\n", " ")
        year     = int(year_match.group(1)) if year_match else 2024
        arxiv_id = id_match.group(1).strip() if id_match else f"arxiv_{i}"

        # Format authors: "Smith, Jones, Lee et al."
        if len(author_names) > 2:
            authors = f"{author_names[0].split(',')[0]} et al."
        elif author_names:
            authors = " & ".join(a.split(",")[0] for a in author_names[:2])
        else:
            authors = "Unknown"

        # Skip duplicates
        if title.lower() in existing_titles:
            continue

        paper = {
            "id":       f"ARX{len(PAPERS) + len(fetched) + 1:03d}",
            "title":    title,
            "authors":  authors,
            "year":     year,
            "venue":    "arXiv",
            "abstract": abstract,
            "arxiv_id": arxiv_id,
        }
        fetched.append(paper)
        existing_titles.add(title.lower())

    # Add new papers to global knowledge base
    PAPERS.extend(fetched)
    print(f"[arXiv] Added {len(fetched)} new papers. Total in knowledge base: {len(PAPERS)}")
    return fetched


# TD-IDF VECTOR INDEXER — This is the "retriever" part of RAG. It finds relevant papers based on the query.

def tokenize(text: str) -> list:
    """Split text into lowercase words, removing short/common words."""
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    stopwords = {"the","and","for","are","was","has","have","with","that",
                 "this","from","its","not","but","they","their","been","more",
                 "also","can","which","than","our","we","in","of","to","a",
                 "is","it","on","as","by","an","at","be","or","do","if",
                 "we","us","all","any","one","two","new","use","used","using"}
    return [w for w in words if w not in stopwords]

def build_index(papers: list) -> tuple:
    """
    Build TF-IDF index over all papers.
    Returns (tfidf_index, idf_dict).
    """
    N = len(papers)
    df = defaultdict(int)
    tf_docs = []

    for paper in papers:
        # Combine title (weighted x3 for importance) + abstract
        text = (paper["title"] + " ") * 3 + paper["abstract"]
        tokens = tokenize(text)
        tf = Counter(tokens)
        total = sum(tf.values()) + 1e-9
        tf_norm = {t: c / total for t, c in tf.items()}
        tf_docs.append(tf_norm)
        for t in tf_norm:
            df[t] += 1

    # IDF: rare terms across the corpus get higher weight
    idf = {t: math.log((N + 1) / (df[t] + 1)) + 1 for t in df}

    # Final TF-IDF vectors
    tfidf = [{t: w * idf.get(t, 1) for t, w in doc.items()} for doc in tf_docs]
    return tfidf, idf

def cosine_sim(v1: dict, v2: dict) -> float:
    """Cosine similarity between two TF-IDF vectors."""
    keys = set(v1) & set(v2)
    if not keys:
        return 0.0
    dot    = sum(v1[k] * v2[k] for k in keys)
    norm1  = math.sqrt(sum(x**2 for x in v1.values()))
    norm2  = math.sqrt(sum(x**2 for x in v2.values()))
    return dot / (norm1 * norm2 + 1e-9)

def retrieve(query: str, top_k: int = 3) -> list:
    """
    Given a user query, return the top_k most relevant papers.
    Rebuilds the index fresh each call (fine for small corpora).
    """
    tfidf_index, idf = build_index(PAPERS)

    # Vectorize the query the same way we vectorized papers
    q_tokens = tokenize(query)
    total    = len(q_tokens) + 1e-9
    q_tf     = Counter(q_tokens)
    q_vec    = {t: (c / total) * idf.get(t, 1) for t, c in q_tf.items()}

    # Score every paper
    scores = [
        (cosine_sim(q_vec, doc_vec), PAPERS[i])
        for i, doc_vec in enumerate(tfidf_index)
    ]
    scores.sort(key=lambda x: -x[0])

    # Return only results with non-zero similarity
    return [(score, paper) for score, paper in scores[:top_k] if score > 0.001]

# ANSWER GENERATOR — This is the "generator" part of RAG. It builds a grounded answer from retrieved papers.

def generate_answer(query: str, retrieved: list) -> dict:
    """
    Build a grounded answer from retrieved papers.

    Every sentence in the answer comes directly from a retrieved paper's
    abstract and is labeled with that paper's ID.

    In production: replace this with a call to the Claude/OpenAI API,
    passing the retrieved abstracts as context. The logic here simulates
    what the LLM would do — constrained generation from retrieved sources.
    """
    if not retrieved:
        return {
            "answer":         "No relevant papers found in the knowledge base for your query.",
            "citations":      [],
            "confidence":     "low",
        }

    answer_parts = [f"Based on the retrieved literature, here is what is known about: '{query}'\n"]
    citations    = []

    for score, paper in retrieved:
        # Extract first 2 sentences from the abstract as the grounded excerpt
        sentences = re.split(r'(?<=[.!?])\s+', paper["abstract"])
        excerpt   = " ".join(sentences[:2])

        answer_parts.append(f"[{paper['id']}] {excerpt}")
        citations.append({
            "id":              paper["id"],
            "title":           paper["title"],
            "authors":         paper["authors"],
            "year":            paper["year"],
            "venue":           paper["venue"],
            "relevance_score": round(score, 4),
            "arxiv_id":        paper.get("arxiv_id", None),
        })

    answer_parts.append(
        f"\n[{len(retrieved)} paper(s) retrieved. "
        "All claims above are traceable to the cited sources.]"
    )

    # Confidence based on top-1 relevance score
    top_score  = retrieved[0][0]
    confidence = "high" if top_score > 0.3 else "medium" if top_score > 0.1 else "low"

    return {
        "answer":         "\n\n".join(answer_parts),
        "citations":      citations,
        "confidence":     confidence,
        "top_score":      round(top_score, 4),
    }


# Flask API ENDPOINTS — This is the web server part. It defines routes for querying, listing papers, fetching new papers, and health checks.
# The SaaS part of RAG — it exposes the retrieval and generation functionality as a web service.

@app.route("/")
def home():
    """Welcome page — shows available routes and provides a simple web interface."""
    return render_template('index.html', papers_count=len(PAPERS))


@app.route("/query")
def query():
    """
    MAIN ENDPOINT — Ask a research question.

    Usage:
        http://localhost:5000/query?q=what+causes+hallucination+in+llms
        http://localhost:5000/query?q=transformer+attention&k=5

    What happens:
        1. Your question is vectorized using TF-IDF
        2. Top-k most similar papers are retrieved
        3. An answer is generated using ONLY those papers
        4. You get back: answer text + full citation list + confidence level
    """
    q = request.args.get("q", "").strip()
    k = int(request.args.get("k", 3))

    if not q:
        return render_template('query.html', error="Please provide a query. Example: /query?q=transformer+attention"), 400

    retrieved = retrieve(q, top_k=k)
    result    = generate_answer(q, retrieved)

    return render_template('query.html',
        query=q,
        retrieved_count=len(retrieved),
        confidence=result["confidence"],
        top_relevance=result.get("top_score", 0),
        answer=result["answer"],
        citations=result["citations"]
    )


@app.route("/papers")
def list_papers():
    """
    List all papers currently in the knowledge base.

    Usage:
        http://localhost:5000/papers
    """
    return render_template('papers.html', papers=PAPERS)


@app.route("/fetch")
def fetch_papers():
    """
    Fetch REAL papers from arXiv and add them to the knowledge base.

    Usage:
        http://localhost:5000/fetch?topic=large+language+models
        http://localhost:5000/fetch?topic=neural+networks&n=3

    What happens:
        - CiteSight calls the free arXiv.org API
        - Downloads real paper titles + abstracts matching your topic
        - Adds them to the knowledge base
        - Future /query calls will now search these real papers too
    """
    topic = request.args.get("topic", "").strip()
    n     = int(request.args.get("n", 5))

    if not topic:
        return render_template('fetch.html', error="Please provide a topic. Example: /fetch?topic=transformer+attention"), 400

    fetched = fetch_from_arxiv(topic, max_results=n)

    if isinstance(fetched, dict) and "error" in fetched:
        return render_template('fetch.html', error=fetched["error"]), 503

    # Check which papers are new vs already existing
    existing_titles = {p["title"] for p in PAPERS}
    papers_with_status = []
    for paper in fetched:
        status = "Already included" if paper["title"] in existing_titles else "Newly added"
        papers_with_status.append({**paper, "status": status})

    # If no papers were fetched (all duplicates), show a message
    if not papers_with_status:
        return render_template('fetch.html', topic=topic, message="All papers for this topic are already in the knowledge base.")

    return render_template('fetch.html', topic=topic, papers=papers_with_status)


@app.route("/health")
def health():
    """Quick health check."""
    import time
    return render_template('health.html',
        status="OK ✅",
        papers_count=len(PAPERS),
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    )


# Run the Flask app. In production, use a WSGI server like Gunicorn instead of app.run().

if __name__ == "__main__":
    print("=" * 60)
    print("  CiteSight — Starting server...")
    print("=" * 60)
    print(f"  Knowledge base loaded: {len(PAPERS)} papers")
    print()
    print("  Open your browser and try:")
    print("    http://localhost:5000/")
    print("    http://localhost:5000/query?q=how+do+transformers+work")
    print("    http://localhost:5000/fetch?topic=large+language+models")
    print("    http://localhost:5000/papers")
    print()
    print("  Press Ctrl+C to stop the server.")
    print("=" * 60)

    import os
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(debug=debug, host="0.0.0.0", port=port)
