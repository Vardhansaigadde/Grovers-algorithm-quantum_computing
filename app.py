"""
Streamlit UI for the Grover username -> password search project.

Setup:  pip install streamlit pandas
Needs:  grover_password_search_v2.py and 10k-most-common.txt in the same folder
Run:    streamlit run app.py
"""

import math
import os

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from grover_password_search_v2 import (
    PASSWORD_FILE,
    build_grover_circuit,
    classical_search,
    grover_search,
    load_dataset,
    optimal_iterations,
)

st.set_page_config(page_title="Grover Password Search", page_icon="🔍", layout="wide")
st.title("🔍 Grover's Algorithm: Username → Password Search")
st.caption("Quantum search vs classical linear search (simulated with Qiskit Aer)")

# ---------------------------------------------------------------- sidebar
st.sidebar.header("Settings")
n = st.sidebar.slider("Number of qubits (n)", 2, 10, 6)
N = 2 ** n
st.sidebar.write(f"Dataset size: **{N}** entries")
st.sidebar.write(f"Optimal Grover iterations: **{optimal_iterations(N)}**")
st.sidebar.write(f"Classical average: about **{N // 2}** comparisons")
st.sidebar.info("Usernames are synthetic. Passwords come from a public "
                "common-password list (SecLists).")


@st.cache_data
def get_data(n_qubits):
    return load_dataset(PASSWORD_FILE, n_qubits)


try:
    data = get_data(n)
except FileNotFoundError:
    st.error(f"Could not find '{PASSWORD_FILE}'. Put it in the same folder as app.py.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["Search demo", "Iterations explorer", "Saved results"])

# -------------------------------------------------------------- tab 1: demo
with tab1:
    usernames = [u for u, _ in data]
    username = st.selectbox("Choose a username (you can type to search)",
                            usernames, index=(N * 3) // 4)

    if st.button("Run search", type="primary"):
        target = usernames.index(username)

        c_idx, c_cmp, c_time = classical_search(data, username)
        with st.spinner("Running Grover circuit..."):
            g_idx, g_calls, g_prob, g_time, counts = grover_search(n, target)

        if g_idx == target:
            st.success(f"Grover found index {g_idx}. "
                       f"Password for **{username}**: `{data[g_idx][1]}`")
        else:
            st.warning(f"Grover returned index {g_idx}, expected {target}. "
                       "Try running again.")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Classical linear search")
            a, b = st.columns(2)
            a.metric("Comparisons", c_cmp)
            b.metric("Time", f"{c_time * 1e6:.1f} µs")
        with col2:
            st.subheader("Grover (simulator)")
            a, b, c = st.columns(3)
            a.metric("Oracle calls", g_calls)
            b.metric("Success prob.", f"{g_prob:.1%}")
            c.metric("Time", f"{g_time * 1e3:.0f} ms")

        st.caption("The speedup is in query count. On a classical simulator, "
                   "Grover's wall-clock time is longer than a simple linear search.")

        st.subheader("Measurement results (top 8 states)")
        top = sorted(counts.items(), key=lambda x: -x[1])[:8]
        df = pd.DataFrame(
            [(f"{int(s, 2)} - {data[int(s, 2)][0]}", c) for s, c in top],
            columns=["entry", "shots"],
        ).set_index("entry")
        st.bar_chart(df)

        if n <= 4:
            with st.expander("Show the Grover circuit"):
                try:
                    qc, _ = build_grover_circuit(n, target)
                    st.pyplot(qc.draw("mpl"))
                except Exception as e:
                    st.info(f"Circuit drawing needs pylatexenc (pip install pylatexenc). {e}")
        else:
            st.caption("Lower the qubit slider to 4 or less to see the circuit diagram.")

# ------------------------------------------------ tab 2: iterations explorer
with tab2:
    st.write("See how the success probability changes with the number of "
             "Grover iterations, and what happens if you overshoot.")
    k_max = 2 * optimal_iterations(N) + 4
    k = st.slider("Number of iterations (k)", 0, k_max, optimal_iterations(N))
    theta = math.asin(1 / math.sqrt(N))
    theory = [math.sin((2 * i + 1) * theta) ** 2 * 100 for i in range(k_max + 1)]

    if k >= 1:
        target_i = N // 2
        _, _, p_sim, _, _ = grover_search(n, target_i, iterations=k)
        st.metric("Simulated success probability", f"{p_sim:.1%}",
                  delta=f"theory: {theory[k]:.1f}%", delta_color="off")
    else:
        st.metric("Success probability (random guess)", f"{theory[0]:.2f}%")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(range(k_max + 1), theory, "--", label="Theory")
    ax.plot([k], [theory[k]], "ro", markersize=10, label=f"k = {k}")
    ax.axvline(optimal_iterations(N), color="green", linestyle=":", label="Optimal k")
    ax.set(xlabel="Iterations (k)", ylabel="Success probability (%)", ylim=(0, 105))
    ax.grid(alpha=0.3); ax.legend()
    st.pyplot(fig)

# ---------------------------------------------------- tab 3: saved results
with tab3:
    st.write("Graphs saved from your earlier experiments "
             "(files must be in the same folder as app.py).")
    files = [
        ("grover_vs_classical.png", "Benchmark: queries, time and success rate vs N"),
        ("grover_iterations.png", "Effect of iteration count"),
        ("hardware_vs_simulator.png", "Theory vs simulator vs real IBM hardware"),
    ]
    for path, caption in files:
        if os.path.exists(path):
            st.image(path, caption=caption, use_container_width=True)
        else:
            st.info(f"{path} not found. Run the matching experiment first.")
