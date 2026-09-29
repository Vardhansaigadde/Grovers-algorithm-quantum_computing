"""
Grover's Algorithm: Username -> Password Retrieval
vs Classical Linear Search

Setup:  pip install qiskit qiskit-aer matplotlib
Run:    python grover_password_search.py demo
        python grover_password_search.py benchmark
"""

import math
import random
import string
import sys
import time

import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


# ---------------------------------------------------------------- dataset
def make_dataset(n_qubits, seed=42):
    """Create N = 2^n fake (username, password) pairs.
    Replace this with a CSV loader for a real dataset subset."""
    random.seed(seed)
    N = 2 ** n_qubits
    chars = string.ascii_letters + string.digits
    data = []
    for i in range(N):
        user = f"user{i:04d}"
        pwd = "".join(random.choices(chars, k=8))
        data.append((user, pwd))
    return data


# ------------------------------------------------------- classical search
def classical_search(data, target_user):
    """Linear search. Returns (index, comparisons, seconds)."""
    start = time.perf_counter()
    comparisons = 0
    found = -1
    for i, (user, _) in enumerate(data):
        comparisons += 1
        if user == target_user:
            found = i
            break
    return found, comparisons, time.perf_counter() - start


# ---------------------------------------------------------- Grover pieces
def multi_controlled_z(qc, n):
    """Apply Z on the all-ones state of n qubits."""
    if n == 1:
        qc.z(0)
    else:
        qc.h(n - 1)
        qc.mcx(list(range(n - 1)), n - 1)
        qc.h(n - 1)


def oracle(qc, n, target_index):
    """Flip the phase of |target_index>.
    NOTE: built with prior knowledge of the target (standard for a
    search demonstration). A real oracle would compare usernames
    inside the circuit, which is far more expensive."""
    zeros = [i for i in range(n) if not (target_index >> i) & 1]
    for q in zeros:
        qc.x(q)
    multi_controlled_z(qc, n)
    for q in zeros:
        qc.x(q)


def diffusion(qc, n):
    """Inversion about the mean."""
    qc.h(range(n))
    qc.x(range(n))
    multi_controlled_z(qc, n)
    qc.x(range(n))
    qc.h(range(n))


def optimal_iterations(N):
    return max(1, math.floor(math.pi / 4 * math.sqrt(N)))


def build_grover_circuit(n, target_index, iterations=None):
    N = 2 ** n
    if iterations is None:
        iterations = optimal_iterations(N)
    qc = QuantumCircuit(n)
    qc.h(range(n))                      # uniform superposition
    for _ in range(iterations):
        oracle(qc, n, target_index)     # 1 oracle call per iteration
        diffusion(qc, n)
    qc.measure_all()
    return qc, iterations


def grover_search(n, target_index, shots=1024, iterations=None, backend=None):
    """Returns (found_index, oracle_calls, success_prob, seconds, counts)."""
    backend = backend or AerSimulator()
    start = time.perf_counter()
    qc, iters = build_grover_circuit(n, target_index, iterations)
    compiled = transpile(qc, backend)
    counts = backend.run(compiled, shots=shots).result().get_counts()
    elapsed = time.perf_counter() - start

    best = max(counts, key=counts.get)
    found = int(best, 2)                # Qiskit bitstrings are q_{n-1}...q_0
    success_prob = counts.get(format(target_index, f"0{n}b"), 0) / shots
    return found, iters, success_prob, elapsed, counts


# ------------------------------------------------------------------- demo
def demo():
    n = 4  # 16 entries; try 3 to 8
    data = make_dataset(n)
    print(f"Dataset size: {len(data)} entries ({n} qubits)")
    print("Sample usernames:", [u for u, _ in data[:3]], "...")
    username = input("\nEnter a username (e.g. user0007): ").strip()

    idx_lookup = {u: i for i, (u, _) in enumerate(data)}
    if username not in idx_lookup:
        print("Username not in dataset.")
        return
    target_index = idx_lookup[username]   # used to build the oracle

    c_idx, c_cmp, c_time = classical_search(data, username)
    g_idx, g_calls, g_prob, g_time, _ = grover_search(n, target_index)

    print("\n=========== RESULTS ===========")
    print(f"Username           : {username}")
    print(f"Password retrieved : {data[g_idx][1]}")
    print(f"Grover found index : {g_idx} (correct: {g_idx == target_index})")
    print("\n--- Classical linear search ---")
    print(f"Comparisons        : {c_cmp}")
    print(f"Time               : {c_time * 1e6:.2f} microseconds")
    print("\n--- Grover (simulator) ---")
    print(f"Oracle calls       : {g_calls}")
    print(f"Success probability: {g_prob:.2%}")
    print(f"Time               : {g_time * 1e3:.2f} ms")
    print("\nNote: the speedup is in query count, not simulator runtime.")


