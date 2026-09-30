# Scientific Formulation: Reduced-Order Variational Quantum Eigensolver (VQE) for Steel Heat-Treatment Phase Transformations

---

## 1. Physical Problem Description
During heat treatment of low-alloy steel (such as AISI 4140), cooling from the austenitization regime triggers phase transformations governed by thermodynamic driving forces ($\Delta G^{\gamma \to \alpha}(T)$), interfacial boundary surface energies ($\gamma_{\alpha/\gamma}$), elastic transformation strain energies ($\Delta E_{\text{strain}}$), and local carbon diffusion/partitioning. 

In classical metallurgy, these cooperative transitions are traditionally approximated either as macro-phenomenological empirical kinetic curves (JMAK, Koistinen-Marburger) or continuum phase-field models requiring empirical gradient coefficients. The physical problem investigated here is whether a reduced-order quantum representation of cooperative multi-domain transformation energetics can capture inter-domain correlations and thermodynamic order parameter fluctuations beyond mean-field classical representations.

---

## 2. Reduced-Order Representation Justification
It is fundamentally impossible and scientifically disingenuous to claim that a near-term circuit of a few qubits simulates the full multi-billion-atom unit-cell lattice of bulk polycrystal AISI 4140. 

Instead, we formulate a **reduced-order mesoscopic domain cluster model**. The system volume is partitioned into a finite cluster of $N = 4$ interacting crystallographic sub-domains (e.g., adjacent austenite grain sub-volumes or Bain strain variant domains). Each qubit represents the structural order parameter $\eta_i$ of an individual domain.

---

