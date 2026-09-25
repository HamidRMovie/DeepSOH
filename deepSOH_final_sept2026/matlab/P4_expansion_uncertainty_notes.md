<!-- Source for sigma3(iExp) in P4_settings.m. Produced 2026-09-24 by three independent literature searches; every cited number was checked against its source by a separate verifier, and 11 findings that could not be confirmed were dropped. -->

# 3-sigma measurement uncertainty for irreversible expansion from a sensor in a vehicle pack

## 1. Recommended value

- **Recommended: 10 um at 3 sigma** for each reading, taken once per cycle. This gives sigma = 3.3 um.
- **Optimistic: 5 um at 3 sigma** (sigma = 1.7 um).
- **Pessimistic: 20 um at 3 sigma** (sigma = 6.7 um).

**What each value assumes**
- **Recommended.** A displacement sensor small enough to fit in a pack, either inductive or eddy-current. It sits at the centre of the cell face and is calibrated for each cell when installed. It is read after a rest at an SOC set by voltage. The reading is corrected for temperature using the measured cell temperature.
- **Optimistic.** The same setup, plus one of two things: a slow bias state in the estimator, or zeroing the sensor again at regular intervals. Readings are also taken close to the reference temperature.
- **Pessimistic.** Force or strain sensing (load cell, thin-film force sensor, strain gauge or FBG). It also covers a displacement sensor whose drift is not estimated.

**These values are engineering judgment.** The literature gives no end-to-end accuracy for expansion measured in a vehicle. Only two in-pack demonstrations were found, and neither reports an expansion accuracy:
- 76-cell Ford Focus HEV pack (Knobloch 2017). The small expansion of the hard-cased cells limited the sensors' use.
- 96-cell, 13.8 kWh pack fitted with FBGs (Meyer et al., as reviewed in Su 2021).

All three values are built up from the lab error terms below.

**For the parameter file:** sigma_exp_irr = 10/3 um (recommended). Use 5/3 um and 20/3 um as the optimistic and pessimistic cases.

## 2. From sensor resolution to accuracy in the vehicle

**Resolution is not what limits accuracy.**
- A lab displacement gauge resolves 0.1 um with 1 um accuracy (Keyence GT2, Oh 2014).
- Capacitive probes are specified at +/-0.012 um (Michelini 2023). A bellows dilatometer resolves 0.38 nm (Wang 2026).
- Short-term noise in pack-style force sensing is also small. One load cell had 0.2 N noise SD (Samad 2016). At the 0.35 N per um stiffness of a Poron-buffered stack (Figueroa-Santos 2020), that is about 0.6 um. The two fixtures differ, so this conversion is only indicative.
- An FBG interrogator reads 1 pm, which is about 1 microstrain or 0.1 C (Sommer 2014).

None of this resolution carries through to a reading in a vehicle. Five other terms set the error.

**(a) Accuracy of a sensor that fits in a pack**

Lab gauges are too large and too costly for a pack. Sensors that do fit are less accurate:
- The UM inductive sensor costs under $20. It had a maximum error of 3.2 um against a 1 um reference (Pannala 2022).
- A PCB eddy-current setup resolves better than 4 nm but has only about 7 um absolute accuracy (Brauchle 2023).
- Laser triangulation reaches about 8 um (Krause 2024). Laser sensors on a prismatic cell had +/-7.5 um linearity error (Clerici 2021).
- GE built eddy-current coils under 100 um thick, with a 0 to 2 mm range, to sit between cells in HEV packs. No accuracy was given (Plotnikov 2015).

Budget at 3 sigma (optimistic / recommended / pessimistic): 3 / 5 / 8 um.

**(b) Temperature**

- The UM 5 Ah NMC111/graphite pouch in its 5 psi spring and Poron fixture has a fitted thermal coefficient of 1.48 um/K. This value lumps the cell and the fixture together (Mohtat 2021, dissertation).
- Another pouch cell measured 2.07 um/K (Schmider 2023).
- Half of an aluminium fixture moved 6 um for a 2 K change in ambient (Clerici 2021). The pack structure therefore adds a term of its own.

A vehicle cannot hold the cell at 25 C when the reading is taken, so temperature must be measured and corrected for:
- A 0.5 C RTD (Samad 2016) leaves about 0.7 um.
- The coefficient itself is the larger error, because the pack is not the lab fixture. A 20% error in the coefficient, 10 K away from the reference temperature, gives 3 um. This is my assumption.
- Suppose the correction uses a pack-level temperature instead of the cell temperature. Cells can then differ by 5 C, the usual design target for pack thermal management (Tang 2020). That gives about 7 um.

Budget: 1 / 3 / 7 um.

