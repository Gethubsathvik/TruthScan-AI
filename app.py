"""
Streamlit UI for the Fake News Detection System.

Run with:  streamlit run app.py
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.models.predict import EmptyInputError, ModelNotFoundError, PredictionService
from src.utils.config import config

st.set_page_config(page_title="Fake News Detection System", page_icon="📰", layout="wide")


@st.cache_resource(show_spinner="Loading model...")
def load_service() -> PredictionService:
    return PredictionService(config=config)


def get_service_or_stop() -> PredictionService:
    try:
        return load_service()
    except ModelNotFoundError as exc:
        st.error(str(exc))
        st.info("From the project root, run:  `python train.py`  (after placing your dataset in `data/raw/`).")
        st.stop()


def render_disclaimer() -> None:
    st.info(
        "⚠️ **Disclaimer:** This tool is a machine-learning text classifier, not an "
        "authoritative fact-checker. It detects statistical language patterns learned "
        "from a training dataset and can be wrong — always verify important claims "
        "against trusted, independent sources."
    )


def render_confidence_badge(level: str) -> None:
    icons = {"High": "🟢", "Medium": "🟡", "Low": "🔴", "Unknown": "⚪"}
    st.write(f"{icons.get(level, '⚪')} **{level} confidence**")


def page_home() -> None:
    st.title("📰 Fake News Detection System")
    st.caption("AI-powered NLP classification of news headlines & articles")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("The problem")
        st.write(
            "Misinformation spreads fast, and manually fact-checking every headline "
            "doesn't scale. This project explores how far text *pattern recognition* "
            "— not fact verification — can go toward flagging content worth a "
            "closer look."
        )
        st.subheader("The solution")
        st.write(
            "A classical NLP pipeline (TF-IDF over cleaned text, plus stylistic "
            "signals like punctuation and capitalization) feeds four candidate "
            "classifiers; the best performer on a held-out validation set is "
            "the one deployed here."
        )
    with col2:
        st.subheader("Technology")
        st.markdown(
            "- **NLP:** cleaning, tokenization, stopword removal, lemmatization\n"
            "- **Features:** TF-IDF (uni/bi-grams) + stylistic numeric features\n"
            "- **Models:** Logistic Regression, Naive Bayes, Linear SVM, "
            "Passive-Aggressive Classifier\n"
            "- **Serving:** this Streamlit UI + a FastAPI REST endpoint, sharing "
            "one prediction service\n"
        )
        st.subheader("Limitations")
        st.write(
            "This system reflects patterns in its *training data*, which has its "
            "own biases (source, political, labeling). It cannot verify facts, "
            "detect novel misinformation styles it hasn't seen, or replace human "
            "judgment and professional fact-checking. See the About page for more."
        )

    render_disclaimer()


def page_predict() -> None:
    st.title("🔍 Check a headline or article")
    service = get_service_or_stop()

    col1, col2 = st.columns(2)
    with col1:
        headline = st.text_area("Headline", height=100, placeholder="Enter the news headline...")
    with col2:
        article = st.text_area(
            "Article body", height=300, placeholder="Paste the full article text (optional if the headline alone is enough)..."
        )

    btn_col, _ = st.columns([1, 5])
    predict_clicked = btn_col.button("Predict", type="primary", use_container_width=True)
    clear_clicked = btn_col.button("Clear", use_container_width=True)

    if clear_clicked:
        st.rerun()

    if predict_clicked:
        try:
            result = service.predict(title=headline, text=article)
        except EmptyInputError as exc:
            st.warning(str(exc))
            return

        st.divider()
        badge = "🔴 FAKE" if result.prediction == "FAKE" else "🟢 REAL"
        st.markdown(f"## Prediction: {badge}")

        m1, m2, m3 = st.columns(3)
        score_label = "Calibrated probability" if result.is_calibrated_probability else "Model score (uncalibrated)"
        m1.metric(score_label, f"{result.confidence:.1%}" if result.confidence is not None else "N/A")
        m2.metric("Model used", result.model_name)
        with m3:
            st.write("")
            render_confidence_badge(result.confidence_level)

        if result.top_features:
            st.subheader("Features influencing this prediction")
            for feat in result.top_features:
                icon = "🔴" if feat.direction == "FAKE" else "🟢"
                st.write(f"{icon} `{feat.feature}` — pushes toward **{feat.direction}** ({feat.weight:+.3f})")
            st.caption(
                "These are learned statistical associations from the training data, "
                "not factual evidence that the content is true or false."
            )

        render_disclaimer()


def page_batch() -> None:
    st.title("📄 Batch prediction")
    service = get_service_or_stop()
    st.write("Upload a CSV with a title/headline and/or text/article column.")

    uploaded = st.file_uploader("CSV file", type=["csv"])
    if uploaded is None:
        return

    try:
        df = pd.read_csv(uploaded)
    except Exception as exc:  # noqa: BLE001 - surfaced directly to the user
        st.error(f"Could not read this file as CSV: {exc}")
        return

    if df.empty:
        st.warning("The uploaded CSV has no rows.")
        return

    with st.spinner(f"Classifying {len(df)} rows..."):
        try:
            result_df = service.predict_batch(df)
        except EmptyInputError as exc:
            st.error(str(exc))
            return

    st.success(f"Classified {len(result_df)} rows.")
    st.dataframe(result_df, use_container_width=True)

    csv_bytes = result_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download results CSV", data=csv_bytes, file_name="predictions.csv", mime="text/csv")
    render_disclaimer()


def page_performance() -> None:
    st.title("📊 Model performance")
    service = get_service_or_stop()
    metadata = service.metadata

    if not metadata:
        st.warning("No metadata.json found yet. Train the model to populate this page.")
        return

    test_metrics = metadata.get("evaluation_metrics", {}).get("test", {})
    val_metrics = metadata.get("evaluation_metrics", {}).get("validation", {})

    st.subheader(f"Best model: {metadata.get('model_name', 'unknown')}")
    st.caption(f"Trained on {metadata.get('training_date', 'unknown date')} · "
               f"{metadata.get('dataset_info', {}).get('n_total', '?')} total examples")

    cols = st.columns(4)
    for col, key in zip(cols, ["accuracy", "precision", "recall", "f1"]):
        val = test_metrics.get(key)
        col.metric(key.capitalize(), f"{val:.3f}" if val is not None else "N/A")

    fig_dir = config.figures_dir
    figure_cols = st.columns(2)
    figures = [
        ("confusion_matrix_test.png", "Confusion matrix (test set)"),
        ("model_comparison.png", "Model comparison (validation F1 / accuracy)"),
        ("roc_curve_test.png", "ROC curve (test set)"),
        ("pr_curve_test.png", "Precision-recall curve (test set)"),
        ("class_distribution.png", "Class distribution"),
    ]
    for i, (fname, caption) in enumerate(figures):
        path = fig_dir / fname
        if path.exists():
            figure_cols[i % 2].image(str(path), caption=caption, use_container_width=True)

    st.subheader("Best model — full validation metrics")
    if val_metrics:
        st.json(val_metrics)
    else:
        st.write("Not available.")


def page_about() -> None:
    st.title("ℹ️ About this project")
    st.markdown(
        """