# -------------------------------------------------------------- benchmark
def benchmark(max_qubits=10, trials=50):
    ns, classical_q, grover_q = [], [], []
    classical_t, grover_t, probs = [], [], []
    backend = AerSimulator()

    print(f"{'n':>2} {'N':>6} {'classical':>10} {'grover':>7} "
          f"{'succ%':>7} {'c_time(ms)':>11} {'g_time(ms)':>11}")
    for n in range(2, max_qubits + 1):
        N = 2 ** n
        data = make_dataset(n)
        c_cmp_sum = c_t_sum = g_t_sum = p_sum = 0
        for _ in range(trials):
            t = random.randrange(N)
            user = data[t][0]
            _, cmp_, ct = classical_search(data, user)
            _, calls, prob, gt, _ = grover_search(n, t, backend=backend)
            c_cmp_sum += cmp_; c_t_sum += ct; g_t_sum += gt; p_sum += prob
        ns.append(n)
        classical_q.append(c_cmp_sum / trials)
        grover_q.append(calls)
        classical_t.append(c_t_sum / trials * 1e3)
        grover_t.append(g_t_sum / trials * 1e3)
        probs.append(p_sum / trials)
        print(f"{n:>2} {N:>6} {classical_q[-1]:>10.1f} {calls:>7} "
              f"{probs[-1]*100:>6.1f}% {classical_t[-1]:>11.4f} {grover_t[-1]:>11.2f}")

    Ns = [2 ** n for n in ns]
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.5))

    ax[0].plot(Ns, classical_q, "o-", label="Classical (avg comparisons)")
    ax[0].plot(Ns, grover_q, "s-", label="Grover (oracle calls)")
    ax[0].set_xscale("log", base=2); ax[0].set_yscale("log")
    ax[0].set(xlabel="Dataset size N", ylabel="Queries",
              title="Query count vs N")
    ax[0].legend(); ax[0].grid(True, alpha=0.3)

    ax[1].plot(Ns, classical_t, "o-", label="Classical")
    ax[1].plot(Ns, grover_t, "s-", label="Grover (simulator)")
    ax[1].set_xscale("log", base=2); ax[1].set_yscale("log")
    ax[1].set(xlabel="Dataset size N", ylabel="Time (ms)",
              title="Wall-clock time vs N")
    ax[1].legend(); ax[1].grid(True, alpha=0.3)

    ax[2].plot(Ns, [p * 100 for p in probs], "d-", color="green")
    ax[2].set_xscale("log", base=2); ax[2].set_ylim(0, 105)
    ax[2].set(xlabel="Dataset size N", ylabel="Success probability (%)",
              title="Grover success rate")
    ax[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("grover_vs_classical.png", dpi=150)
    print("\nSaved plot: grover_vs_classical.png")
    plt.show()


def iterations_experiment(n=8, max_iter=30, shots=1024):
    N = 2 ** n
    target = random.randrange(N)
    backend = AerSimulator()
    iters, sim_prob, theory_prob = [], [], []
    theta = math.asin(1 / math.sqrt(N))

    for k in range(0, max_iter + 1):
        if k == 0:
            # no Grover iterations: just superposition + measurement
            qc = QuantumCircuit(n)
            qc.h(range(n))
            qc.measure_all()
            counts = backend.run(transpile(qc, backend), shots=shots).result().get_counts()
            p = counts.get(format(target, f"0{n}b"), 0) / shots
        else:
            _, _, p, _, _ = grover_search(n, target, shots=shots,
                                          iterations=k, backend=backend)
        iters.append(k)
        sim_prob.append(p * 100)
        theory_prob.append(math.sin((2 * k + 1) * theta) ** 2 * 100)

    best_k = optimal_iterations(N)
    plt.figure(figsize=(9, 5))
    plt.plot(iters, sim_prob, "o-", label="Simulated")
    plt.plot(iters, theory_prob, "--", label="Theory: sin²((2k+1)θ)")
    plt.axvline(best_k, color="red", linestyle=":", label=f"Optimal k = {best_k}")
    plt.xlabel("Number of Grover iterations (k)")
    plt.ylabel("Success probability (%)")
    plt.title(f"Effect of iteration count (N = {N})")
    plt.legend(); plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("grover_iterations.png", dpi=150)
    print("Saved plot: grover_iterations.png")
    plt.show()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "demo"
    if mode == "benchmark":
        benchmark(trials=50)
    elif mode == "iterations":
        iterations_experiment()
    else:
        demo()