**(c) Reversible expansion left in the reading**

- The reversible swing is about 100 um per full charge on 5 Ah HEV cells. Oh 2014 measured 99.8 and 103.2 um; Plotnikov 2015 measured 100 to 125 um. So each 1% of SOC error at the reference point leaves up to about 1 um.
- Expansion shows hysteresis between charge and discharge even at 0.05C. Peak expansion rises with C-rate. Readings settle within about 0.5 h (Schmider 2023).
- The UM protocol rests the cell 3 h at 25 C before the reference reading (Mohtat 2021).

Budget: 1 / 2 / 5 um.

**(d) Slow drift and creep**

This is the largest term for any sensor that presses on compliant pack materials:
- A load cell against a Poron pad drifted 3 to 6 N between two tests two months apart. At 0.35 N per um, that is about 9 to 17 um (my conversion). The authors state that every mechanical measurement drifts even after calibration, and they model the drift as a bias state (Figueroa-Santos 2020).
- The same load cell's accuracy, 4.45 N, equals about 13 um at that stiffness (my conversion).
- Over 6000 cycles, absolute force in a module fixture did not change monotonically. The authors attribute this to creep of polymer layers (Samad 2016).
- Bolted and spring fixtures lose up to 20% of stack pressure to early relaxation (Wang 2026).

Budget:
- 1 um if drift is estimated as a bias state.
- 5 um if it is partly corrected, for example by zeroing at service. This is judgment for a displacement sensor, roughly a third of the two-month force drift.
- 15 um if it is not corrected over months.

**(e) Gain and sensor placement**

- Expansion near the current-collector edges is less than half the centre value (Oh 2014). An off-centre sensor therefore reads a scaled-down growth.
- Aged 60 Ah cells show a local thickness interquartile width of 0.1 mm (Michelini 2023).
- Four nominally identical cells with strain gauges differed by about +/-18% in full-swing strain (Hendricks 2023). Each sensor and cell pair therefore needs its own calibration.
- About 150 um of irreversible expansion builds up over life (Mohtat 2021). That leaves roughly 100 um of growth after hand-over at about 50 um. A 1 to 5% gain error after calibration gives 1 to 5 um. Without per-cell calibration, 18% of that growth would be about 18 um.

Budget: 1 / 3 / 5 um.

**Combining the terms (judgment)**

I treat each accuracy or maximum-error figure as roughly a 3-sigma bound and assume the terms are independent. They are combined by root-sum-square:

| Term (3 sigma, um) | Optimistic | Recommended | Pessimistic |
|---|---|---|---|
| Sensor accuracy | 3 | 5 | 8 |
| Temperature residual | 1 | 3 | 7 |
| Reversible/SOC residual | 1 | 2 | 5 |
| Drift and creep | 1 | 5 | 15 |
| Gain and placement | 1 | 3 | 5 |
| Root-sum-square | 3.6 | 8.5 | 19.7 |
| **Rounded up** | **5** | **10** | **20** |

- **Why round up:** it covers terms not listed separately, such as vibration, electronics ageing and fixture changes at service.
- **If the estimator has a slow bias state:** the per-cycle random (white) part of the recommended budget is about 7 um at 3 sigma. That is the root-sum-square without the drift row. The drift then goes into the bias state's process noise.

**Why force and strain sensing sit at the pessimistic end**
- Thin-film force sensors: +/-3% FS linearity, drift below 5% per logarithmic time, and 0.36%/C (Tekscan A201).
- A compact MEMS load cell: +/-1% FS, with 0.05% FS/C zero and span shift. It is rated only for 0 to 50 C (TE FX29).
- FBGs measure strain, not thickness. Across reported sensors, an uncompensated 1 C change reads as about 0.7 to 20 microstrain (Chen 2023). A system costs over $10,000, plus about $165 per point at EV scale (Su 2021).

**Stack pressure changes the model, not the sensor error**
- Irreversible expansion falls as stack pressure rises (Mohtat 2021).
- At high pressure a cell can compact for about 150 cycles before it starts to expand (Wang 2026).
- If the pack pressure differs from the 5 psi fixture, b_SEI, b_pl and b_LAM change. That is model error and is not in this budget.

## 3. How this compares with our cells

At 10 um (3 sigma), one reading has sigma 3.3 um. A difference of two readings, whether two cells or two cycles of one cell, has sigma 4.7 um. That is 14 um at 3 sigma.

