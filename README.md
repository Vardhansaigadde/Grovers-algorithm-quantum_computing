# Quantum Unstructured Search: Grover's Algorithm for Database Retrieval

An educational internship project exploring **Grover's Quantum Search Algorithm** for unstructured database lookups, demonstrated through a synthetic username/email-to-password retrieval scenario. 

The project evaluates quantum search performance against classical linear search, provides an interactive **Streamlit** web application, visualizes quantum gate operations, and benchmarks real hardware execution on physical **IBM Quantum** processors (QPUs) using Qiskit.

---

> [!CAUTION]
> **Educational & Conceptual Simulation Only**
> This project is designed strictly for educational demonstrations of quantum search complexity on unstructured databases. In modern software engineering and cybersecurity, **passwords must never be retrievable**. Production systems must store only salted cryptographic one-way hashes (e.g., using Argon2, bcrypt, or PBKDF2), making reverse lookup or direct plaintext extraction fundamentally impossible by design.

---

## 🔬 Project Overview

Grover's algorithm provides a provable **quadratic speedup** for unstructured search problems over an item space of size $N = 2^n$:

- **Classical Linear Search:** Requires $O(N)$ evaluations in the worst case and $N/2$ evaluations on average.
- **Grover's Quantum Search:** Locates the marked item in $O(\sqrt{N})$ oracle queries with high probability through iterative amplitude amplification:
  $$k \approx \left\lfloor \frac{\pi}{4}\sqrt{N} \right\rfloor$$

This repository demonstrates:
1. **Mathematical Validation & Simulation:** Simulating state vector rotations and amplitude amplification on Qiskit's `AerSimulator`.
2. **Interactive Web Interface:** A user-friendly Streamlit application where users can search records by username or email, watch live step-by-step simulations, and inspect compiled quantum circuits.
3. **Physical Hardware Validation:** Executing quantum circuits on real IBM Quantum devices via Qiskit Runtime to analyze physical gate fidelity, circuit depth, and NISQ-era noise effects.
4. **Animated Comparative Race:** An interactive HTML/Canvas visualizer showcasing the speed differential between quantum amplitude amplification and classical step-by-step evaluation.

---

## 📁 Repository Structure

