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
`image_type`, `page_type`, `year`, `location`, `category`, `capacity`, and `url`
when those fields exist. Extend `FILTER_FIELDS` in `bot/counting.py` for
other structured fields.

Counting image assets or pages differs from counting objects inside photos
or quantities stated in text. Those questions use the existing RAG path.
For count questions, its prompt explicitly forbids treating partial search
results as a total or guessing without sufficient evidence. Unsupported or
malformed filter plans also fall back to that path.

## Metadata and rebuilding

No production `submission_repo/data/` directory was present when this
feature was added. Populate the source data before building an index.

The image ingestion prompt now produces a JSON description and an
`image_type` (`poster`, `photo`, `diagram`, `logo`, `other`, or `unknown`). A
photo containing posters is classified as `photo`, not as a poster asset.
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

After updating source metadata, rebuild from `submission_repo`:

```bash
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