**Spread at hand-over (48.0, 52.7 and 60.9 um)**
- The outer pair differs by 12.9 um, which is 2.7 sigma of a difference. It is detectable, just under 3 sigma.
- The neighbouring pairs differ by 4.7 um and 8.2 um, which is 1.0 and 1.7 sigma. One reading cannot separate them.
- At 5 um the outer pair is 5.5 sigma apart. At 20 um it is 1.4 sigma apart.
- Averaging over cycles removes white noise but not calibration bias.
- In second life the sensor sees total thickness. Turning that into irreversible expansion needs each cell's fresh thickness. The only fresh values in the verified set are reported to 0.01 mm (13.36 and 13.37 mm, Michelini 2023). Unless fresh thickness was logged for each cell, the hand-over value is an initial-condition uncertainty about as large as the 13 um spread. It belongs in the initial covariance, not in the measurement noise R.

**Early growth (0.4 to 1.9 um per cycle)**
- This is 0.1 to 0.4 sigma of the change between two cycles. Growth within a single cycle cannot be seen at any of the three values.
- At a constant rate, the total growth passes 14 um after about 35 cycles at 0.4 um per cycle, and about 7 cycles at 1.9 um per cycle.
- A line fit over N readings does better against white noise. The 3-sigma of the fitted slope is 1.1 um per cycle over 10 cycles and 0.39 um per cycle over 20 cycles. So the full range of rates is resolved within about 10 to 20 cycles, provided drift over that window is only a few um.
- By cycle 50 (0.8 to 5.3 um per cycle), the fastest cell passes the threshold in about 3 cycles.
- Near end of life, growth of tens of um per cycle clears the 14 um threshold every cycle.

| 3 sigma per reading | sigma | 3 sigma of a difference | Outer pair (12.9 um) | Cycles to 3 sigma at 0.4 / 1.9 um per cycle | 3-sigma slope over 20 cycles |
|---|---|---|---|---|---|
| 5 um | 1.7 um | 7.1 um | 5.5 sigma | 18 / 4 | 0.19 um/cycle |
| 10 um | 3.3 um | 14.1 um | 2.7 sigma | 35 / 7 | 0.39 um/cycle |
| 20 um | 6.7 um | 28.3 um | 1.4 sigma | 71 / 15 | 0.78 um/cycle |

The 20 um case is mostly drift, which is not white noise, so the slope figure in that row is optimistic.

**Compared with simulation studies:** observer studies assume sigma = 1 um (Pannala 2020; Wan 2026), which is lab grade. The recommended in-vehicle sigma is about 3 times that; the pessimistic sigma is about 7 times.

## 4. References

