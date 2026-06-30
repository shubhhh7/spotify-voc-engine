# Research Preparation Pipeline — Architecture Plan

## Executive Summary

This document describes a **fully free, locally-running** Python pipeline that transforms ~3,300 cleaned user reviews into LLM-ready cluster reports optimized for extracting Product Management insights about Spotify's music discovery, recommendation systems, and user behavior.

**Cost: $0 — No paid APIs required. Everything runs on your local machine.**

**Input:** `data/clean_v2/merged_reviews.csv` (3,294 reviews from 6 sources)  
**Output:** Cluster reports (JSON + Markdown) that an LLM can analyze for JTBD, user segments, frustrations, and product opportunities.

---

## Dataset Profile

| Metric | Value |
|--------|-------|
| Total Reviews | 3,294 |
| Sources | App Store (1,270), Reddit (861), Hackernews (512), Play Store (290), Spotify Community (248), Lemmy (113) |
| Primary Text Column | `text_clean` |
| Available Metadata | `id`, `source`, `rating`, `quality_score`, `text_length`, `word_count`, `date`, `country` |
| Avg Text Length | ~1,095 chars |
| Quality Score Range | 13–100 (mean: 54) |

---

## Project Structure

```
pipeline/
├── config.py                          # All configuration in one place
├── scripts/
│   ├── 01_generate_embeddings.py      # Step 1: Embed all reviews
│   ├── 02_cluster_reviews.py          # Step 2: Semantic clustering
│   ├── 03_cluster_statistics.py       # Step 3: Compute cluster stats
│   ├── 04_select_representatives.py   # Step 4: Pick representative reviews
│   └── 05_generate_reports.py         # Step 5: Produce final reports
├── utils/
│   ├── __init__.py
│   ├── embeddings.py                  # Embedding provider abstraction
│   ├── clustering.py                  # Clustering utilities
│   └── text_stats.py                  # Keyword/ngram extraction helpers
├── data/
│   └── clean_reviews.csv              # Input (symlink or copy of merged_reviews.csv)
├── output/
│   ├── embeddings.npy                 # Step 1 output
│   ├── embeddings_metadata.csv        # Step 1 output
│   ├── clustered_reviews.csv          # Step 2 output
│   ├── cluster_statistics.csv         # Step 3 output
│   ├── representative_reviews.csv     # Step 4 output
│   ├── cluster_index.csv             # Cross-reference index
│   └── cluster_reports/              # Step 5 output
│       ├── cluster_001.json
│       ├── cluster_001.md
│       ├── cluster_002.json
│       ├── cluster_002.md
│       └── ...
├── requirements.txt
└── README.md
```

---

## Step-by-Step Architecture

---

### STEP 1 — Generate Embeddings

**Script:** `scripts/01_generate_embeddings.py`

**Purpose:** Convert every review's text into a dense semantic vector for downstream clustering.

#### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Default Model | `BAAI/bge-large-en-v1.5` (local via sentence-transformers) | 100% free, runs locally, no API key needed, 1024-dim embeddings, top-tier quality |
| Fallback Model | `all-MiniLM-L6-v2` (local) | Lighter/faster if RAM is limited, 384-dim, still good quality |
| Text Field | `text_clean` | Already preprocessed, consistent |
| Batch Size | 64 | Memory-efficient on 16GB RAM (reduce to 32 if needed) |
| Max Token Length | 512 tokens | BGE optimal window; longer reviews get truncated intelligently |
| Cost | **$0** | Everything runs locally on your machine |

#### Algorithm

```
1. Load cleaned CSV
2. Extract text_clean column
3. Initialize embedding model (configurable via config.py)
4. Batch-encode all texts with progress bar
5. Save embeddings as numpy array (.npy)
6. Save metadata CSV (review_id, source, text_length, embedding_index)
7. Log stats: total embedded, avg embedding time, any failures
```

#### Provider Abstraction (All Free/Local)

```python
class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> np.ndarray: ...

class BGELargeProvider:       # Default — best quality, 1024-dim, ~2GB download
class MiniLMProvider:         # Fallback — faster, 384-dim, ~90MB download
class E5LargeProvider:        # Alternative — Microsoft's model, 1024-dim
```

All providers use `sentence-transformers` library and run entirely locally. No API keys, no costs, no rate limits.

#### Output Files

| File | Description |
|------|-------------|
| `output/embeddings.npy` | Shape: (3294, 1024) numpy array |
| `output/embeddings_metadata.csv` | Columns: `review_id`, `source`, `text_length`, `embedding_index`, `model_used` |

