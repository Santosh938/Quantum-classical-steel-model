### Table_06: VQE_Configuration

| Parameter          | Configuration                                  |   Parameter Count |   Max Iterations | Shots   | Error Rates               |
|:-------------------|:-----------------------------------------------|------------------:|-----------------:|:--------|:--------------------------|
| Ansatz             | Hardware-Efficient (RealAmplitudes / Ry-CZ)    |                12 |              nan | nan     | nan                       |
| Optimizer          | COBYLA                                         |               nan |              150 | nan     | nan                       |
| Ideal Backend      | StatevectorSimulator (Exact)                   |               nan |              nan | N/A     | nan                       |
| Shot-Based Backend | AerSimulator                                   |               nan |              nan | 2048    | nan                       |
| Noisy Backend      | AerSimulator with Depolarizing + Readout Error |               nan |              nan | nan     | p_depol=0.005, p_ro=0.015 |