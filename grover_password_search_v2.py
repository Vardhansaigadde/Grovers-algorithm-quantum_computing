"""
Grover's Algorithm: Username -> Password Retrieval (v2, real dataset)

Setup:  pip install qiskit qiskit-aer matplotlib faker
Needs:  10k-most-common.txt (from SecLists) in the same folder

Run:    python grover_password_search_v2.py demo
        python grover_password_search_v2.py benchmark
        python grover_password_search_v2.py iterations
"""

import math
import random
import sys
import time

import matplotlib.pyplot as plt
from faker import Faker
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

PASSWORD_FILE = "10k-most-common.txt"   # change if your file name differs
DEMO_QUBITS = 6                         # 2^6 = 64 entries for the demo


# ---------------------------------------------------------------- dataset
def load_dataset(path, n_qubits, seed=42):
    """Load N = 2^n passwords from a text file and pair each with a
    synthetic unique username (usernames are generated, not real)."""
    N = 2 ** n_qubits
    with open(path, encoding="utf-8", errors="ignore") as f:
        passwords = [line.strip() for line in f if line.strip()]
    if len(passwords) < N:
        raise ValueError(f"File has only {len(passwords)} passwords, need {N}.")

    rng = random.Random(seed)            # local RNG, doesn't touch global one
    passwords = rng.sample(passwords, N)

    fake = Faker()
    Faker.seed(seed)
    usernames = [fake.unique.user_name() for _ in range(N)]
    return list(zip(usernames, passwords))


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
    if n == 1:
        qc.z(0)
    else:
        qc.h(n - 1)
        qc.mcx(list(range(n - 1)), n - 1)
        qc.h(n - 1)


def oracle(qc, n, target_index):
    """Flip the phase of |target_index>.
    Built with prior knowledge of the target (standard for a search demo)."""
    zeros = [i for i in range(n) if not (target_index >> i) & 1]
    for q in zeros:
        qc.x(q)
    multi_controlled_z(qc, n)
    for q in zeros:
        qc.x(q)


def diffusion(qc, n):
    qc.h(range(n))
    qc.x(range(n))
    multi_controlled_z(qc, n)
    qc.x(range(n))
    qc.h(range(n))


def optimal_iterations(N):
    return max(1, math.floor(math.pi / 4 * math.sqrt(N)))


def build_grover_circuit(n, target_index, iterations=None):
    if iterations is None:
        iterations = optimal_iterations(2 ** n)
    qc = QuantumCircuit(n)
    qc.h(range(n))
    for _ in range(iterations):
        oracle(qc, n, target_index)
        diffusion(qc, n)
    qc.measure_all()
    return qc, iterations


def grover_search(n, target_index, shots=1024, iterations=None, backend=None):
    """Returns (found_index, oracle_calls, success_prob, seconds, counts)."""
    backend = backend or AerSimulator()
    start = time.perf_counter()
    qc, iters = build_grover_circuit(n, target_index, iterations)
    counts = backend.run(transpile(qc, backend), shots=shots).result().get_counts()
    elapsed = time.perf_counter() - start
    found = int(max(counts, key=counts.get), 2)
    prob = counts.get(format(target_index, f"0{n}b"), 0) / shots
    return found, iters, prob, elapsed, counts


# ------------------------------------------------------------------- demo
def demo():
    n = DEMO_QUBITS
    data = load_dataset(PASSWORD_FILE, n)
    print(f"Dataset size: {len(data)} entries ({n} qubits)")
    print("Sample usernames:", [u for u, _ in data[:5]])
    username = input("\nEnter a username exactly as shown above: ").strip()

    lookup = {u: i for i, (u, _) in enumerate(data)}
    if username not in lookup:
        print("Username not in dataset.")
        return
    target = lookup[username]

    _, c_cmp, c_time = classical_search(data, username)
    g_idx, g_calls, g_prob, g_time, _ = grover_search(n, target)

    print("\n=========== RESULTS ===========")
    print(f"Username           : {username}")
    print(f"Password retrieved : {data[g_idx][1]}")
    print(f"Grover found index : {g_idx} (correct: {g_idx == target})")
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
    ns, cq, gq, ct, gt, probs = [], [], [], [], [], []
    backend = AerSimulator()

    print(f"{'n':>2} {'N':>6} {'classical':>10} {'grover':>7} "
          f"{'succ%':>7} {'c_time(ms)':>11} {'g_time(ms)':>11}")
    for n in range(2, max_qubits + 1):
        N = 2 ** n
        data = load_dataset(PASSWORD_FILE, n)
        cs = ts = gs = ps = 0
        for _ in range(trials):
            t = random.randrange(N)
            _, cmp_, tc = classical_search(data, data[t][0])
            _, calls, p, tg, _ = grover_search(n, t, backend=backend)
            cs += cmp_; ts += tc; gs += tg; ps += p
        ns.append(n)
        cq.append(cs / trials); gq.append(calls)
        ct.append(ts / trials * 1e3); gt.append(gs / trials * 1e3)
        probs.append(ps / trials)
        print(f"{n:>2} {N:>6} {cq[-1]:>10.1f} {calls:>7} "
              f"{probs[-1]*100:>6.1f}% {ct[-1]:>11.4f} {gt[-1]:>11.2f}")

    Ns = [2 ** n for n in ns]
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.5))
    ax[0].plot(Ns, cq, "o-", label="Classical (avg comparisons)")
    ax[0].plot(Ns, gq, "s-", label="Grover (oracle calls)")
    ax[0].set(xlabel="Dataset size N", ylabel="Queries", title="Query count vs N")
    ax[1].plot(Ns, ct, "o-", label="Classical")
    ax[1].plot(Ns, gt, "s-", label="Grover (simulator)")
    ax[1].set(xlabel="Dataset size N", ylabel="Time (ms)", title="Wall-clock time vs N")
    ax[2].plot(Ns, [p * 100 for p in probs], "d-", color="green")
    ax[2].set(xlabel="Dataset size N", ylabel="Success probability (%)",
              title="Grover success rate", ylim=(0, 105))
    for a in ax:
        a.set_xscale("log", base=2); a.grid(alpha=0.3)
    for a in ax[:2]:
        a.set_yscale("log"); a.legend()
    plt.tight_layout()
    plt.savefig("grover_vs_classical.png", dpi=150)
    print("\nSaved plot: grover_vs_classical.png")
    plt.show()


# ------------------------------------------------- iterations experiment
def iterations_experiment(n=8, max_iter=30, shots=1024):
    N = 2 ** n
    target = random.randrange(N)
    backend = AerSimulator()
    theta = math.asin(1 / math.sqrt(N))
    iters, sim_prob, theory_prob = [], [], []

    for k in range(0, max_iter + 1):
        if k == 0:
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
        benchmark()
    elif mode == "iterations":
        iterations_experiment()
    else:
        demo()