| File | Description |
| :--- | :--- |
| [`app_v2.py`](file:///c:/Users/vardh/OneDrive/Desktop/Internship%20project/app_v2.py) | **Main Web App:** Realistic Streamlit interface supporting username/email search, synthetic profiles, live simulation, and circuit inspection. |
| [`app.py`](file:///c:/Users/vardh/OneDrive/Desktop/Internship%20project/app.py) | Baseline Streamlit UI (v1) for username-to-password search with interactive Grover iterations and circuit plotting. |
| [`grover_password_search_v2.py`](file:///c:/Users/vardh/OneDrive/Desktop/Internship%20project/grover_password_search_v2.py) | Core quantum search engine using real dictionary passwords (`10k-most-common.txt`), benchmark suite, and iteration analysis. |
| [`grover_password_search.py`](file:///c:/Users/vardh/OneDrive/Desktop/Internship%20project/grover_password_search.py) | Baseline CLI implementation comparing classical linear search vs Grover search on synthetic records. |
| [`ibm_hardware_run.py`](file:///c:/Users/vardh/OneDrive/Desktop/Internship%20project/ibm_hardware_run.py) | Script executing Grover circuits on physical IBM Quantum QPUs via Qiskit Runtime, comparing theory, Aer simulator, and physical hardware. |
| [`grover_race.html`](file:///c:/Users/vardh/OneDrive/Desktop/Internship%20project/grover_race.html) | Interactive browser-based animated race comparing quantum amplitude growth vs classical linear search. |
| [`10k-most-common.txt`](file:///c:/Users/vardh/OneDrive/Desktop/Internship%20project/10k-most-common.txt) | Curated list of 10,000 common passwords from SecLists used to populate realistic database entries. |
| [`grover_vs_classical.png`](file:///c:/Users/vardh/OneDrive/Desktop/Internship%20project/grover_vs_classical.png) | Benchmark plot displaying the $O(\sqrt{N})$ quantum scaling advantage over classical $O(N)$ linear search. |
| [`grover_iterations.png`](file:///c:/Users/vardh/OneDrive/Desktop/Internship%20project/grover_iterations.png) | Visualization of Grover success probability over iterations, demonstrating state over-rotation. |
| [`hardware_vs_simulator.png`](file:///c:/Users/vardh/OneDrive/Desktop/Internship%20project/hardware_vs_simulator.png) | Empirical bar chart comparing theoretical success probability, Aer simulator, and physical IBM Quantum hardware. |
| [`requirements.txt`](file:///c:/Users/vardh/OneDrive/Desktop/Internship%20project/requirements.txt) | Project dependencies including Qiskit, Qiskit-Aer, Qiskit-IBM-Runtime, Streamlit, Pandas, Faker, and Matplotlib. |
| [`.gitignore`](file:///c:/Users/vardh/OneDrive/Desktop/Internship%20project/.gitignore) | Git exclusions for Python virtual environments (`.venv`), bytecode caches (`__pycache__`), and Streamlit configurations. |

---

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.10+ (tested on Python 3.12 - 3.14)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### 2. Create and Activate a Virtual Environment
```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Configure IBM Quantum Credentials
If you plan to run jobs on physical quantum processors via `ibm_hardware_run.py`:
1. Create a free account at [quantum.ibm.com](https://quantum.ibm.com/).
2. Copy your API token from the dashboard.
3. Save your credentials locally (done once):
   ```python
   from qiskit_ibm_runtime import QiskitRuntimeService
   QiskitRuntimeService.save_account(channel="ibm_quantum", token="YOUR_IBM_QUANTUM_TOKEN")
   ```

---

## 🚀 How to Run

### 1. Launch the Streamlit Web Application
Run the enhanced interactive dashboard:
```bash
streamlit run app_v2.py
```
*(Alternatively, run the baseline UI via `streamlit run app.py`).*

Features in the web app:
- Search database entries by **Username** or **Email address**.
- Inspect synthetic profiles generated via Faker paired with common passwords.
- Step through the Grover phase inversion (Oracle) and amplitude amplification (Diffuser).
- View circuit diagrams rendered via Matplotlib / LaTeX (`pylatexenc`).

### 2. Run the Grover CLI Suite
Run the CLI engine in one of three modes:

- **Interactive Demo (6 qubits, $N=64$ database entries):**
  ```bash
  python grover_password_search_v2.py demo
  ```
- **Classical vs. Quantum Scaling Benchmark ($N = 4$ to $N = 1024$):**
  ```bash
  python grover_password_search_v2.py benchmark
  ```
  *(Generates `grover_vs_classical.png`).*
- **Analyze Grover Iterations & Over-rotation:**
  ```bash
  python grover_password_search_v2.py iterations
  ```
  *(Generates `grover_iterations.png`).*

### 3. Execute on Real IBM Quantum Hardware
Submit Grover search circuits to an operational IBM Quantum superconducting backend:
```bash
python ibm_hardware_run.py
```
- Selects the least-busy physical QPU meeting the qubit criteria.
- Transpiles the circuit into the target backend's native instruction set (basis gates & coupling map).
- Compares measured probability distributions against the ideal Aer simulator and theoretical predictions, saving the results in `hardware_vs_simulator.png`.

### 4. Open the Animated Browser Race
Double-click [`grover_race.html`](file:///c:/Users/vardh/OneDrive/Desktop/Internship%20project/grover_race.html) or open it in any web browser to see an animated side-by-side visualization of classical step-by-step checking versus quantum amplitude amplification.

---

## 📊 Summary of Results

### 1. Quantum vs. Classical Search Complexity
- For an unstructured search space of $N = 64$ ($n=6$ qubits), classical linear search requires an average of **32 comparisons** (up to 64 worst case).
- Grover's algorithm finds the target in only **$k = 6$ oracle evaluations** ($\approx \frac{\pi}{4}\sqrt{64} = 6.28$), achieving $>99\%$ measurement probability on the ideal simulator.

### 2. Optimal Iterations & Over-Rotation
Amplitude amplification acts as a geometric rotation in the 2D state space spanned by the target state $|w\rangle$ and the uniform superposition $|s'\rangle$. Executing more than the optimal number of iterations causes the state vector to rotate past $|w\rangle$, reducing the probability of measuring the correct answer (observed experimentally in `grover_iterations.png`).

### 3. Physical Hardware Execution (NISQ Realities)
Executing on physical IBM Quantum QPUs highlights the current challenges of NISQ computing:
- **Simulator ($n=2, N=4$):** $100\%$ target state fidelity.
- **Physical Hardware ($n=2, N=4$):** $\approx 78\%$ - $85\%$ success rate.
- **Physical Hardware ($n=3, N=8$):** Success rate drops due to increased circuit depth, multi-qubit CNOT/ECR gate error rates, and decoherence ($T_1$ and $T_2$ times).

---

## 📜 License
This project was developed for educational and internship research purposes.
