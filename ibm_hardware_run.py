"""
Run the Grover search on real IBM Quantum hardware and compare with
the ideal simulator and theory.

Setup:   pip install qiskit-ibm-runtime
Needs:   grover_password_search_v2.py in the same folder
Run:     python ibm_hardware_run.py
"""

import math
import random

import matplotlib.pyplot as plt
from qiskit import transpile
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

from grover_password_search_v2 import build_grover_circuit, optimal_iterations

QUBIT_SIZES = [2, 3]     # start small; try adding 4 later (much noisier)
SHOTS = 1024


def theory_probability(n, k):
    theta = math.asin(1 / math.sqrt(2 ** n))
    return math.sin((2 * k + 1) * theta) ** 2


def run_on_hardware(service, backend, qc, shots):
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    isa_circuit = pm.run(qc)
    depth = isa_circuit.depth()
    two_q = sum(v for k, v in isa_circuit.count_ops().items()
                if k in ("cx", "cz", "ecr", "rzz"))

    sampler = Sampler(mode=backend)
    job = sampler.run([isa_circuit], shots=shots)
    print(f"   Job ID: {job.job_id()}  (waiting in queue...)")
    result = job.result()
    counts = result[0].data.meas.get_counts()
    return counts, depth, two_q


def main():
    # Uses the credentials you saved earlier with save_account
    service = QiskitRuntimeService()
    backend = service.least_busy(operational=True, simulator=False,
                                 min_num_qubits=max(QUBIT_SIZES))
    print(f"Using backend: {backend.name} ({backend.num_qubits} qubits)\n")

    sim = AerSimulator()
    labels, theory, ideal, hardware = [], [], [], []

    for n in QUBIT_SIZES:
        N = 2 ** n
        target = random.randrange(N)
        k = optimal_iterations(N)
        qc, _ = build_grover_circuit(n, target, k)
        target_bits = format(target, f"0{n}b")
        print(f"n={n} (N={N}), target index={target} ({target_bits}), iterations={k}")

        # ideal simulator
        sim_counts = sim.run(transpile(qc, sim), shots=SHOTS).result().get_counts()
        p_sim = sim_counts.get(target_bits, 0) / SHOTS

        # real hardware
        hw_counts, depth, two_q = run_on_hardware(service, backend, qc, SHOTS)
        p_hw = hw_counts.get(target_bits, 0) / SHOTS
        top = sorted(hw_counts.items(), key=lambda x: -x[1])[:4]

        print(f"   Theory: {theory_probability(n, k):.1%} | "
              f"Simulator: {p_sim:.1%} | Hardware: {p_hw:.1%}")
        print(f"   Transpiled depth: {depth}, two-qubit gates: {two_q}")
        print(f"   Top hardware outcomes: {top}\n")

        labels.append(f"n={n}\n(N={N})")
        theory.append(theory_probability(n, k) * 100)
        ideal.append(p_sim * 100)
        hardware.append(p_hw * 100)

    # bar chart: theory vs simulator vs hardware
    x = range(len(labels))
    w = 0.25
    plt.figure(figsize=(8, 5))
    plt.bar([i - w for i in x], theory, w, label="Theory")
    plt.bar(list(x), ideal, w, label="Ideal simulator")
    plt.bar([i + w for i in x], hardware, w, label=f"Real hardware ({backend.name})")
    plt.xticks(list(x), labels)
    plt.ylabel("Success probability (%)")
    plt.title("Grover search: theory vs simulator vs real IBM hardware")
    plt.ylim(0, 105)
    for xs, vals in [([i - w for i in x], theory), (list(x), ideal), ([i + w for i in x], hardware)]:
        for xi, v in zip(xs, vals):
            plt.text(xi, v + 1, f"{v:.1f}%", ha="center", fontsize=9)
    plt.legend(loc="lower left"); plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig("hardware_vs_simulator.png", dpi=150)
    print("Saved plot: hardware_vs_simulator.png")
    plt.show()


if __name__ == "__main__":
    main()