## 3. State Variables
For each domain $i \in \{0, 1, \dots, N-1\}$:
- **Order Parameter** $\eta_i \in \{0, 1\}$:
  - $\eta_i = 0$: Parent FCC austenitic state ($\gamma$).
  - $\eta_i = 1$: Transformed product phase ($\alpha$, $\alpha'$, or bainitic ferrite BCC/BCT).
- **Temperature** $T$ (K): Controls the chemical free-energy driving force $\Delta G(T)$.
- **Carbon and Alloying Content** $C, Mn, Cr, Mo$: Modulate transformation barrier and strain energies.

---

## 4. Qubit State Mapping
We adopt a standard computational basis mapping:
$$|0\rangle_i \longleftrightarrow \text{Austenitic domain } (\gamma, \text{FCC})$$
$$|1\rangle_i \longleftrightarrow \text{Transformed product domain } (\alpha / \alpha', \text{BCC/BCT})$$

For an $N=4$ qubit cluster:
- $|0000\rangle$: Fully austenitic parent state ($f_\gamma = 1.0$).
- $|1111\rangle$: Fully transformed product state ($f_{\text{trans}} = 1.0$).
- Superpositions $\sum c_k |k\rangle$: Intermediate or partially transformed mixed-phase states with domain interface boundaries.

The continuous local transformed fraction is given by the single-qubit projector or Pauli-$Z$ observable:
$$\hat{n}_i = \frac{I - Z_i}{2}, \quad \langle \hat{n}_i \rangle \in [0, 1]$$

---

## 5. Hamiltonian Derivation
The total effective domain Hamiltonian $H$ is derived from the Ginzburg-Landau / Ising-type cooperative transformation energy:

$$H(T, C) = H_{\text{chemical}} + H_{\text{interface}} + H_{\text{constraint}}$$

### A. Chemical Driving Force Term
$$H_{\text{chemical}} = \sum_{i=0}^{N-1} h_i(T) Z_i$$
where:
$$h_i(T) = \frac{1}{2} \left[ \Delta G^{\gamma \to \alpha}(T) + \Delta E_{\text{strain}} \right]$$
- For $T > Ac3$: $\Delta G > 0 \implies h_i > 0$, energetic ground state is $|0\rangle$ ($Z_i = +1$).
- For $T < Ms$: $\Delta G \ll 0 \implies h_i < 0$, energetic ground state favors $|1\rangle$ ($Z_i = -1$).
- Near $T_0$: $h_i \approx 0$, critical phase equilibrium.

### B. Cooperative Interfacial Coupling Term
Adjacent domain boundaries incur interfacial boundary energy $\gamma_{\text{interface}}$ and autocatalytic strain accommodation:
$$H_{\text{interface}} = \sum_{\langle i, j \rangle} J_{ij} Z_i Z_j$$
where $J_{ij} > 0$ represents the energetic penalty for unaligned domains (creating a phase interface boundary $\gamma/\alpha$), promoting domain clustering (domain coarsening).

### C. Target Fraction Soft-Constraint
To anchor the reduced-order cluster to the instantaneous macroscopic temperature/kinetic target fraction $f_{\text{target}}(T)$:
$$H_{\text{constraint}} = \lambda \left( \sum_{i=0}^{N-1} \frac{I - Z_i}{2} - N \cdot f_{\text{target}} \right)^2$$
Expanding this operator yields additional diagonal single-qubit $Z_i$ and two-qubit $Z_i Z_j$ Pauli terms plus an identity offset.

---

## 6. Ansätze Architectures
1. **Hardware-Efficient Ansatz (HEA)**:
   - Alternating layers of single-qubit rotations $R_y(\theta_{i,l})$ and nearest-neighbor entangling gates (CZ / CNOT).
   - Minimizes circuit depth for near-term NISQ noisy devices.
2. **Problem-Inspired Subspace Ansatz (PIA)**:
   - Excitation-preserving parameterized Givens rotation gates:
     $$U_{XY}(\theta) = \exp\left(-i \frac{\theta}{2} (X_i Y_j - Y_i X_j)\right)$$
   - Preserves total transformed fraction within invariant topological sectors.

---

## 7. Quantum Observables
From the optimized VQE ground state $|\psi(\vec{\theta}^*)\rangle$:
1. **Ground State Energy**: $E_0 = \langle \psi | H | \psi \rangle$.
2. **Local Domain Magnetization**: $\langle Z_i \rangle = \langle \psi | Z_i | \psi \rangle$.
3. **Two-Domain Correlators**: $C_{ij} = \langle Z_i Z_j \rangle - \langle Z_i \rangle \langle Z_j \rangle$.
4. **Order Parameter Dispersion / Fluctuations**: $\chi = \sum_{i,j} C_{ij}$.
5. **Entanglement Entropy**: $S_E = -\text{Tr}(\rho_A \ln \rho_A)$.

---

## 8. Physical Interpretation of Observables
- **Ground State Energy $E_0$**: Represents the minimized configuration energy of the mesoscopic domain cluster under local undercooling.
- **Two-point Correlators $C_{ij}$**: Quantify spatial correlation between neighboring transformation fronts, reflecting cooperative nucleation or autocatalytic transformation (lath packet alignment).
- **Fluctuation Susceptibility $\chi$**: Peaks near transformation onset temperatures, providing a physical descriptor for phase transition sharpness.

---

## 9. Classical vs Quantum vs Hybrid Integration
- **Classical Model**: $P_C = f(X_C)$ where $X_C = \{ \text{composition}, T(t), f_{\text{classical}}, d_{\gamma}, \rho_{\text{dis}} \}$.
- **Hybrid Model**: $P_{CQ} = f(X_C, X_Q)$ where $X_Q = \{ E_0, \langle Z \rangle_{\text{avg}}, C_{\text{pair}}, \chi \}$.
- The hybrid formulation incorporates quantum correlation descriptors as non-linear cooperative correction factors to grain boundary nucleation and strain energy.

---

## 10. Strict Limitations and Assumptions
1. **Reduced Order**: A 4-qubit cluster represents a discrete mesoscopic domain ensemble, NOT direct atomic-scale electronic structure.
2. **Effective Parameters**: $h_i(T)$ and $J_{ij}$ are derived from continuum thermodynamic driving forces and interfacial energies.
3. **Simulation Noise**: Finite sampling (shot noise) and NISQ gate errors introduce variance in expectation values, which must be tracked via Monte Carlo uncertainty analysis.
4. **No Artificial Supremacy**: Quantum contribution must be benchmarked strictly against classical metrics ($R^2$, MAE, RMSE). If $\Delta R^2 \approx 0$, we conclude that classical models suffice.
