### Table_15: Computational_Cost

| Paradigm                 | Execution Platform       |   Qubits |   Circuit Depth |   Gate Count |   Iterations |   Runtime (s) |   Memory (MB) |
|:-------------------------|:-------------------------|---------:|----------------:|-------------:|-------------:|--------------:|--------------:|
| Classical Kinetics       | CPU (Single Core)        |        0 |               0 |            0 |          150 |         0.045 |          18.5 |
| Quantum VQE (Ideal)      | Qiskit Statevector       |        4 |               7 |           20 |           80 |         0.82  |          38   |
| Quantum VQE (Shots=2048) | Qiskit Aer Simulator     |        4 |               7 |           20 |           80 |         1.45  |          44   |
| Quantum VQE (Noisy Aer)  | Qiskit Aer Noise Model   |        4 |               7 |           20 |           80 |         1.82  |          46.5 |
| Hybrid Workflow          | Combined Classical + VQE |        4 |               7 |           20 |          230 |         1.865 |          52   |