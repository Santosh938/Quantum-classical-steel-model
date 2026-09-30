### Table_14: Ablation_Study

| Exp ID   | Configuration                           |   MAE (HV) |   RMSE (HV) |     R2 |   Cost (s) |
|:---------|:----------------------------------------|-----------:|------------:|-------:|-----------:|
| A        | Classical Only                          |       12.8 |        15.4 | 0.9821 |      0.045 |
| B        | Classical + VQE Ground Energy E0        |       12.6 |        15.1 | 0.9828 |      1.12  |
| C        | Classical + Local Magnetization <Z_i>   |       12.5 |        14.9 | 0.9832 |      1.15  |
| D        | Classical + Pair Correlations <Z_i Z_j> |       12.3 |        14.7 | 0.9839 |      1.2   |
| E        | Classical + All Quantum Descriptors     |       12.1 |        14.4 | 0.9845 |      1.305 |
| F        | Hybrid (Coupled Physics Formulation)    |       12.1 |        14.4 | 0.9845 |      1.305 |