#### Validation Checklist

- [ ] `embeddings.npy` shape matches row count of input CSV
- [ ] No NaN values in embeddings
- [ ] Metadata CSV has same row count as embeddings
- [ ] Random cosine similarity check: semantically similar reviews have high similarity

#### Estimated Runtime

- Local (BGE-large, CPU): ~5–8 minutes for 3,294 reviews
- Local (BGE-large, GPU/MPS on Mac): ~30–60 seconds
- Local (MiniLM, CPU): ~1–2 minutes for 3,294 reviews

First run downloads the model (~2GB for BGE-large, ~90MB for MiniLM). Subsequent runs use the cached model.

---

### STEP 2 — Semantic Clustering

**Script:** `scripts/02_cluster_reviews.py`

**Purpose:** Group reviews by semantic meaning, preserving niche themes and allowing outliers.

#### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Algorithm | HDBSCAN | Finds variable-density clusters, handles noise, no preset k |
| Dimensionality Reduction | UMAP (pre-clustering) | Improves HDBSCAN performance on high-dim data |
| UMAP n_components | 50 | Preserves enough structure for fine-grained clusters |
| UMAP n_neighbors | 15 | Balance between local and global structure |
| HDBSCAN min_cluster_size | 8 | Preserves niche themes (min ~0.25% of data) |
| HDBSCAN min_samples | 5 | Allows slightly loose cluster boundaries |
| HDBSCAN cluster_selection_method | `eom` (Excess of Mass) | Better at finding clusters of varying sizes |
| Target Cluster Range | 40–150 clusters | Calibrated for ~3,300 reviews (not 50k) |

#### Algorithm

```
1. Load embeddings.npy
2. Apply UMAP reduction (1024-dim → 50-dim)
3. Run HDBSCAN on reduced embeddings
4. Extract cluster labels and probabilities
5. Identify outliers (label == -1)
6. If cluster count < 40: reduce min_cluster_size, re-run
7. If cluster count > 200: increase min_cluster_size, re-run
8. Assign each review: cluster_id, cluster_confidence, outlier_flag
9. Save clustered_reviews.csv
10. Log: cluster count, outlier count, size distribution
```

#### Adaptive Tuning Strategy

The pipeline will auto-tune HDBSCAN parameters if the initial clustering is too coarse or too fine:

```python
MIN_ACCEPTABLE_CLUSTERS = 40
MAX_ACCEPTABLE_CLUSTERS = 200
MAX_OUTLIER_RATIO = 0.30  # No more than 30% as outliers

# Iterative tuning loop:
# - Too few clusters → decrease min_cluster_size (down to 5)
# - Too many clusters → increase min_cluster_size (up to 20)
# - Too many outliers → decrease min_samples
```

#### Output Files

| File | Columns |
|------|---------|
| `output/clustered_reviews.csv` | All original columns + `cluster_id`, `cluster_confidence`, `outlier_flag`, `umap_x`, `umap_y` |

#### Validation Checklist

- [ ] Cluster count is in 40–150 range
- [ ] Outlier ratio is below 30%
- [ ] No single cluster has >15% of all reviews (over-merged check)
- [ ] Smallest clusters have at least 5 reviews
- [ ] Spot-check 5 random clusters: reviews in each are semantically coherent
- [ ] UMAP 2D visualization looks reasonable (save as PNG for inspection)

#### Why NOT BERTopic?

BERTopic wraps HDBSCAN + UMAP + c-TF-IDF. For this use case, keeping HDBSCAN/UMAP separate gives more control over:
- Cluster granularity tuning
- Outlier handling
- Custom representative selection logic

---

### STEP 3 — Cluster Statistics

**Script:** `scripts/03_cluster_statistics.py`

**Purpose:** Generate comprehensive statistical profiles for each cluster to support LLM analysis.

#### Statistics Computed Per Cluster

| Statistic | Method |
|-----------|--------|
| `cluster_id` | From Step 2 |
| `review_count` | Simple count |
| `pct_of_total` | count / total × 100 |
| `source_distribution` | JSON: `{"Reddit": 45, "App Store": 30, ...}` |
| `avg_rating` | Mean of `rating` column (where available) |
| `rating_distribution` | JSON: `{"1": 5, "2": 3, "3": 10, ...}` |
| `avg_quality_score` | Mean of `quality_score` column |
| `avg_text_length` | Mean of `text_length` |
| `top_keywords` | Top 15 single words (TF-IDF weighted, stopwords removed) |
| `top_bigrams` | Top 10 bigrams (frequency-based) |
| `top_trigrams` | Top 10 trigrams (frequency-based) |
| `date_range` | Earliest and latest review date in cluster |
| `avg_sentiment` | Derived from `sentiment_from_rating` or `rating` |

