# Where to put your dataset

This directory should contain your **raw, unmodified** dataset. It's empty
by default (only this README is tracked in git) so the real dataset is
never committed to version control.

## Option A — Kaggle "Fake and Real News Dataset" layout

Download `Fake.csv` and `True.csv` and place both files directly here:

```
data/raw/Fake.csv
data/raw/True.csv
```

The loader (`src/data/loader.py`) auto-detects this layout: every row in
`Fake.csv` is labeled FAKE, every row in `True.csv` is labeled REAL.

## Option B — a single CSV (or several) with title/text/label columns

```
data/raw/news.csv
```

```csv
title,text,label
"Some headline","Full article body...",REAL
"Another headline","Full article body...",FAKE
```

Column names are auto-detected, case-insensitively:
- **title**: `title`, `headline`, `news_title`, `head`
- **text**: `text`, `article`, `content`, `body`, `news_text`, `articles`, `statement`
- **label**: `label`, `class`, `target`, `type`, `news_type`

Label values `1`/`0`, `"FAKE"`/`"REAL"` (any case), `true`/`false`, and
`reliable`/`unreliable` are all understood.

## The LIAR dataset

LIAR ships as headerless `.tsv` files with a 6-way truthfulness label
(`pants-fire`, `false`, `barely-true`, `half-true`, `mostly-true`, `true`).
This loader reads `.tsv` files too, but you'll need to collapse those 6
labels into binary REAL/FAKE yourself first — for example:

```python
import pandas as pd

columns = ["id", "label", "statement", "subject", "speaker", "job", "state",
           "party", "barely_true_ct", "false_ct", "half_true_ct",
           "mostly_true_ct", "pants_fire_ct", "context"]
df = pd.read_csv("train.tsv", sep="\t", header=None, names=columns)

fake_labels = {"false", "pants-fire", "barely-true"}
df["label"] = df["label"].apply(lambda l: "FAKE" if l in fake_labels else "REAL")
df[["statement", "label"]].rename(columns={"statement": "text"}).to_csv(
    "data/raw/liar.csv", index=False
)
```

## Don't have a dataset yet?

`data/sample/sample_news.csv` ships with this project — a small, clearly
synthetic set of examples good for sanity-checking that the pipeline runs
end to end (`python train.py --data-dir data/sample`). **Do not treat any
metrics from that run as real performance numbers** — the sample is far too
small and stylistically simplistic to mean anything; it exists only to
prove the code works before you plug in a real dataset.

Once your real data is here, run:

```
python train.py
```
