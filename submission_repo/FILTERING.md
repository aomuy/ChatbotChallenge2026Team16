# Filtering and counting

Similarity search (`query`, `retrieve`) returns at most `k` chunks. Use
`filter_records` to fetch **all** matches or `count_records` to count them.
Both page through Chroma using `get`; they do not call the embedding API.
`batch_size` controls the size of each database request, not the total.

```python
from bot.store import get_store, filter_records, count_records

store = get_store()
posters = {"$and": [{"kind": "image"}, {"image_type": "poster"}]}

all_posters = filter_records(store, where=posters)
number_of_posters = count_records(store, where=posters, distinct_by="image")

posters_2025 = {"$and": [posters, {"year": 2025}]}
number_in_2025 = count_records(store, where=posters_2025, distinct_by="image")

# Text filtering matches records containing a phrase; it does not count
# occurrences of the phrase or prove the existence of physical objects.
mentions = filter_records(store, where_document={"$contains": "poster"})
```

`distinct_by="image"` counts unique image URLs. `distinct_by="url"` counts
unique web page URLs instead of overlapping text chunks. Omitting it counts
database records. A matched record missing the requested identity raises an
error. Pagination assumes the collection is not changing during the read.

`query` and `retrieve` also accept `where` and `where_document`; these filters
apply **before** the similarity result limit.

## Chatbot integration

`rag_answer` detects English and Chinese count questions and asks the model
to select a metadata filter. Python executes that filter against the full
collection and returns the deduplicated count directly; the model does not
compute the number from retrieved text. The planner currently supports
`image_type`, `page_type`, `year`, `location`, `category`, `capacity`, `url`,
`event_start`, and `event_end` when those fields exist. Extend `FILTER_FIELDS`
in `bot/counting.py` for other structured fields.

Event calendar questions use inclusive ISO intervals on pages:

```python
from bot.event_dates import (
    DEFAULT_YEAR, month_window, overlaps, filter_overlapping_records,
)
from bot.store import filter_records

# Chroma $gte/$lte only accept numbers, so ISO date overlap is applied in Python.
records = filter_records(store, where={"kind": "text"})
plan = {"window_start": "2026-03-01", "window_end": "2026-03-31", "mode": "overlap"}
march_events = filter_overlapping_records(records, plan)
```

Multi-day and multi-month events match every overlapping month; a span such as
August–September still counts each page once (dedupe by `url`). When the
user omits a year, the bot assumes `DEFAULT_YEAR` (2026). List questions
(“what events in March?”) use the same overlap filter instead of top‑k
similarity alone.

Counting image assets or pages differs from counting objects inside photos
or quantities stated in text. Those questions use the existing RAG path.
For count questions, its prompt explicitly forbids treating partial search
results as a total or guessing without sufficient evidence. Unsupported or
malformed filter plans also fall back to that path. `event_start` /
`event_end` are exempt from the “every row must have this field” completeness
check because most pages are not dated events.

## Metadata and rebuilding

No production `submission_repo/data/` directory was present when this
feature was added. Populate the source data before building an index.

The image ingestion prompt now produces a JSON description and an
`image_type` (`poster`, `photo`, `diagram`, `logo`, `map`, `signage`, `other`,
or `unknown`). A photo containing posters or signs is classified as `photo`,
not as a poster or signage asset.
Explicit `image_type` annotations in `data/images.json` take precedence:

```json
{
  "src": "https://example.org/open-day-poster.png",
  "page": "https://example.org/open-day",
  "image_type": "poster",
  "year": 2025,
  "location": "Innovation Wing"
}
```

Existing plain-text description caches remain readable and are not
automatically regenerated. For those entries, annotate `image_type` in
`images.json`, or deliberately regenerate the corresponding cached vision
descriptions. The code does not guess asset types from text mentions.

Scalar fields on source pages (for example `page_type`, numeric `capacity`,
and `year`) and source images are retained as metadata. Add these fields
explicitly to the source JSON; the scraper does not infer them. Use
consistent types, such as an integer year for every record. Each page URL
must represent one entity for page counts such as the number of venues.

Event dates are produced by an offline enrichment step that cross-checks
three sources (parsed `Date:` / `Dates:` text, HTML structured data from a
re-fetch, and a Qwen date-model extract). Agreed intervals are written as
`event_start` and `event_end` (ISO `YYYY-MM-DD`, inclusive; single-day ⇒
equal). Derived `year` / `month` fields are not written. Conflicts prefer
the text parse and are logged to `data/date_review.jsonl` together with hubs
and single-source hits. Pages where no source found a date go to
`data/date_missing.jsonl`. Images inherit `event_start` / `event_end` from
their parent page URL.

The enricher is **resumable**. Pages that already have `event_start`+
`event_end`, or an `event_date_status` (`hub` / `missing` / `single_source` /
`conflict`), are skipped. `--limit N` processes at most **N unfinished**
pages this run. To force a page to run again, delete `event_start`,
`event_end`, and `event_date_status` on that object in `pages.json`. On
Ctrl-C or when every Qwen date model is out of quota, the current
`pages.json` (and image inheritance) is saved and review/missing lines for
finished pages are appended (prior log lines are kept).

LLM date extraction uses `QWEN_AVAILABLE_DATE_MODELS` (comma-separated,
left to right). On quota/token exhaustion the next model is tried; if all
are exhausted the run checkpoints and exits.

```bash
python -m build.enrich_dates --limit 5
```

After updating source metadata, rebuild from `submission_repo`:

```bash
python -m build.enrich_dates
python -m build.index
python -m build.images
```

The first command resets the text/image index; the second repopulates image
records using cached descriptions where available. Both require the
embedding API. Running the image command alone on an existing index does
not update previously added IDs, so use the full rebuild sequence above.

Automatic counts conservatively require all records of the selected kind
(`image` or `text`) to have the identity and filter fields. Missing fields
or `unknown` classifications cause fallback rather than an understated
total. A numeric result covers indexed assets/pages; it does not guarantee
the crawl captured every real-world asset.

## Verification

```bash
python -m unittest discover -s tests -v
```

Tests use real in-memory Chroma collections with explicit embeddings and
mocked model responses, without API credentials or network calls. They
cover multi-page reads, duplicate image URLs, overlapping chunks, compound
and content filters, empty results, English/Chinese count routing,
incomplete metadata, physical-object fallback, and batch answer order.