1. K.-Y. Oh, J.B. Siegel, L. Secondo, S.U. Kim, N.A. Samad, J. Qin, D. Anderson, K. Garikipati, A. Knobloch, B.I. Epureanu, C.W. Monroe, A. Stefanopoulou, J. Power Sources 267 (2014) 197-202. doi:10.1016/j.jpowsour.2014.05.039
2. P. Mohtat, S. Lee, J.B. Siegel, A.G. Stefanopoulou, "Reversible and Irreversible Expansion of Lithium-Ion Batteries Under a Wide Range of Stress Factors," J. Electrochem. Soc. 168(10) (2021) 100520. doi:10.1149/1945-7111/ac2d3e
3. P. Mohtat, "Advanced Diagnostics for Lithium-ion Batteries: Decoding the Information in Electrode Swelling," Ph.D. dissertation, University of Michigan, Ann Arbor, 2021. hdl:2027.42/169953, doi:10.7302/2998
4. S. Pannala, A. Weng, I.S. Fischer, J.B. Siegel, A.G. Stefanopoulou, "Low-Cost Inductive Sensor and Fixture Kit for Measuring Battery Cell Thickness Under Constant Pressure," IFAC-PapersOnLine 55(37) (2022) 712-717. doi:10.1016/j.ifacol.2022.11.266
5. F. Brauchle, F. Grimsmann, K.P. Birke, "New Eddy-Current Sensor Setup for High-Resolution Lithium-Ion Cell Dilation Measurements," IEEE Sensors Journal 23(15) (2023) 17002-17010. doi:10.1109/JSEN.2023.3290349
6. T. Krause, D. Nusko, L. Pitta Bauermann, M. Vetter, M. Schafer, C. Holly, "Methods for Quantifying Expansion in Lithium-Ion Battery Cells Resulting from Cycling: A Review," Energies 17(7) (2024) 1566. doi:10.3390/en17071566
7. D. Clerici, F. Mocera, A. Soma, "Experimental Characterization of Lithium-Ion Cell Strain Using Laser Sensors," Energies 14(19) (2021) 6281. doi:10.3390/en14196281
8. Y.A. Plotnikov, J.H. Karp, A.J. Knobloch, C. Kapusta, D.T.W. Lin, "Eddy current sensor for in-situ monitoring of swelling of Li-ion prismatic cells," AIP Conf. Proc. 1650 (2015) 434-442. doi:10.1063/1.4914639
9. A. Knobloch, J. Karp, Y. Plotnikov, C. Kapusta, J.B. Siegel, N.A. Samad, A.G. Stefanopoulou, "Novel thin temperature and expansion sensors for li-ion battery monitoring," 2017 IEEE SENSORS, pp. 1-3. doi:10.1109/ICSENS.2017.8234066
10. M.A. Figueroa-Santos, J.B. Siegel, A.G. Stefanopoulou, "Leveraging Cell Expansion Sensing in State of Charge Estimation: Practical Considerations," Energies 13(10) (2020) 2653. doi:10.3390/en13102653
11. N.A. Samad, Y. Kim, J.B. Siegel, A.G. Stefanopoulou, "Battery Capacity Fading Estimation Using a Force-Based Incremental Capacity Analysis," J. Electrochem. Soc. 163(8) (2016) A1584-A1594. doi:10.1149/2.0511608jes
12. D. Schmider, W.G. Bessler, "Thermo-Electro-Mechanical Modeling and Experimental Validation of Thickness Change of a Lithium-Ion Pouch Cell with Blend Positive Electrode," Batteries 9(7) (2023) 354. doi:10.3390/batteries9070354
13. Tang Wei, Xu Xiaoming, Ding Hua, Guo Yaohua, Liu Jicheng, Wang Hongchao, "Sensitivity Analysis of the Battery Thermal Management System with a Reciprocating Cooling Strategy Combined with a Flat Heat Pipe," ACS Omega 5(14) (2020) 8258-8267. doi:10.1021/acsomega.0c00552
14. H. Wang, R. Wang, C.A. O'Keefe, E. Bjorklund, D. Proprentner, J.C. Stallard, H.J. Tan, W.M. Dose, L.F.J. Piper, R.S. Weatherup, A.J.D. Shaikeea, C.P. Grey, M. De Volder, "The interplay between stack pressure, mechanical expansion and degradation pathways in lithium-ion batteries," Nature Energy 11(7) (2026) 1032-1042. doi:10.1038/s41560-026-02087-6
15. E. Michelini, P. Höschele, S.F. Heindl, S. Erker, C. Ellersdorfer, Batteries 9(4) (2023) 218. doi:10.3390/batteries9040218
16. C. Hendricks, B. Sood, M. Pecht, "Lithium-Ion Battery Strain Gauge Monitoring and Depth of Discharge Estimation," J. Electrochem. Energy Convers. Storage 20(1) (2023) 011008. doi:10.1115/1.4054340
17. L.W. Sommer, A. Raghavan, P. Kiesel, B. Saha, T. Staudt, A. Lochbaum, A. Ganguli, C.-J. Bae, M. Alamgir, "Embedded Fiber Optic Sensing for Accurate State Estimation in Advanced Battery Management Systems," Mater. Res. Soc. Symp. Proc. 1681 (2014). doi:10.1557/opl.2014.560
18. D. Chen, Q. Zhao, Y. Zheng, Y. Xu, Y. Chen, J. Ni, Y. Zhao, "Recent Progress in Lithium-Ion Battery Safety Monitoring Based on Fiber Bragg Grating Sensors," Sensors 23(12) (2023) 5609. doi:10.3390/s23125609
19. Y.-D. Su, Y. Preger, H. Burroughs, C. Sun, P.R. Ohodnicki, "Fiber Optic Sensing Technologies for Battery Management Systems and Energy Storage Applications," Sensors 21(4) (2021) 1397. doi:10.3390/s21041397
20. Tekscan Inc., "FlexiForce A201 Sensor," product specification, https://www.tekscan.com/products-solutions/force-sensors/a201 (accessed 24 Sep 2026).
21. TE Connectivity, "FX29 Compact Compression Load Cell," product page https://www.te.com/en/product-CAT-FSE0006.html (accessed 24 Sep 2026); FX29 datasheet, rev. 06/2019.
22. S. Pannala, P. Valecha, P. Mohtat, J.B. Siegel, A.G. Stefanopoulou, "Improved Battery State Estimation Under Parameter Uncertainty Caused by Aging Using Expansion Measurements," arXiv:2009.14270 (2020); published in Proc. 2021 American Control Conference, pp. 3088-3093. doi:10.23919/ACC50511.2021.9482886
23. Z. Wan, H. Movahedi, W. Liu, J. Ma, J.B. Siegel, A. Weng, A. Stefanopoulou, "Modeling and Estimation of Solid Electrolyte Interphase during Formation in Battery Manufacturing," arXiv:2606.12664 (2026).