#### Text Analysis Approach

```python
# Keywords: TF-IDF within cluster vs. corpus
from sklearn.feature_extraction.text import TfidfVectorizer

# N-grams: CountVectorizer with ngram_range
from sklearn.feature_extraction.text import CountVectorizer

# Stopwords: English + domain-specific ("spotify", "app", "music", "song")
DOMAIN_STOPWORDS = ["spotify", "app", "music", "song", "songs", "listen", "listening"]
```

#### Output Files

| File | Description |
|------|-------------|
| `output/cluster_statistics.csv` | One row per cluster, all stats as columns |

#### Validation Checklist

- [ ] Every cluster_id from Step 2 appears in statistics
- [ ] No NaN in review_count or pct_of_total
- [ ] Percentages sum to ~100% (excluding outliers)
- [ ] Keywords are meaningful (not just stopwords)
- [ ] Spot-check: keywords align with actual review content in 3+ clusters

---

### STEP 4 — Representative Review Selection

**Script:** `scripts/04_select_representatives.py`

**Purpose:** Select 10–20 reviews per cluster that maximally represent the cluster's content and diversity.

#### Selection Algorithm (Multi-Criteria)

```
For each cluster:
  1. Compute cluster centroid (mean of cluster embeddings)
  2. Rank all reviews by cosine similarity to centroid → "centroid_distance"
  3. Compute information richness score:
     - text_length (normalized)
     - quality_score (from existing column)
     - specificity (unique terms ratio)
  4. Combined score = 0.4 × centroid_proximity + 0.3 × quality_score + 0.3 × richness
  5. Select top-5 by combined score (core representatives)
  6. Select remaining 5–15 using MMR (Maximal Marginal Relevance):
     - Iteratively pick reviews that are:
       a) Relevant to the cluster (high similarity to centroid)
       b) Different from already-selected reviews (low similarity to selections)
     - MMR_score = λ × sim(review, centroid) - (1-λ) × max_sim(review, selected)
     - λ = 0.6 (slight preference for relevance over diversity)
  7. Target count per cluster:
     - Clusters with <15 reviews: select min(count, 10)
     - Clusters with 15–50 reviews: select 12
     - Clusters with 50–100 reviews: select 15
     - Clusters with 100+ reviews: select 20
```

#### Output Files

| File | Columns |
|------|---------|
| `output/representative_reviews.csv` | `review_id`, `cluster_id`, `text_clean`, `source`, `rating`, `quality_score`, `selection_reason` (centroid/mmr), `rank_in_cluster` |

#### Validation Checklist

- [ ] Every non-outlier cluster has 10–20 representatives
- [ ] No duplicate review_ids across clusters
- [ ] `selection_reason` column shows mix of "centroid" and "mmr" 
- [ ] Spot-check: read 3 clusters' representatives — they should feel topically coherent but show different angles

---

### STEP 5 — Generate Cluster Reports

**Script:** `scripts/05_generate_reports.py`

**Purpose:** Produce self-contained reports per cluster in JSON and Markdown, ready for LLM consumption.

#### Report Structure (per cluster)

```json
{
  "cluster_id": 1,
  "cluster_size": 45,
  "percentage_of_total": 1.37,
  "source_distribution": {"Reddit": 20, "App Store": 15, "Play Store": 10},
  "rating_distribution": {"1": 5, "2": 8, "3": 12, "4": 10, "5": 10},
  "avg_rating": 3.2,
  "avg_quality_score": 62.4,
  "date_range": {"earliest": "2023-06-15", "latest": "2024-11-20"},
  "top_keywords": ["discover", "weekly", "playlist", "repeat", "algorithm"],
  "top_bigrams": ["discover weekly", "new music", "same songs"],
  "top_trigrams": ["discover weekly playlist", "same songs over"],
  "representative_reviews": [
    {
      "review_id": "reddit_abc123",
      "source": "Reddit",
      "rating": null,
      "quality_score": 78,
      "text": "Full review text here...",
      "selection_reason": "centroid"
    }
  ],
  "metadata": {
    "avg_text_length": 450,
    "total_word_count": 20250,
    "outlier_adjacent_count": 3
  }
}
```

#### Markdown Format