### Dataset
Trained on a labeled REAL/FAKE news dataset (e.g. the Kaggle "Fake and Real
News Dataset") placed under `data/raw/` — see `data/raw/README.md` for the
exact expected layout.

### NLP pipeline
Unicode normalization → HTML/URL/email stripping → lowercasing →
tokenization → stopword removal → lemmatization, applied identically at
training and inference time. Stylistic signals (capitalization, punctuation,
exclamation/question marks, length) are captured separately as numeric
features *before* that cleaning happens, so they aren't lost.

### Algorithms
Logistic Regression, Multinomial Naive Bayes, Linear SVM, and a
Passive-Aggressive Classifier are trained and compared with hyperparameter
tuning; the model with the best **validation F1-score** is selected
automatically and evaluated once, at the end, on a held-out test set.

### Limitations & ethical considerations
- **Dataset bias** — the model can only reflect patterns present in its
  training data's sources, topics, and time period.
- **Political / source bias** — if training data skews toward particular
  outlets or viewpoints, predictions can inherit that skew.
- **Labeling errors** — any mislabeled training examples teach the model
  the wrong pattern.
- **Language limitations** — the NLP pipeline is English-only.
- **Distribution shift** — performance can degrade on topics, writing
  styles, or time periods very different from the training data.
- **Adversarial text** — text deliberately written to evade detection can
  fool the model.
- **Not fact-checking** — a "REAL" prediction is not proof of truth, and a
  "FAKE" prediction is not proof of falsehood. It is a statistical pattern
  match and should always be reviewed critically.
        """
    )
    render_disclaimer()


PAGES = {
    "Home": page_home,
    "Predict": page_predict,
    "Batch Prediction": page_batch,
    "Model Performance": page_performance,
    "About": page_about,
}


def main() -> None:
    st.sidebar.title("📰 Navigation")
    choice = st.sidebar.radio("Go to", list(PAGES.keys()))
    PAGES[choice]()


if __name__ == "__main__":
    main()
