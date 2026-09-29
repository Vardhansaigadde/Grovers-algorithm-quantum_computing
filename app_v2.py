"""
Realistic UI: retrieve a password by username or email using
Grover's algorithm (simulated) and compare with classical linear search.

Setup:  pip install streamlit pandas faker pylatexenc
Needs:  grover_password_search_v2.py and 10k-most-common.txt in the same folder
Run:    streamlit run app_v2.py
"""

import math
import os
import random
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from faker import Faker

from grover_password_search_v2 import (
    PASSWORD_FILE,
    build_grover_circuit,
    grover_search,
    optimal_iterations,
)

st.set_page_config(page_title="Quantum Credential Lookup", page_icon="🔐", layout="wide")

CLASSICAL_COLOR = "#d9822b"
GROVER_COLOR = "#2b7bd9"
DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "proton.me"]


# ---------------------------------------------------------------- data
@st.cache_data
def load_records(n_qubits, seed=42):
    """N = 2^n records: synthetic name/username/email + real common password."""
    N = 2 ** n_qubits
    with open(PASSWORD_FILE, encoding="utf-8", errors="ignore") as f:
        passwords = [line.strip() for line in f if line.strip()]
    rng = random.Random(seed)
    passwords = rng.sample(passwords, N)

    fake = Faker()
    Faker.seed(seed)
    records = []
    for i in range(N):
        username = fake.unique.user_name()
        records.append({
            "name": fake.name(),
            "username": username,
            "email": f"{username}@{rng.choice(DOMAINS)}",
            "password": passwords[i],
        })
    return records


def classical_lookup(records, key):
    """Linear search on username OR email. Returns (index, comparisons)."""
    key = key.strip().lower()
    comparisons = 0
    for i, r in enumerate(records):
        comparisons += 1
        if r["username"].lower() == key or r["email"].lower() == key:
            return i, comparisons
    return -1, comparisons


def time_classical(records, key, repeats=200):
    """Average time of a classical lookup over many repeats (it's very fast)."""
    start = time.perf_counter()
    for _ in range(repeats):
        idx, comparisons = classical_lookup(records, key)
    return idx, comparisons, (time.perf_counter() - start) / repeats


def bar_pair(ax, values, text_labels, title, ylabel, log=False):
    bars = ax.bar(["Classical", "Grover"], values, color=[CLASSICAL_COLOR, GROVER_COLOR])
    if log:
        ax.set_yscale("log")
    ax.set_title(title, fontsize=11)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.3)
    for b, v, t in zip(bars, values, text_labels):
        ax.text(b.get_x() + b.get_width() / 2, v, t, ha="center", va="bottom", fontsize=10)
    ax.margins(y=0.25)


# ------------------------------------------------------------- sidebar
st.sidebar.header("Database settings")
n = st.sidebar.slider("Database size (qubits n)", 2, 10, 8,
                      help="The database holds 2^n accounts.")
N = 2 ** n
records = load_records(n)
st.sidebar.write(f"Accounts in database: **{N}**")
st.sidebar.write(f"Classical average: about **{N // 2}** comparisons")
st.sidebar.write(f"Grover iterations: **{optimal_iterations(N)}**")
st.sidebar.info("All names, usernames and emails are synthetic. Passwords come "
                "from the public SecLists common-password list.")

st.title("🔐 Quantum Credential Lookup")
st.caption("Retrieve a password by username or email using Grover's algorithm "
           "(Qiskit Aer simulator) and compare with classical linear search.")

tab1, tab_race, tab2, tab3, tab4 = st.tabs(
    ["Lookup", "Grover Race", "Scaling", "How Grover works", "Saved results"])