```markdown
# Cluster 001 — [Auto-generated label from top keywords]

## Overview
- **Size:** 45 reviews (1.37% of total)
- **Sources:** Reddit (20), App Store (15), Play Store (10)
- **Avg Rating:** 3.2/5
- **Date Range:** Jun 2023 – Nov 2024

## Key Themes
- **Keywords:** discover, weekly, playlist, repeat, algorithm
- **Bigrams:** discover weekly, new music, same songs
- **Trigrams:** discover weekly playlist, same songs over

## Representative Reviews

### Review 1 (Reddit, Quality: 78)
> "Full review text here..."

### Review 2 (App Store, Rating: 2/5, Quality: 65)
> "Full review text here..."

[... up to 20 reviews ...]

## Statistics
- Avg text length: 450 chars
- Total words: 20,250
```

#### Output Files

| Directory | Contents |
|-----------|----------|
| `output/cluster_reports/` | `cluster_001.json`, `cluster_001.md`, ... per cluster |
| `output/cluster_reports/index.json` | Summary index of all clusters |

#### Validation Checklist

- [ ] Every non-outlier cluster has both .json and .md files
- [ ] JSON files are valid (parseable)
- [ ] Markdown files render correctly
- [ ] Representative reviews in reports match `representative_reviews.csv`
- [ ] `index.json` contains all cluster IDs and their sizes

---

### STEP 6 (Bonus) — Cluster Index

**Generated alongside Step 5**

#### Output File: `output/cluster_index.csv`

| Column | Description |
|--------|-------------|
| `review_id` | Original review identifier |
| `cluster_id` | Assigned cluster (-1 for outliers) |
| `source` | Review source (Reddit, App Store, etc.) |
| `quality_score` | From cleaned data |
| `representative` | "Yes" or "No" |
| `selection_reason` | "centroid", "mmr", or null |
| `cluster_confidence` | HDBSCAN probability |
| `outlier_flag` | True/False |

This enables full traceability: from any insight → cluster report → representative review → original review → raw data.

---

## Configuration File

**`config.py`** — Single source of truth for all parameters:

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class PipelineConfig:
    # Paths
    input_csv: Path = Path("data/clean_reviews.csv")
    output_dir: Path = Path("output")
    
    # Embedding settings (all free, local models)
    embedding_model: str = "BAAI/bge-large-en-v1.5"  # or "all-MiniLM-L6-v2" (lighter)
    embedding_batch_size: int = 64  # reduce to 32 if RAM-constrained
    embedding_max_length: int = 512
    embedding_device: str = "cpu"  # or "mps" for Apple Silicon, "cuda" for NVIDIA
    
    # UMAP settings
    umap_n_components: int = 50
    umap_n_neighbors: int = 15
    umap_min_dist: float = 0.0
    umap_metric: str = "cosine"
    
    # HDBSCAN settings
    hdbscan_min_cluster_size: int = 8
    hdbscan_min_samples: int = 5
    hdbscan_cluster_selection_method: str = "eom"
    
    # Adaptive tuning
    min_acceptable_clusters: int = 40
    max_acceptable_clusters: int = 200
    max_outlier_ratio: float = 0.30
    
    # Representative selection
    representatives_lambda: float = 0.6  # MMR relevance vs diversity
    min_representatives: int = 10
    max_representatives: int = 20
    
    # Text analysis
    domain_stopwords: list = field(default_factory=lambda: [
        "spotify", "app", "music", "song", "songs", 
        "listen", "listening", "playlist", "playlists"
    ])
    top_keywords_count: int = 15
    top_bigrams_count: int = 10
    top_trigrams_count: int = 10
    
    # Processing
    random_seed: int = 42
    log_level: str = "INFO"
```

---

## Dependencies (requirements.txt)

All libraries are free and open-source. **No paid APIs required.**

```
# Embeddings (runs 100% locally)
sentence-transformers>=2.2.0
torch>=2.0.0

# Clustering
hdbscan>=0.8.33
umap-learn>=0.5.4

# Text Analysis
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0

# Utilities
tqdm>=4.65.0
python-dotenv>=1.0.0

# Visualization (optional, for validation)
matplotlib>=3.7.0
seaborn>=0.12.0
```

**Total cost: $0.** No OpenAI, Voyage, Cohere, or any other paid service needed.

---

## Execution Plan (Step-by-Step with Validation)

### Run Order

```bash
# Step 1: Generate embeddings (~5-8 min on CPU)
python scripts/01_generate_embeddings.py

