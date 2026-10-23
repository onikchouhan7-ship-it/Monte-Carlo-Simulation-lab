from __future__ import annotations
import csv
import io
import math
import random
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st

PI = math.pi
ROOT = Path(__file__).resolve().parent
DEFAULT_CSV = ROOT / "comparison.csv"

st.set_page_config(
    page_title="Monte Carlo Lab | Simulation Studio",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Lightweight design system: custom CSS only affects presentation.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --ink:#e8edf7; --muted:#98a5bc; --panel:#111827; --panel2:#151f30; --line:rgba(148,163,184,.18); --mint:#70e1c1; --blue:#82aaff; }
html, body, [class*="css"] { font-family:'Manrope',sans-serif; }
.stApp { background: radial-gradient(ellipse at 15% 0%, rgba(60,100,170,.16), transparent 35%), #0a0f18; color:var(--ink); }
[data-testid="stHeader"] { background:rgba(10,15,24,.8); }
[data-testid="stSidebar"] { background:#0c1320; border-right:1px solid var(--line); }
.block-container { padding-top:2rem; padding-bottom:3rem; max-width:1500px; }
.hero { padding:1.35rem 1.5rem 1.3rem; border:1px solid var(--line); border-radius:22px; background:linear-gradient(135deg,rgba(25,38,58,.95),rgba(15,23,36,.93)); margin-bottom:1.25rem; position:relative; overflow:hidden; }
.hero:after { content:'π'; position:absolute; right:2.2rem; top:-2.2rem; font-family:Georgia,serif; font-size:12rem; font-weight:700; color:rgba(130,170,255,.06); pointer-events:none; }
.eyebrow { color:var(--mint); font-family:'DM Mono',monospace; font-size:.75rem; letter-spacing:.14em; text-transform:uppercase; }
.hero h1 { margin:.35rem 0 .25rem; font-size:2.25rem; letter-spacing:-.055em; color:#f2f6ff; }
.hero p { color:var(--muted); margin:0; max-width:740px; }
.section-title { font-size:1.13rem; font-weight:800; color:#eef3ff; margin:.3rem 0 .85rem; letter-spacing:-.025em; }
.panel { background:linear-gradient(145deg,rgba(21,31,48,.92),rgba(15,23,35,.92)); border:1px solid var(--line); border-radius:18px; padding:1rem 1.1rem; }
.kpi-label { color:var(--muted); font-size:.78rem; letter-spacing:.02em; margin-bottom:.35rem; }
.kpi-value { color:#f2f6ff; font-size:1.55rem; font-weight:800; letter-spacing:-.04em; line-height:1.25; }
.kpi-foot { color:#a1b0c8; font-size:.76rem; margin-top:.4rem; }
.tag { display:inline-block; padding:.25rem .55rem; border-radius:99px; background:rgba(112,225,193,.1); color:var(--mint); border:1px solid rgba(112,225,193,.22); font-size:.72rem; font-family:'DM Mono',monospace; }
div[data-testid="stMetric"] { background:linear-gradient(145deg,rgba(21,31,48,.92),rgba(15,23,35,.92)); border:1px solid var(--line); padding:1rem 1.05rem; border-radius:16px; }
div[data-testid="stMetricLabel"] { color:#aab6ca; }
div[data-testid="stMetricValue"] { color:#f2f6ff; }
.stButton button, .stDownloadButton button { border-radius:10px; min-height:2.8rem; font-weight:750; }
.stButton button[kind="primary"] { background:#70e1c1; color:#092017; border:0; }
.stButton button[kind="primary"]:hover { background:#9aefd8; color:#092017; }
[data-testid="stTabs"] button { font-weight:700; }
[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
.small-note { color:var(--muted); font-size:.82rem; }
.formula { padding:.75rem 1rem; border-left:3px solid var(--mint); background:rgba(112,225,193,.06); border-radius:0 10px 10px 0; color:#dce8f8; }
hr { border-color:var(--line); }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Sidebar: experiment configuration
# -----------------------------
st.sidebar.markdown('<div class="eyebrow">Experiment console</div>', unsafe_allow_html=True)
st.sidebar.title("Run configuration")
st.sidebar.caption("Parameters mirror your C++ benchmark workflow.")
trials = st.sidebar.number_input("Repeated trials per sample size", min_value=1, max_value=10000, value=20, step=1)
start_n = st.sidebar.select_slider(
    "Starting sample size",
    options=[100, 1_000],
    value=1_000,
    format_func=lambda x: f"{x:,}",
)
seed = st.sidebar.number_input("Random seed", min_value=0, max_value=2_147_483_647, value=42, step=1)
engine_choice = st.sidebar.radio("Simulation engine", ["Python demo engine", "Use C++ engine (optional)"], index=0)
cpp_binary = st.sidebar.text_input("C++ executable path", value="./MonteCarloLab.exe" if __import__('os').name == 'nt' else "./MonteCarloLab", disabled=engine_choice != "Use C++ engine (optional)")
run_button = st.sidebar.button("▶  Run experiment", type="primary", use_container_width=True)
st.sidebar.markdown("---")
st.sidebar.markdown("**Sample-size schedule**")
st.sidebar.code("N, 10N, 100N, 1000N", language="text")
st.sidebar.caption("The C++ program currently caps each sample size at 1,000,000. Choose a starting size accordingly.")

st.markdown('''<div class="hero">
  <div class="eyebrow">Monte Carlo Simulation Lab · Research workspace</div>
  <h1>Measure randomness.<br>Understand convergence.</h1>
  <p>Explore how sampling error, repeated trials, and computation time behave as the number of random points grows. Built around your project's π-estimation benchmark and CSV results.</p>
</div>''', unsafe_allow_html=True)

# Helpers

def run_python_experiment(num_trials: int, initial_n: int, random_seed: int) -> list[dict]:
    """Perform the same four-level repeated-trial experiment as main.cpp."""
    rows: list[dict] = []
    rng = random.Random(random_seed)
    for level in range(4):
        n = initial_n * (10 ** level)
        if n > 1_000_000:
            raise ValueError(f"Sample size {n:,} exceeds the existing C++ project's 1,000,000-point limit. Lower the starting sample size.")
        estimates, errors, timings = [], [], []
        for _ in range(num_trials):
            inside = 0
            start = time.perf_counter()
            for _ in range(n):
                x = rng.uniform(-1.0, 1.0)
                y = rng.uniform(-1.0, 1.0)
                if x * x + y * y <= 1.0:
                    inside += 1
            elapsed = time.perf_counter() - start
            estimate = 4.0 * inside / n
            estimates.append(estimate)
            errors.append(abs(estimate - PI))
            timings.append(elapsed)
        avg_time = statistics.mean(timings)
        rows.append({
            "samples": n,
            "trials": num_trials,
            "mean_estimate": statistics.mean(estimates),
            "mean_absolute_error": statistics.mean(errors),
            "average_time": avg_time,
            "points_per_second": n / avg_time if avg_time > 0 else 0.0,
            "estimate_stddev": statistics.stdev(estimates) if len(estimates) > 1 else 0.0,
        })
    return rows


def read_comparison_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"samples", "trials", "mean_estimate", "mean_absolute_error", "average_time", "points_per_second"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            return []
        rows = []
        for raw in reader:
            try:
                rows.append({
                    "samples": int(raw["samples"]),
                    "trials": int(raw["trials"]),
                    "mean_estimate": float(raw["mean_estimate"]),
                    "mean_absolute_error": float(raw["mean_absolute_error"]),
                    "average_time": float(raw["average_time"]),
                    "points_per_second": float(raw["points_per_second"]),
                    "estimate_stddev": float(raw.get("estimate_stddev", 0) or 0),
                })
            except (ValueError, TypeError):
                continue
        return rows


def write_csv(rows: list[dict]) -> bytes:
    fieldnames = ["samples", "trials", "mean_estimate", "mean_absolute_error", "average_time", "points_per_second", "estimate_stddev"]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, 0) for k in fieldnames})
    return buffer.getvalue().encode("utf-8")


def style_ax(ax, title: str, xlabel: str, ylabel: str, log_x: bool = True, log_y: bool = False):
    ax.set_title(title, loc="left", color="#e8edf7", fontsize=12, fontweight="bold", pad=13)
    ax.set_xlabel(xlabel, color="#aab6ca")
    ax.set_ylabel(ylabel, color="#aab6ca")
    if log_x:
        ax.set_xscale("log")
    if log_y:
        # Zero errors cannot be represented on a logarithmic axis; clamp only for display.
        ax.set_yscale("log")
    ax.grid(True, which="both", linestyle="--", linewidth=.6, alpha=.2, color="#9aacc6")
    ax.tick_params(colors="#aab6ca", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#344256")
    ax.set_facecolor("#111a28")

# Run chosen engine. C++ runner is opt-in because the repo's current CLI is interactive and writes comparison.csv.
if run_button:
    if start_n * 1000 > 1_000_000:
        st.error("Your C++ project's current main.cpp restricts the largest sample size to 1,000,000. Select a starting sample size of 100 or 1,000.")
    elif engine_choice == "Use C++ engine (optional)":
        st.warning("Your existing executable is interactive and writes comparison.csv in its working directory. To avoid overwriting your current data unexpectedly, this dashboard has not launched it automatically. Run the compiled C++ program in a terminal, then reload the CSV from the Data tab. The Python demo engine is fully runnable from this interface.")
    else:
        with st.spinner("Running repeated trials across four sample sizes…"):
            try:
                results = run_python_experiment(int(trials), int(start_n), int(seed))
                st.session_state["results"] = results
                st.session_state["last_run"] = {"trials": int(trials), "start_n": int(start_n), "seed": int(seed), "engine": "Python demo engine"}
                st.success("Experiment complete. Results updated below.")
            except Exception as exc:
                st.error(str(exc))

# Data import is deliberately local-only.
with st.expander("Load your existing comparison.csv", expanded=False):
    st.write("Use the CSV produced by your C++ program. The dashboard reads your actual benchmark columns; it does not make up new results.")
    uploaded = st.file_uploader("Choose comparison.csv", type=["csv"], key="comparison_upload")
    if uploaded is not None:
        try:
            raw_text = uploaded.getvalue().decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(raw_text))
            needed = {"samples", "trials", "mean_estimate", "mean_absolute_error", "average_time", "points_per_second"}
            if not reader.fieldnames or not needed.issubset(set(reader.fieldnames)):
                st.error("CSV is missing one or more required columns. Expected: samples, trials, mean_estimate, mean_absolute_error, average_time, points_per_second.")
            else:
                loaded = []
                for row in reader:
                    loaded.append({"samples": int(row["samples"]), "trials": int(row["trials"]), "mean_estimate": float(row["mean_estimate"]), "mean_absolute_error": float(row["mean_absolute_error"]), "average_time": float(row["average_time"]), "points_per_second": float(row["points_per_second"]), "estimate_stddev": 0.0})
                st.session_state["results"] = loaded
                st.session_state["last_run"] = {"trials": None, "start_n": None, "seed": None, "engine": "Imported C++ CSV"}
                st.success(f"Loaded {len(loaded)} benchmark rows.")
        except Exception as exc:
            st.error(f"Could not read CSV: {exc}")

results = st.session_state.get("results")
if not results:
    # Load repository's committed experimental data if present alongside app.py.
    results = read_comparison_csv(DEFAULT_CSV)
    if not results:
        # Published baseline from this repository's README/comparison.csv, clearly identified as repository data.
        results = [
            {"samples": 1000, "trials": 20, "mean_estimate": 3.1116, "mean_absolute_error": 0.0512778, "average_time": 0.00015015, "points_per_second": 6660006.66, "estimate_stddev": 0.0},
            {"samples": 10000, "trials": 20, "mean_estimate": 3.14528, "mean_absolute_error": 0.0149222, "average_time": 0.00215370, "points_per_second": 4643172.21525746, "estimate_stddev": 0.0},
            {"samples": 100000, "trials": 20, "mean_estimate": 3.142666, "mean_absolute_error": 0.0034962, "average_time": 0.00902590, "points_per_second": 11079227.55625478, "estimate_stddev": 0.0},
            {"samples": 1000000, "trials": 20, "mean_estimate": 3.1418216, "mean_absolute_error": 0.001038, "average_time": 0.09894475, "points_per_second": 10106650.42864831, "estimate_stddev": 0.0},
        ]
        source_note = "Showing baseline results committed in the repository. Run a new experiment or upload comparison.csv to view fresh results."
    else:
        source_note = "Showing rows from the local comparison.csv file."
else:
    source_note = "Showing the most recently generated or imported results."

# Build data arrays for dashboard sections.
sorted_results = sorted(results, key=lambda row: row["samples"])
xs = [row["samples"] for row in sorted_results]
errs = [max(row["mean_absolute_error"], 1e-12) for row in sorted_results]
means = [row["mean_estimate"] for row in sorted_results]
times = [row["average_time"] for row in sorted_results]
throughputs = [row["points_per_second"] for row in sorted_results]

st.markdown(f'<span class="tag">● DATA SOURCE</span> &nbsp; <span class="small-note">{source_note}</span>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Experiment overview</div>', unsafe_allow_html=True)

latest = sorted_results[-1]
first_error = sorted_results[0]["mean_absolute_error"]
last_error = latest["mean_absolute_error"]
error_reduction = (first_error / last_error) if last_error > 0 else float("inf")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Largest sample size", f"{latest['samples']:,}", help="Points generated in each trial at the largest benchmark level.")
k2.metric("Mean π estimate", f"{latest['mean_estimate']:.8f}", delta=f"{latest['mean_estimate'] - PI:+.6f} vs true π")
k3.metric("Mean absolute error", f"{latest['mean_absolute_error']:.6f}", delta=f"{error_reduction:.1f}× lower than first level" if math.isfinite(error_reduction) else None, delta_color="inverse")
k4.metric("Average throughput", f"{latest['points_per_second']:,.0f}", help="Points per second based on average time per trial.")

# Tabs keep the dashboard information architecture focused.
tab_overview, tab_accuracy, tab_performance, tab_data, tab_method = st.tabs(["✦ Overview", "↘ Accuracy & convergence", "◴ Performance", "▤ Data & export", "∑ Method"])

with tab_overview:
    left, right = st.columns([1.35, 1])
    with left:
        st.markdown('<div class="section-title">How accuracy changes with sample size</div>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(8, 4.2), constrained_layout=True)
        fig.patch.set_facecolor("#111a28")
        style_ax(ax, "Experimental error vs sample size", "Random points per trial (N)", "Mean absolute error", log_x=True, log_y=True)
        ax.plot(xs, errs, color="#70e1c1", marker="o", markersize=6, linewidth=2.4, label="Observed mean absolute error")
        ref = [errs[0] * math.sqrt(xs[0] / x) for x in xs]
        ax.plot(xs, ref, color="#82aaff", linestyle="--", linewidth=1.8, label="1/√N reference trend")
        ax.legend(facecolor="#111a28", edgecolor="#344256", labelcolor="#dce6f5", fontsize=8)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    with right:
        st.markdown('<div class="section-title">Run summary</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-label">Sample-size levels</div><div class="kpi-value">{len(sorted_results)} levels</div><div class="kpi-foot">Geometric progression: ×10 per level</div><hr>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-label">Trials per level</div><div class="kpi-value">{sorted_results[0]["trials"]:,}</div><div class="kpi-foot">Repeated independent estimates</div><hr>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-label">Largest-level average runtime</div><div class="kpi-value">{latest["average_time"]:.6f} s</div><div class="kpi-foot">Measured simulation time per trial</div><hr>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-label">Largest-level estimate difference</div><div class="kpi-value">{abs(latest["mean_estimate"] - PI):.6f}</div><div class="kpi-foot">Absolute difference between mean estimate and π</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="formula"><b>Monte Carlo estimator</b><br><span style="font-family:DM Mono,monospace">π̂ = 4 × points inside circle / total points</span></div>', unsafe_allow_html=True)

with tab_accuracy:
    st.markdown('<div class="section-title">Accuracy analysis</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(7, 4.4), constrained_layout=True)
        fig.patch.set_facecolor("#111a28")
        style_ax(ax, "Mean estimate vs true π", "Random points per trial (N)", "Mean π estimate", log_x=True)
        ax.plot(xs, means, color="#82aaff", marker="o", linewidth=2.2, label="Mean estimate")
        ax.axhline(PI, color="#70e1c1", linestyle="--", linewidth=1.7, label=f"True π = {PI:.6f}")
        ax.legend(facecolor="#111a28", edgecolor="#344256", labelcolor="#dce6f5", fontsize=8)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    with c2:
        fig, ax = plt.subplots(figsize=(7, 4.4), constrained_layout=True)
        fig.patch.set_facecolor("#111a28")
        style_ax(ax, "Error on log-log axes", "Random points per trial (N)", "Mean absolute error", log_x=True, log_y=True)
        ax.plot(xs, errs, color="#f0a66c", marker="o", linewidth=2.2, label="Observed error")
        ref = [errs[0] * math.sqrt(xs[0] / x) for x in xs]
        ax.plot(xs, ref, color="#82aaff", linestyle="--", linewidth=1.7, label="1/√N reference")
        ax.legend(facecolor="#111a28", edgecolor="#344256", labelcolor="#dce6f5", fontsize=8)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    st.info("The 1/√N curve is a reference trend, not a guaranteed error at each sample size. Individual Monte Carlo results are random, and observed errors need not decrease monotonically.")

with tab_performance:
    st.markdown('<div class="section-title">Performance & scaling</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(7, 4.4), constrained_layout=True)
        fig.patch.set_facecolor("#111a28")
        style_ax(ax, "Throughput by sample size", "Random points per trial (N)", "Points per second", log_x=True)
        ax.plot(xs, throughputs, color="#70e1c1", marker="o", linewidth=2.2)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    with c2:
        fig, ax = plt.subplots(figsize=(7, 4.4), constrained_layout=True)
        fig.patch.set_facecolor("#111a28")
        style_ax(ax, "Average runtime by sample size", "Random points per trial (N)", "Average seconds per trial", log_x=True, log_y=True)
        ax.plot(xs, [max(x, 1e-12) for x in times], color="#f0a66c", marker="o", linewidth=2.2)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    st.caption("Throughput and runtime depend on CPU, compiler optimizations, system load, and the engine used. Compare runs on the same machine for meaningful conclusions.")

with tab_data:
    st.markdown('<div class="section-title">Benchmark table</div>', unsafe_allow_html=True)
    display_rows = []
    for row in sorted_results:
        display_rows.append({
            "Points / trial": f"{row['samples']:,}",
            "Trials": row["trials"],
            "Mean π estimate": f"{row['mean_estimate']:.8f}",
            "Mean absolute error": f"{row['mean_absolute_error']:.8f}",
            "Average time (s)": f"{row['average_time']:.6f}",
            "Throughput (pts/s)": f"{row['points_per_second']:,.0f}",
        })
    st.dataframe(display_rows, use_container_width=True, hide_index=True)
    st.download_button("⬇ Download current results (CSV)", data=write_csv(sorted_results), file_name="monte_carlo_lab_results.csv", mime="text/csv", type="primary")
    st.caption("CSV fields remain aligned with your repository's comparison.csv format, with estimate_stddev included when available.")

with tab_method:
    st.markdown('<div class="section-title">What the simulation computes</div>', unsafe_allow_html=True)
    st.markdown("""
    **1. Sample uniformly from the square** `[-1, 1] × [-1, 1]`.

    **2. Classify each point** using `x*x + y*y <= 1`.

    **3. Estimate π** from the proportion of points inside the unit circle.
    """)
    st.latex(r"\hat{\pi} = 4\frac{N_{\mathrm{inside}}}{N}")
    st.markdown("""
    **Repeated-trial statistics**

    - **Mean estimate:** average of all trial-level π estimates.
    - **Mean absolute error:** average of `|estimate − π|` across trials.
    - **Average execution time:** average simulation duration per trial.
    - **Throughput:** sample size divided by average execution time.

    The expected error scale behaves approximately like `1/√N`, so a 100× increase in sample size generally reduces the typical error scale by roughly 10×. This is a probabilistic trend, not a promise about every run.
    """)
    with st.expander("Why is it a full circle, not a quarter-circle?"):
        st.write("This project samples both x and y uniformly from −1 to 1, so the plotted domain is a square of side length 2 containing the full unit circle. The circle's area is π and the square's area is 4; therefore the inside-point proportion estimates π/4.")

st.markdown("---")
st.markdown('<div class="small-note">Monte Carlo Simulation Lab · C++ benchmark concepts with a Python/Streamlit dashboard. Baseline figures are labeled as repository data; new dashboard runs use the Python demo engine unless the C++ CSV is imported.</div>', unsafe_allow_html=True)