# ------------------------------------------------------------- tab 1
with tab1:
    with st.expander("Browse the database (passwords hidden)"):
        st.dataframe(pd.DataFrame(records)[["name", "username", "email"]])

    mode = st.radio("How do you want to search?",
                    ["Type username or email", "Select from list"], horizontal=True)
    if mode == "Type username or email":
        query = st.text_input("Username or email",
                              placeholder="e.g. " + records[N // 2]["username"])
    else:
        choice = st.selectbox(
            "Select an account", range(N), index=(N * 3) // 4,
            format_func=lambda i: f"{records[i]['name']}  |  {records[i]['email']}")
        query = records[choice]["email"]

    if st.button("Retrieve password", type="primary"):
        if not query.strip():
            st.warning("Please enter a username or email.")
        else:
            target, c_cmp, c_time = time_classical(records, query)
            if target < 0:
                st.error("No account found with that username or email.")
                hints = [r["username"] for r in records
                         if r["username"].lower().startswith(query.strip().lower()[:3])][:5]
                if hints:
                    st.info("Similar usernames: " + ", ".join(hints))
            else:
                with st.spinner("Running Grover circuit..."):
                    g_idx, g_calls, g_prob, g_time, counts = grover_search(n, target)
                rec = records[g_idx]

                if g_idx == target:
                    st.success(f"Account found: **{rec['name']}**")
                else:
                    st.warning("Grover returned a different entry. Try again.")
                a, b, c = st.columns(3)
                a.write("**Username**"); a.code(rec["username"])
                b.write("**Email**"); b.code(rec["email"])
                c.write("**Password**"); c.code(rec["password"])

                st.divider()
                st.subheader("Classical vs Grover")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Classical comparisons", c_cmp)
                m2.metric("Grover oracle calls", g_calls)
                m3.metric("Query reduction", f"{c_cmp / g_calls:.1f}x")
                m4.metric("Grover success prob.", f"{g_prob:.1%}")
                t1, t2 = st.columns(2)
                t1.metric("Classical time", f"{c_time * 1e6:.1f} µs")
                t2.metric("Grover time (simulator)", f"{g_time * 1e3:.0f} ms")

                fig, ax = plt.subplots(1, 3, figsize=(15, 4))
                bar_pair(ax[0], [c_cmp, g_calls], [str(c_cmp), str(g_calls)],
                         "Number of queries", "Comparisons / oracle calls")
                bar_pair(ax[1], [c_time * 1e6, g_time * 1e6],
                         [f"{c_time * 1e6:.1f} µs", f"{g_time * 1e3:.0f} ms"],
                         "Time taken (log scale)", "Microseconds", log=True)

                top = sorted(counts.items(), key=lambda x: -x[1])[:6][::-1]
                names = [records[int(s, 2)]["username"] for s, _ in top]
                pcts = [cnt / 1024 * 100 for _, cnt in top]
                colors = [GROVER_COLOR if int(s, 2) == target else "#bbbbbb" for s, _ in top]
                ax[2].barh(names, pcts, color=colors)
                ax[2].set_title("Grover measurement results", fontsize=11)
                ax[2].set_xlabel("Share of 1,024 shots (%)")
                ax[2].grid(axis="x", alpha=0.3)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

                st.caption("Grover reduces the number of queries, but on a classical "
                           "simulator each query is expensive to simulate, so classical "
                           "search is faster in real time here. See the Scaling tab.")

                if n <= 4:
                    with st.expander("Show the Grover circuit"):
                        try:
                            qc, _ = build_grover_circuit(n, target)
                            st.pyplot(qc.draw("mpl"))
                        except Exception as e:
                            st.info(f"Circuit drawing needs pylatexenc. {e}")

# ------------------------------------------------------------- tab 2
with tab2:
    st.subheader("Measured on your machine (n = 2 to 10)")
    st.write("Runs 10 random lookups per database size for both methods.")
    if st.button("Run scaling benchmark"):
        rows = []
        prog = st.progress(0.0)
        for j, m in enumerate(range(2, 11)):
            recs = load_records(m)
            trials, cq, ct, gt = 10, 0, 0, 0
            for _ in range(trials):
                t = random.randrange(2 ** m)
                _, cmp_, tc = time_classical(recs, recs[t]["email"], repeats=20)
                _, calls, _, tg, _ = grover_search(m, t)
                cq += cmp_; ct += tc; gt += tg
            rows.append({"N": 2 ** m, "classical_queries": cq / trials,
                         "grover_queries": calls,
                         "classical_time_us": ct / trials * 1e6,
                         "grover_time_us": gt / trials * 1e6})
            prog.progress((j + 1) / 9)
        st.session_state["scaling"] = pd.DataFrame(rows)

    if "scaling" in st.session_state:
        df = st.session_state["scaling"]
        fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
        ax[0].plot(df["N"], df["classical_queries"], "o-", color=CLASSICAL_COLOR, label="Classical")
        ax[0].plot(df["N"], df["grover_queries"], "s-", color=GROVER_COLOR, label="Grover")
        ax[0].set(title="Queries vs database size", xlabel="N (accounts)", ylabel="Queries")
        ax[1].plot(df["N"], df["classical_time_us"], "o-", color=CLASSICAL_COLOR, label="Classical")
        ax[1].plot(df["N"], df["grover_time_us"], "s-", color=GROVER_COLOR, label="Grover (simulator)")
        ax[1].set(title="Time vs database size", xlabel="N (accounts)", ylabel="Microseconds")
        for a in ax:
            a.set_xscale("log", base=2); a.set_yscale("log")
            a.grid(alpha=0.3); a.legend()
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        st.dataframe(df.round(2))

    st.divider()
    st.subheader("Projection: where Grover's query advantage grows large")
    st.write("Pure theory: classical needs about N/2 queries on average and Grover "
             "about (π/4)√N. Real speedup needs large fault-tolerant quantum hardware.")
    Ns = [10 ** e for e in range(1, 13)]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(Ns, [x / 2 for x in Ns], color=CLASSICAL_COLOR, label="Classical N/2")
    ax.plot(Ns, [math.pi / 4 * math.sqrt(x) for x in Ns], color=GROVER_COLOR,
            label="Grover (π/4)√N")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set(xlabel="Database size N", ylabel="Queries")
    ax.grid(alpha=0.3); ax.legend()
    st.pyplot(fig)
    plt.close(fig)
    st.dataframe(pd.DataFrame({
        "N": [f"{x:,}" for x in (10**3, 10**6, 10**9, 10**12)],
        "Classical (avg)": [f"{x // 2:,}" for x in (10**3, 10**6, 10**9, 10**12)],
        "Grover": [f"{math.ceil(math.pi / 4 * math.sqrt(x)):,}"
                   for x in (10**3, 10**6, 10**9, 10**12)],
    }))

# ------------------------------------------------------------- tab 3
with tab3:
    st.subheader("Watch Grover's algorithm find the answer")
    st.write(
        "Every account starts with the same **amplitude**. Each round has two steps: "
        "the **oracle** flips the sign of the target's amplitude, then the **diffusion** "
        "step reflects every amplitude about the average. The target's amplitude grows "
        "and all the others shrink. Drag the slider to step through it."
    )

    vc1, vc2 = st.columns(2)
    vn = vc1.slider("Database size for this visualization (qubits)", 2, 6, 4, key="viz_n")
    VN = 2 ** vn
    vrecs = load_records(vn)
    vt = vc2.selectbox("Target account", range(VN), index=VN // 3, key="viz_target",
                       format_func=lambda i: vrecs[i]["username"])

    k_opt = optimal_iterations(VN)
    amp = np.full(VN, 1 / np.sqrt(VN))
    states = [("Start: equal superposition (every account equally likely)", amp.copy())]
    for r in range(1, k_opt + 3):
        amp[vt] *= -1
        states.append((f"Round {r}, oracle: flip the target's sign", amp.copy()))
        amp = 2 * amp.mean() - amp
        states.append((f"Round {r}, diffusion: reflect about the average", amp.copy()))

    step = st.slider("Step", 0, len(states) - 1, 0, key="viz_step")
    label, cur = states[step]
    rounds_done = step // 2
    st.markdown(f"**{label}**")

    left, right = st.columns(2)
    with left:
        fig, ax = plt.subplots(figsize=(7, 4))
        colors = [GROVER_COLOR if i == vt else "#bbbbbb" for i in range(VN)]
        ax.bar(range(VN), cur, color=colors)
        ax.axhline(cur.mean(), color="red", linestyle="--", linewidth=1, label="average")
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_ylim(-1.05, 1.05)
        ax.set(title="Amplitude of every account", xlabel="Account index",
               ylabel="Amplitude")
        if VN > 16:
            ax.set_xticks([])
        ax.legend(loc="upper right")
        ax.grid(axis="y", alpha=0.3)
        st.pyplot(fig)
        plt.close(fig)

    with right:
        probs = [s[1][vt] ** 2 * 100 for i, s in enumerate(states) if i % 2 == 0]
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(range(len(probs)), probs, "o-", color=GROVER_COLOR)
        ax.plot([rounds_done], [probs[rounds_done]], "ro", markersize=11, label="current")
        ax.axvline(k_opt, color="green", linestyle=":", label=f"optimal rounds = {k_opt}")
        ax.set(title="Chance of finding the target after each full round",
               xlabel="Rounds completed", ylabel="Probability (%)", ylim=(0, 105))
        ax.grid(alpha=0.3); ax.legend(loc="center right")
        st.pyplot(fig)
        plt.close(fig)

    st.metric("Chance of measuring the target now", f"{cur[vt] ** 2 * 100:.1f}%")
    if rounds_done > k_opt:
        st.warning("Past the optimal number of rounds, the amplitude rotates past the "
                   "target and the success probability starts to fall.")
    st.caption(
        f"With {VN} accounts, about {k_opt} rounds are needed. A classical search would "
        f"check about {VN // 2} accounts on average. Blue bar = the account you are "
        "searching for; the red dashed line is the average amplitude."
    )

# ------------------------------------------------------------- tab 4
with tab4:
    st.write("Graphs saved from your earlier experiments "
             "(the PNG files must be in the same folder as app_v2.py).")
    saved = [
        ("grover_vs_classical.png", "Benchmark: queries, time and success rate vs N"),
        ("grover_iterations.png", "Effect of the number of Grover iterations"),
        ("hardware_vs_simulator.png", "Theory vs simulator vs real IBM hardware"),
    ]
    for path, caption in saved:
        if os.path.exists(path):
            st.image(path, caption=caption)
        else:
            st.info(f"{path} not found. Run the matching experiment first.")


# ------------------------------------------------------- tab: Grover Race
with tab_race:
    race_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grover_race.html")
    if os.path.exists(race_path):
        with open(race_path, encoding="utf-8") as f:
            screen_h = st.session_state.get("_race_h", 900)
            components.html(f.read(), height=screen_h, scrolling=True)
            st.caption("If the page looks cropped or you want more room, drag the "
                       "small resize handle in the bottom-right corner of the box above, "
                       "or open the full page below.")
            st.link_button("Open full-screen in a new tab",
                          "https://claude.ai/artifact/WVUm5tB71e2b4jrWATiE5N")
    else:
        st.info("grover_race.html not found. Put it in the same folder as app_v2.py.")