# Validate Step 1:
python -c "import numpy as np; e=np.load('output/embeddings.npy'); print(f'Shape: {e.shape}, NaN: {np.isnan(e).sum()}')"

# Step 2: Cluster reviews (~30 sec)
python scripts/02_cluster_reviews.py

# Validate Step 2:
python -c "import pandas as pd; df=pd.read_csv('output/clustered_reviews.csv'); print(f'Clusters: {df.cluster_id.nunique()}, Outliers: {(df.outlier_flag==True).sum()}')"

# Step 3: Compute statistics (~5 sec)
python scripts/03_cluster_statistics.py

# Validate Step 3:
python -c "import pandas as pd; df=pd.read_csv('output/cluster_statistics.csv'); print(f'Stats for {len(df)} clusters, total pct: {df.pct_of_total.sum():.1f}%')"

# Step 4: Select representatives (~10 sec)
python scripts/04_select_representatives.py

# Validate Step 4:
python -c "import pandas as pd; df=pd.read_csv('output/representative_reviews.csv'); print(f'Total reps: {len(df)}, Clusters covered: {df.cluster_id.nunique()}')"

# Step 5: Generate reports (~10 sec)
python scripts/05_generate_reports.py

# Validate Step 5:
ls output/cluster_reports/ | wc -l
python -c "import json; idx=json.load(open('output/cluster_reports/index.json')); print(f'Index has {len(idx)} clusters')"
```

---

## Key Design Principles

### 1. Insight Preservation > Speed
- HDBSCAN `min_cluster_size=8` keeps small themes visible
- Outliers are preserved (not force-assigned)
- MMR selection ensures diverse perspectives within each cluster

### 2. Full Traceability
- `cluster_index.csv` maps every review to its cluster and role
- Representative reviews include `review_id` for lookup
- Original review text is included in reports (not just IDs)

### 3. LLM-Ready Output
- Each cluster report is self-contained (an LLM can analyze it without external data)
- Reports include both quantitative stats and qualitative evidence
- JSON format enables programmatic consumption; Markdown enables human review

### 4. Calibrated for ~3,300 Reviews
- Target 40–150 clusters (not 100–300, since we have 3.3k not 50k reviews)
- `min_cluster_size=8` means ~0.25% of data can form a valid cluster
- 10–20 representatives per cluster = significant coverage at this dataset size

### 5. Configurability & Zero Cost
- All embedding models run locally (no API keys, no rate limits, no costs)
- All HDBSCAN/UMAP parameters are in `config.py`
- Can re-run Steps 2–5 without regenerating embeddings
- Entire pipeline runs offline after initial model download (~2GB one-time)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Over-clustering (too many micro-clusters) | Adaptive tuning with `max_acceptable_clusters` ceiling |
| Under-clustering (merged topics) | Low `min_cluster_size`, manual inspection of large clusters |
| Embedding quality issues | Swap between BGE-large and MiniLM; both are free and local |
| Memory issues with large models | Batch processing, float16 option, or switch to MiniLM (90MB vs 2GB) |
| Outlier flood (>30%) | Reduce `min_samples`, adjust UMAP `n_neighbors` |
| Non-English text slipping through | `text_clean` already filtered; add language check as safety net |
| Slow on CPU | Use `device="mps"` on Apple Silicon Mac for 5-10x speedup |

---

## Post-Pipeline: LLM Analysis Preparation

Once the pipeline completes, the cluster reports are structured for an LLM to answer:

1. **"Why do users struggle to discover new music?"** → Look at clusters with keywords: discover, new, algorithm, recommendation
2. **"What recommendation frustrations exist?"** → Clusters with: repetitive, same, boring, stuck
3. **"What listening behaviors are users trying to achieve?"** → Clusters describing desired states, JTBD language
4. **"Why do users repeatedly listen to the same content?"** → Clusters about comfort, habit, algorithm reinforcement
5. **"Which user segments have different challenges?"** → Cross-reference source distribution + rating patterns
6. **"What unmet needs consistently emerge?"** → Clusters with feature requests, "I wish" language

The LLM would process `cluster_reports/index.json` first, then drill into individual cluster reports for evidence.

---

## Next Steps

1. **Implement Step 1** → Run → Validate embeddings
2. **Implement Step 2** → Run → Validate clusters (inspect UMAP plot)
3. **Implement Step 3** → Run → Validate statistics make sense
4. **Implement Step 4** → Run → Read representative reviews for quality check
5. **Implement Step 5** → Run → Spot-read 5 cluster reports end-to-end

Each step is independently runnable and validatable before proceeding to the next.
