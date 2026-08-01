#let filename = "magnetic_loop_antenna_v2026-07-14a.pdf"

#set page(
  paper: "a4",
  margin: 1.5cm,
  numbering: "1",
  footer: context {
    let current = counter(page).get().first()
    let total = counter(page).final().first()
    set text(size: 8pt)
    align(
      center,
    )[  \  #link("http://www.positron.ch/rf/magnetic_loop")[www.positron.ch/rf/magnetic\_loop]#h(4em)#link("https://arxiv.org/abs/2607.10828")[arXiv:2607.10828]#h(4em)#filename #h(4em)Page #{"" + str(current) + " of " + str(total)}]
  },
)
#set text(font: "Libertinus Serif", size: 11pt, lang: "en")
#set heading(numbering: "1.1") // Enables numbering (e.g. 1.1.1)

#set text(size: 18pt, weight: "bold")
#align(center)[Small but Tubby: A Magnetic Loop Antenna Made from 100 mm Copper Tubing]
#set text(size: 11pt, weight: "regular")

#v(0.5em)
#align(center)[
  #image("images/20260305_114902773.jpg", width: 60%)
]

#set text(size: 10pt)
#align(center)[
  *Author:* HB9ISP Peter Märki, El. Ing. FH (ORCID: 0000-0002-0596-076X), Zelglistrasse 49, 8634 Hombrechtikon, Switzerland \
  *Co-Author:* Markus Niese, MSc Quantum Engineering, PhD candidate at ETH Zurich (ORCID: 0009-0009-9132-9613)
]
#set text(size: 11pt)

#v(0.5em)
#set text(style: "italic")
*Abstract:* This paper presents the electrical model, key equations, and practical construction of a small transmitting magnetic loop antenna built from unusually large 100 mm diameter copper tubing. The large conductor surface area and wide-area transitions to the vacuum capacitors were designed to minimize resistive losses. The frequency range from 1.8 MHz to 31 MHz is unusually wide. Frequency, impedance matching, and azimuth are all adjusted automatically by servo motors.
A novel feature is the routing of the control wiring inside the loop conductor, allowing the motor to be mounted without electrical insulation from the loop conductor.

Indoor losses originate predominantly from near-field coupling to the environment rather than from the antenna itself. Temperature-rise measurements confirm that the bulk of the dissipated power is absorbed by the environment, not by the antenna components.

The conducted H-field measurements demonstrate good agreement between the measured H-field and the theoretical free-space H-field calculated from the antenna geometry and an estimated loop current. The loop current was estimated from the measured antenna bandwidth and the applied transmit power.

The antenna was developed for indoor operation where outdoor installation is not possible.

*Keywords:* magnetic loop antenna, small transmitting loop, vacuum capacitor, KP1-4, copper tubing, antenna efficiency, gamma match, servo tuning, indoor antenna, thermal measurement, building losses

#set text(style: "normal")

#pagebreak()
#v(0.25em)
#set text(size: 9pt, style: "italic")
Unless otherwise stated, all variables are expressed in SI units.
#set text(size: 11pt, style: "normal")

#outline(
  title: [Table of Contents],
  indent: auto, // Indent subsections automatically
)
#pagebreak()

#set math.equation(numbering: "(1)")

= Fundamentals



== Schematic, resonant circuit

To model the magnetic loop antenna we will successively add elements that represent specific physical effects. @fig_basics_loop_symbol shows the magnetic loop together with a capacitor. We introduce a capacitor C and a inductance L, which represents the inductive behaviour of the loop, see @fig_basics_l_c.

#pad(left: 12mm)[
#figure(
  image("images/basics_loop_symbol.svg", width: 20%),
  caption: [Magnetic loop antenna: main loop and capacitor.],
)<fig_basics_loop_symbol>
]

#figure(
  image("images/basics_l_c.svg", width: 20%),
  caption: [The antenna forms an LC tank circuit, where the loop itself acts as the inductor ($L$).],
)<fig_basics_l_c>

#pad(left: 2mm)[
#figure(
  image("images/loop_diameter.svg", width: 20%),
  caption: [Inductance of a ring-shaped tube.],
)<fig_loop_diameter>
]


For a single-turn circular loop with mean diameter $D$ and conductor diameter $d$, the approximate inductance is given by:

$ L = mu_0 dot D / 2 (ln((8D) / d) - 2) $

where $mu_0 = 4 pi dot 10^(-7) H/m$.

#set text(style: "italic")
This approximation assumes a pronounced skin effect where the current flows only on the conductor's surface (e.g., in high-frequency applications or thin-walled tubing).
#set text(style: "normal")

The resonance frequency of the tuned loop is given by:

$ f_0 = 1 / (2 pi dot sqrt(L dot C)) $




#pagebreak()
In addition to the inductance, there is also damping in the loop, modeled by $R_T$ (see @fig_basics_l_c_rt). This damping can be further split up in radiation $R_R$, representing the energy that is radiated away, and losses $R_"loss"$ in the loop. These losses consist of inductive losses $R_L$, capacitor losses $R_C$ and near-field losses in the environment $R_E$ (see @fig_basics_l_c_resistors_detail).

#pad(right: 22mm)[
#figure(
  image("images/basics_l_c_rt.svg", width: 20%),
  caption: [The resonant circuit is damped; this is modeled by inserting a resistance ($R_T$).],
)<fig_basics_l_c_rt>
]



#figure(
  image("images/basics_l_c_resistor_loss.svg", width: 30%),
  caption: [The damping is caused by losses ($R_"loss"$) and radiation ($R_"R"$).],
)<fig_basics_l_c_resistors_loss>

#figure(
  image("images/basics_l_c_resistors_detail.svg", width: 30%),
  caption: [The losses $R_"loss"$ can be split into inductor losses ($R_L$), capacitor losses ($R_C$), and losses due to energy absorbed in the near vicinity of the antenna ($R_E$).],
)<fig_basics_l_c_resistors_detail>




#figure(
  image("images/basics_l_c_transformator.svg", width: 30%),
  caption: [The transmitter, with a 50 Ω internal resistance, delivers the RF power $P$ into the main loop via a matching network (such as a coupling loop, gamma match, or similar transformer).],
)<fig_basics_l_c_transformator>



#let H = math.upright("H")
#let m = math.upright("m")

#pagebreak()

We can get the total resistance $R_T$ from measurements. By measuring the SWR (Standing Wave Ratio) from the transmitter to the antenna (see @fig_basics_l_c_transformator), the intrinsic quality factor (unloaded quality factor) $Q_0$ can be determined. After achieving a perfect match ($"SWR" = 1:1$) using the transformer, the bandwidth $B_"SWR 2.62"$ is measured at the points where the SWR rises to $2.62$.

The unloaded quality factor is then calculated as:

$ Q_0 = f_0 / B_"SWR 2.62" = f_0 / (f_"upper_SWR_2.62" - f_"lower_SWR_2.62") $

For the derivation, see @app_swr.

From this, the total resistance $R_T$ (including radiation and loss resistance) can be derived using the inductive reactance $X_L$:

$ R_T = X_L / Q_0 = 2 pi dot f_0 dot L / Q_0 $



During transmission, the loop current $I_"main_loop"$ can be estimated by assuming that the total transmitter power $P$ is delivered to the antenna:

$ I_"main_loop" = sqrt(P / R_T) $

Consequently, the voltage across the capacitor (loop voltage) is given by:

$ U_"loop" = I_"main_loop" dot X_L = I_"main_loop" dot 2 pi dot f_0 dot L $

In both the receiving and the transmitting case, the $3"dB"$ bandwidth $Delta f_"3dB"$ is determined by the total damping of the system, which defines the loaded quality factor $Q_L$. Under matched conditions, where the receiver load equals the antenna resistance, this bandwidth is given by:

$ Delta f_"3dB" = f_0 / X_L dot 2 R_T $

#v(0.5em)
In this scenario, the total resistance is doubled due to the matched load of the transceiver. This leads to a broader bandwidth than in the unloaded case (antenna without transceiver connected). See also reference [1] and @app_bandwidth_3db.

#pagebreak()

== Coupling Loop
There are many possible coupling methods. Several variants are shown in references [2] and [3]. This section focuses on two similar methods, both are mechanically and electrically elegant solutions: First, I will discuss the shielded coaxial coupling loop, a small complete coupling loop that is magnetically coupled to the main loop, then I will discuss the gamma match feed system, which only has half a loop in addition to the main loop. There I will also discuss the differences between the two and explain why the gamma match feed system was chosen for the antenna presented in this paper.
=== Shielded Coaxial Coupling Loop

In the following, we describe the shielded coaxial coupling loop. We simplify the coupling loop step by step to explain its function.
#figure(
  image("images/coupling_loop_overview.svg", width: 50%),
  caption: [Coupling loop overview: coaxial cable from TX to antenna, with the lower part of the main loop shown in gray; at the top, the shield is opened and the conductors are connected as indicated.],
)<fig_coupling_loop_overview>

#figure(
  image("images/coupling_loop_tx_moved.svg", width: 50%),
  caption: [For simplification, the source TX is moved all the way to the top. This simplification is functionally equivalent.],
)<fig_coupling_tx_position>

#figure(
  image("images/coupling_loop_current.svg", width: 50%),
  caption: [Coupling-loop current flow: Moving the source TX to the top allows us to draw a functionally equivalent picture where the current is modelled to flow only in the one single loop with one conductor, here black, while the other two are grayed out; the source current flows on the outer shield, and symmetry at the GND point helps minimize common-mode feed-line currents toward TX.
  ],
)<fig_coupling_loop_current>

#figure(
  image("images/coupling_loop_transformer.svg", width: 50%),
  caption: [The coupling ratio (equivalent turns ratio) between the coupling loop and the main loop depends on how much magnetic flux links the coupling loop versus the main loop. By changing the position, size, or shape of the coupling loop, the coupling ratio can be adjusted continuously. The adjustment is made so that the input impedance is matched to 50 Ω. Ideally, all power from the transmitter is transferred via the coupling loop into the main loop. Losses in this coupling are usually negligible compared to the other antenna losses. Current and voltage in the coupling loop can therefore be calculated for given power from TX.],
)<fig_coupling_loop_transformer>
Numerical example, consider 100 W into the 50 Ω coupling loop: the voltage is $U = sqrt(P dot R) = sqrt(100 upright(W) dot 50 Omega) approx 71 upright(V)$ and the coupling-loop current is $I = sqrt(P slash R) approx 1.4 upright(A)$. Assuming the main loop has $R_T = 0.0625 Omega$, the main-loop current is $I_"main loop" = sqrt(P slash R_T) = sqrt(100 upright(W) slash 0.0625 Omega) = 40 upright(A)$.
#pagebreak()
=== The Gamma Match Feed System

An alternative to the coaxial coupling loop is the gamma match feed system. This method also uses a small loop or a shorted stub to magnetically couple to the main loop.
In contrast to the coaxial coupling loop, the main loop itself is used as the return path to the coaxial connector.



#figure(
  image("images/gamma_match_overview.svg", width: 50%),
  caption: [The outer conductor of the coaxial cable is galvanically connected to the main loop at the symmetry point.
    The inner conductor is run along the main loop at a certain distance and finally also galvanically connected to the left side of the main loop. ],
)<fig_gamma_match>

In contrast to the previously shown coaxial coupling loop, the gamma match is asymmetric and the conductor is not shielded. In my opinion, however, this is not a relevant disadvantage. The asymmetry is minimal for a main loop with high Q factor because the current in the gamma match is only a small fraction of the current in the main loop. The fact that the gamma match is not shielded is also not a problem.
The main loop, much larger and with a larger cross-section, is also not shielded. The small, also unshielded gamma match makes no significant difference.


Gamma matches are usually set to a fixed position or are manually adjustable, possibly with the help of a screwdriver. #v(0.25em)



Here, I present an approach with a pivoted and thus easily automatically adjustable gamma match. The end point, where the gamma match is connected to the main loop stays fixed, while the arc of the gamma match can be rotated to change the area between the main loop and the gamma match loop.

#figure(
  image("images/gamma_match_rotation.svg", width: 50%),
  caption: [The gamma match is rotatably mounted (red: rotation axis). Position with minimal coupling in black. Maximum coupling in blue. ],
)<fig_gamma_match_rotation>

With minimal coupling, the gamma match conductor is very close to the main loop. The self-inductance of the coupling is very small. In my view, this is a major advantage. A disadvantage is the somewhat complex geometry of the bearing and the rotating contacts, which can be solved using flexible cable sections (see @fig_gamma_match_mechanism).






== Radiation Resistance

The radiation resistance $R_"R"$ is a crucial parameter determining the antenna's efficiency.


For electrically small loops ($C < lambda/10$), the radiation resistance is well approximated by the standard Rayleigh formula:

$ R_"R" approx 31171 dot ((A dot f^2) / c^2)^2 $

For larger loops (up to $D approx 0.5 lambda$), the small loop approximation loses accuracy and tends to overestimate the radiation resistance. R.W.P. King derived a more general expression for a circular loop with uniform current distribution, which includes a correction factor (second bracket) for larger loops:

$ R_"R" approx 31171 dot ((A dot f^2) / c^2)^2 dot (1 + 0.5 dot ((pi dot D dot f) / c)^2) $

where:
- $R_"R"$: Radiation resistance ($Omega$)
- $A$: Loop area ($m^2$)
- $f$: Frequency (Hz)
- $c$: Speed of light ($299 792 458 "m/s"$)
- $D$: Loop diameter (m)

#pagebreak()
== Antenna Efficiency

The antenna efficiency $eta$ describes how efficiently the antenna radiates power. It is defined as the ratio of radiated power to the total power supplied to the antenna. The efficiency can be calculated as

$ eta = R_"R" / R_T = R_"R" / (R_"R" + R_E + R_L + R_C) $
where $R_T$ is the total resistance, which includes radiation resistance ($R_"R"$) and all loss resistances: loss resistance due to conductor losses ($R_L$), losses due to absorption in the environment ($R_E$), and losses in the resonating capacitor ($R_C$).






== Magnetic Field Strength near the Loop
<sec_magnetic_field_strength>

#figure(
  image("images/koordinatensystem.jpeg", width: 80%),
  caption: [Coordinate system used for the figures in this document. Main loop in red.],
)<fig_coordinate_system>

It is important to discuss some safety aspects of the antenna. During transmission, the magnetic field close to the antenna can be quite large, requiring people to keep a safety distance.


#v(0.5em)
A simple estimate is obtained by treating the loop as a *magnetic dipole* (valid for $lambda ≫ r$ and $r >> D$). The magnitude of the magnetic field strength is:

$ H = I_"main_loop" dot D^2 / (16 dot r^3) dot sqrt(1 + 3 dot cos(phi)^2) $ <eq_h_field_dipole>

where $D$ is the loop diameter, $r$ is the distance from the loop center to the observation point, and $phi$ is the angle measured from the x-axis (loop axis) (see Figure @fig_coordinate_system).

For a more accurate estimate that is also valid at larger distances, the full retarded magnetic dipole solution is used. With the magnetic dipole moment $m = I_"main_loop" pi (D/2)^2$ and wavenumber $k = 2 pi f / c$, the H-field magnitude is:

$ H = m / (4 pi) dot sqrt(4 cos^2(phi) (1/r^6 + k^2/r^4) + sin^2(phi) (1/r^6 - k^2/r^4 + k^4/r^2)) $

The first terms ($1/r^6$ inside the square root, i.e., $prop 1/r^3$) dominate in the near field; the last terms ($k^4/r^2$ inside the square root, i.e., $prop 1/r$) dominate in the far field.

The magnetic field strength $H$ around the loop is visualized in the next figure. The figure shows lines of equal magnetic field strength for a loop with a diameter of 1 m and a current of 10.5 A at 14.1 MHz.

#figure(
  image("images/magnetic_field_strength.svg", width: 80%),
  caption: [Simulated magnetic field strength (H) around the loop antenna.],
)<fig_magnetic_field_strength>

A typical safety limit value for the near-field magnetic field strength is 0.073 A/m at 14 MHz (ICNIRP, 1998). In the example shown here, the required safety distance is already quite large.

For indoor operation, safety assessments based solely on theoretical antenna losses may overestimate the magnetic field strength, because additional environmental losses reduce the loop current. Consequently, the actual H-field should be estimated from the measured antenna bandwidth or, preferably, verified directly using an H-field probe.



A wider view highlights the transition toward the far-field pattern: in this cross-sectional view, the field extends predominantly in the loop plane (y-direction) while it narrows along the loop axis (x-direction).

#figure(
  image("images/magnetic_field_strenght_big.svg", height: 10cm),
  caption: [Simulated magnetic field strength (H), wide-view map showing the transition toward the far-field pattern (see next section). The innermost contour here corresponds to the outermost contour in @fig_magnetic_field_strength.],
)<fig_magnetic_field_strength_big>

Examples of H-field measurements can be found in @app_h_field_measurement.


== Far-Field Radiation Pattern

The following figure shows the normalized linear far-field radiation characteristic.

#figure(
  image("images/linear_radiation_pattern.svg", width: 50%),
  caption: [Normalized linear far-field radiation pattern of a loop antenna.],
)<fig_far_field_radiation_pattern>


In the far-field region, the magnetic loop antenna exhibits a figure-eight radiation pattern, with maximum radiation occurring in the plane of the loop ($phi = 90°$) and nulls along the loop axis ($phi = 0°$). This characteristic is typical for small loop antennas.
#pagebreak()

== Environmental Losses ($R_E$): Near-Field Coupling vs. Far-Field Radiation

In discussions about this paper, several people expressed confusion: if the antenna is operated indoors, the power passes through the air and is absorbed by the surrounding walls — so it must be radiated. However, far-field radiation and near-field coupling into nearby objects (as in a transformer) are not the same thing, even though in both cases the power leaves the antenna through the air. The following worked example with concrete numbers is intended to clarify this distinction.

The numerical values in the figures are based on the 20 m band (see @fig_measured_antenna).
#figure(
  image("images/example_wall_loop_to_loop.png", height: 7cm),
  caption: [A magnetic loop is shown with its loss resistances. The antenna couples to a dummy load (dummy loop with resistor) placed in close proximity. Most of the energy is coupled from the antenna into this dummy load via the magnetic field, as in a transformer.],
)<fig_example_wall_loop_to_loop>

#figure(
  image("images/example_wall_loop_to_wall.png", height: 7cm),
  caption: [The dummy load has been replaced by a wall. The wall absorbs energy from the antenna's near field in exactly the same way as the dummy load. From the antenna's perspective, the conditions are identical.],
)<fig_example_wall_loop_to_wall>

#figure(
  image("images/example_wall_loop_to_radiation.png", height: 7cm),
  caption: [Now the wall is removed and the antenna stands in free space. The gamma match has been re-adjusted so that the feed point still presents 50 Ω. $R_E$ is now 0 Ω. A significantly larger current now flows in the main loop. The power going into radiation is much greater. The losses in $R_L$ and $R_C$ are also larger.],
)<fig_example_wall_loop_to_radiation>


It is somewhat counterintuitive that the antenna in free space, where it has good efficiency, produces more heat loss in the antenna itself than when operated indoors, where the radiation efficiency is worse. Yet this is exactly the case.
#pagebreak()

= The Small but Tubby Magnetic Loop Antenna
In this chapter I explain how I built the antenna and the choices I made to achieve the optimal design for my use case. In @sec_loop_const I describe the construction of the loop, starting with the commercially available copper tubes, to adding mounting and transition parts and assembling the tube. In @sec_capacitors I describe the capacitors used. The antenna is constructed in a way such that the capacitors can be exchanged to reach different bands from 10 m to 160 m.



== Loop Construction <sec_loop_const>
Commercial copper downspouts were used (see @fig_copper_tubing).

#figure(
  image("images/20251231_145724591.jpg", width: 50%),
  caption: [Commercially available copper downspouts with 100 mm diameter.],
)<fig_copper_tubing>

To mount the coaxial cable to the transmitter and to hold the coupling loop, additional copper parts were attached to the lower part of the loop (see @fig_preparation_contacts).

#figure(
  image("images/20260105_151841411.jpg", width: 50%),
  caption: [Copper parts for mounting the coupling loop.],
)<fig_preparation_contacts>


For the transitions to the capacitors, I applied cutting patterns using adhesive labels and rough-cut them with tin snips (see @fig_tubing_to_capacitor). The details were then machined using a Dremel cutter.

#figure(
  image("images/20260103_230506438.jpg", width: 50%),
  caption: [Transitions from pipe to capacitors with glued-on cutting patterns.],
)<fig_tubing_to_capacitor>

The movable parts of the transitions were annealed with a propane torch to make them ductile (see @fig_tubing_to_capacitor_bent).

#figure(
  image("images/20260104_100238884.jpg", width: 50%),
  caption: [Annealed and bent transitions. The surface is still black from copper oxide.],
)<fig_tubing_to_capacitor_bent>

The commercially available pipe elbows had an angle of 85°. Since I needed 90°, I made a cut on the outside to provide the necessary flexibility. The pipes were cut to length, and the surfaces were cleaned with steel wool.



For the solder joints, the pipes were pressed together and fixed using a strap and screw buckle, ensuring a very narrow solder gap (see @fig_fixation_before_soldering).

#figure(
  image("images/20260105_172702589.jpg", width: 50%),
  caption: [Clamping the copper parts securely before soldering.],
)<fig_fixation_before_soldering>

Aggressive soldering grease (containing 16% zinc chloride) was used as flux. Soldering was performed with a propane torch and soft solder (Stannol Kristall 611, 1 mm, Sn96.5Ag3Cu0.5), which flows excellently and offers good conductivity.

#figure(
  image("images/20260105_190309991.jpg", width: 50%),
  caption: [Soldering joint after removing flux residues.],
)<fig_soldering_joint>

Excess solder was removed using a small cutter on a Dremel tool. The goal was to minimize the path current travels through the solder (see @fig_dremel_solder_removal).

#figure(
  image("images/20260105_190736487_dremel.jpg", width: 50%),
  caption: [Removing excess solder with a milling cutter.],
)<fig_dremel_solder_removal>

#figure(
  image("images/20260106_121111891.jpg", width: 50%),
  caption: [Surface after milling and sanding. The current flows through the solder for only a very short distance.],
)<fig_solder_removal_process>



#figure(
  image("images/20260105_215609871.jpg", width: 50%),
  caption: [Finished soldered loop.],
)<fig_soldered_loop>




#figure(
  image("images/20260106_121530147.jpg", width: 50%),
  caption: [Loop before final cleaning with steel wool.],
)<fig_before_cleaning>

Finally, the surface was cleaned with sandpaper and steel wool. "Kontakt Chemie PLASTIK 70" varnish was applied for corrosion protection, while contact points were masked with tape (see @fig_painted_loop). This was a substantial and laborious task.

#figure(
  image("images/20260107_152010205.jpg", width: 50%),
  caption: [Loop finished and varnished.],
)<fig_painted_loop>

#figure(
  image("images/20260107_175604052.jpg", width: 50%),
  caption: [Transition to the variable capacitor. The flattened pipe section is 100 mm wide and is screwed onto the 12 mm thick transition piece to the capacitor using six M6 stainless-steel Torx screws.],
)<fig_contact_fingers>


#figure(
  image("images/20260305_114419398.jpg", width: 50%),
  caption: [Configuration for 10 m to 40 m: only the variable capacitor is connected. Capacitor A is mechanically mounted, but the side screws are not inserted. The gap between the copper tabs and the capacitor end caps is about 10 mm.],
)<fig_config_10m_40m>

#figure(
  box[
    #image("images/20260305_114541031.jpg", width: 50%)
    #place(bottom + right, dx: 0%, dy: -24%)[#rect(fill: white, inset: 3pt)[#text(
      size: 10pt,
      fill: black,
    )[capacitor A]]]
  ],
  caption: [Configuration for 60 m: capacitor A 500 pF is electrically connected. The side screws press the copper tabs onto the capacitor end caps.],
)<fig_config_60m>

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    box[
      #image("images/20260305_114725844.jpg", height: 5.5cm)
      #place(bottom + right, dx: 0%, dy: -31%)[#rect(fill: white, inset: 3pt)[#text(
        size: 10pt,
        fill: black,
      )[capacitor A]]]
      #place(bottom + right, dx: 0%, dy: -11%)[#rect(fill: white, inset: 3pt)[#text(
        size: 10pt,
        fill: black,
      )[capacitor B]]]
    ],
    image("images/20260305_114952554.jpg", height: 5.5cm),
  ),
  caption: [Configuration for 80 m: additional capacitor B 500 pF is installed.],
)<fig_config_80m>


== Capacitors <sec_capacitors>

=== Variable Capacitor
#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20251117_164218183.jpg", height: 6cm), image("images/20251123_195552832.jpg", height: 6cm),
  ),
  caption: [Left: variable vacuum capacitor KP1-4 10--500 pF. Right: when the capacitor is set to minimum capacitance, the concentric copper tubes are visible.],
)<fig_variable_capacitor>



#pagebreak()
I had long been curious about the internal structure of such a vacuum capacitor, so one had to be sacrificed.

#figure(
  grid(
    columns: (auto, auto, auto),
    gutter: 2mm,
    image("images/20260307_125830100.jpg", height: 5.5cm), image("images/20260307_130138886.jpg", height: 5.5cm), image("images/20260307_133151708.jpg", height: 5.5cm),
  ),
  caption: [Left: the author and the capacitor wrapped in cardboard as implosion protection. I had no idea whether opening it would be dangerous — it took some courage to drill into the glass envelope. The sound was just a soft blob, not loud at all. Center: glass drill bit; the vacuum is gone. Right: the glass is then removed with a hammer, revealing the beautifully colored copper inside.],
)<fig_capacitor_teardown_1>

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260307_133017478.jpg", height: 5.5cm), image("images/20260307_133035582.jpg", height: 5.5cm),
  ),
  caption: [View of the concentric interleaving vanes.],
)<fig_capacitor_teardown_2>

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260307_212434761.jpg", height: 5.5cm), image("images/20260307_212516394.jpg", height: 5.5cm),
  ),
  caption: [Turning the shaft clockwise retracts one set of vanes, reducing the capacitance. An internal spring (not visible in the photo) pushes the copper bellows back to full extension when the capacitance is increased.],
)<fig_capacitor_teardown_3>

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/KP1-4_10_500_capacitor_10pF.png", height: 4.5cm),
    image("images/KP1-4_10_500_capacitor_500pF.png", height: 4.5cm),
  ),
  caption: [Left: vanes fully separated, 10 pF. Right: vanes fully interleaved, 500 pF. The spring that extends the bellows is visible.],
)<fig_capacitor_teardown_4>

#figure(
  image("images/kp1_4_cap_turns.png", width: 70%),
  caption: [Capacitance characteristics versus turns of the axis. Reproduced with kind permission of Frank Dörenberg [3].],
)<fig_turn_cap_curve>


#figure(
  image("images/KP1-4_10_500_capacitor_detail.png", height: 5.5cm),
  caption: [Cross-sectional detail showing the movable copper bellows, which not only provides the vacuum seal but also carries the RF current to the vanes. The thrust bearing absorbs the axial force of the shaft.],
)<fig_capacitor_teardown_5>

#figure(
  grid(
    columns: (auto, auto, auto),
    gutter: 2mm,
    image("images/20260309_201649927.jpg", height: 5.5cm),
    image("images/20260309_202038094.jpg", height: 5.5cm),
    image("images/20260307_212015073.jpg", height: 5.5cm),
  ),
  caption: [The transition from glass to copper was made by fusing glass and copper together.],
)<fig_capacitor_teardown_6>

#figure(
  grid(
    columns: (auto, auto, auto),
    gutter: 2mm,

    box[
      #image("images/2026-03-09-210641.jpg", height: 5.5cm)
      #place(horizon + left, dx: 2%, dy: 0%)[#rect(fill: white, inset: 3pt)[#text(size: 10pt, fill: black)[copper]]]
      #place(horizon + right, dx: -2%, dy: -15%)[#rect(fill: white, inset: 3pt)[#text(
        size: 10pt,
        fill: black,
      )[yellow colored \ glass]]]
      #place(bottom + center, dx: -20%, dy: -5%)[#rect(fill: white, inset: 3pt)[#text(
        size: 10pt,
        fill: black,
      )[black paint]]]
    ],
    image("images/2026-03-09-210457.jpg", height: 5.5cm),
    box[
      #image("images/20260309_203206420.jpg", height: 5.5cm)
      #place(top + center, dx: 0%, dy: 2%)[#rect(fill: white, inset: 3pt)[#text(size: 10pt, fill: black)[glass]]]
      #place(horizon + left, dx: 0%, dy: -15%)[#rect(fill: white, inset: 3pt)[#text(size: 10pt, fill: black)[vacuum]]]
      #place(horizon + right, dx: -0%, dy: -15%)[#rect(fill: white, inset: 3pt)[#text(size: 10pt, fill: black)[air]]]
      #place(bottom + center, dx: -30%, dy: -15%)[#rect(fill: white, inset: 3pt)[#text(
        size: 10pt,
        fill: black,
      )[copper]]]
      #place(bottom + right, dx: -13%, dy: -4%)[#rect(fill: white, inset: 3pt)[#text(
        size: 10pt,
        fill: black,
      )[black \ paint]]]
    ],
  ),
  caption: [Left: view of a fracture point; when looking through the glass from outside, a yellow coloring is visible in the copper region, presumably caused by the fusion of glass and copper oxide. Center: a glass shard from the copper side, showing violet coloring with visible rings. Right: cross-sectional sketch. The copper lip must be very thin so that the stresses caused by the different thermal expansion coefficients of glass and copper do not become too high. Remarkably, this seal has remained vacuum-tight for decades.],
)<fig_capacitor_teardown_7>

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260308_085941573.jpg", height: 5.5cm), image("images/20260308_085830998.jpg", height: 5.5cm),
  ),
  caption: [On this capacitor specimen, arcing marks are clearly visible.],
)<fig_capacitor_arcing>

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/2026-03-09-210924.jpg", height: 5.5cm), image("images/2026-03-09-211047.jpg", height: 5.5cm),
  ),
  caption: [Left: close-up of an arcing pit, finely recessed and barely visible in the photograph. Right: view of a vane showing visible copper crystals — such large crystals indicate that very pure copper was annealed. Copper with impurities does not form crystals of this size. Pure copper conducts electricity well.],
)<fig_capacitor_teardown_8>

#figure(
  box[
    #image("images/arcing_marks.png", width: 70%)
    #place(bottom + left, dx: 22%, dy: -7%)[#rect(fill: white, inset: 3pt)[#text(
      size: 10pt,
      fill: black,
    )[arcing marks]]]
  ],
  caption: [The arcing marks appear only at the outermost gap. The outermost vane is slightly bent outward — a feature presumably intended for electric-field grading. Despite this measure, flashovers still occur exclusively at the outermost vanes. It has been reported that vacuum capacitors can be conditioned by slowly increasing DC voltage through a series resistor, which smooths protruding surface irregularities.],
)<fig_arcing_marks>


#figure(
  table(
    columns: (auto, auto),
    [*Detail*], [*Observation*],
    [Type designation], [КП1-4 (KP1-4); "КП" stands for "Конденсатор Переменный" (variable capacitor)],
    [Glass], [Wall thickness 2 mm],
    [Copper],
    [Very soft, presumably pure — as indicated by the large visible crystals — and fully annealed, then electropolished],

    [Vanes], [Plate thickness 0.5 mm; nominal free gap between plates 1.5 mm, reduced by mechanical tolerances],
    [Solder joints], [Likely silver brazing alloy, performed in vacuum without flux],
    [Glass-to-copper transition],
    [Glass and copper fused together, perfectly airtight. A thin copper lip is embedded in glass on both sides.],

    [End caps], [Silver-plated copper],
    [Shaft], [Stainless steel with M6 thread; 3.2 mm hole for pinning the drive coupling],
    [Bearing], [Axial thrust bearing; thread and bearing were completely packed with grease],
    [Estimated origin], [Presumably manufactured between approximately 1970 and 1990 in the USSR during the Cold War],
  ),
  caption: [Notable construction details of the KP1-4 vacuum capacitor.],
)<fig_capacitor_construction_details>

I am impressed by this capacitor — a masterpiece of engineering.

#figure(
  grid(
    columns: 2,
    gutter: 2mm,
    image("images/20251120_171957021.jpg", width: 80%), align(horizon, image("images/kp1-4_ass.jpeg", width: 100%)),
  ),
  caption: [Clamps manufactured from 12 mm OF copper as a transition from the capacitor ends to the copper tubes.],
)<fig_variable_capacitor_clamps>


#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260217_205255523.jpg", height: 5.5cm), image("images/capacitor_assembly.png", height: 5.5cm),
  ),
  caption: [Capacitor assembly. The servo_f is located inside the copper tube and is therefore in a field-free region.],
)<fig_capacitor_assembly>

Servo end stop. Clockwise rotation: the capacitor shaft reaches its stop. The servo torque is artificially limited. Counterclockwise rotation: at the end of the range, the shaft is unscrewed from the capacitor. A pin on the shaft then reaches a mechanical stop so that the shaft cannot be unscrewed too far from the capacitor.

The servo has a built-in 12-bit magnetic encoder for angle measurement over 360°. The absolute position is tracked in a file on the PC so that the number of full rotations is retained even after a power interruption. Therefore, no homing is required when restarting the control software.


=== Fixed Capacitors Jennings 500 pF


#figure(
  image("images/20251204_125635064.jpg", width: 50%),
  caption: [Jennings JCS-500-10S vacuum capacitor. Two of these are used.],
)<fig_fixed_capacitor>

Note the different colors of the metal-to-glass fusion. In the variable capacitor, the transition was yellow-colored — copper fused directly onto glass. The yellow coloring is presumably caused by copper oxide together with iron oxide in the glass.

In the Jennings capacitor, however, the fusion zone is dark red. Here, a Fe–Ni–Co alloy (Kovar) was likely used. This alloy is thermally better matched to glass. It colors dark red and provides a mechanically more robust bond than the direct fusion of copper with glass.

#figure(
  grid(
    columns: 2,
    gutter: 2mm,
    image("images/20251204_163311710.jpg", height: 30%), image("images/20260109_115041488.jpg", height: 30%),
  ),
  caption: [Turned sleeves made of OF copper serving as transition from vacuum capacitor to copper tubes. The sleeves are clamped onto the capacitor caps with hose clamps.],
)<fig_turned_parts>

=== Fixed Capacitor 4700 pF PTFE, Unsuccessful

I conducted a test with this 4700 pF capacitor on the 160 m band. The PTFE dielectric is known for its low losses.

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260219_222214572_4n7.jpg", height: 5.5cm), image("images/20260220_225940128_4n7.jpg", height: 5.5cm),
  ),
  caption: [Markings: type designation ФГТ-И (FGT-I series, PTFE dielectric), 4700 пФ ±10% (4700 pF ±10%), Uр = 12 кВ (peak voltage 12 kV), IV 1962 г (4th quarter 1962). Translation without guarantee.],
)<fig_capacitor_4700pf_ptfe>

The result was sobering — this capacitor is unsuitable for use in a magnetic loop antenna. The losses were so large that even the maximum coupling of the gamma match was insufficient to match the impedance to 50 ohms. Still, it is a beautiful sight — such lovingly crafted vintage components.

#pagebreak()
=== Fixed Capacitor 4000 pF PCB, Unsuccessful
A capacitor was fabricated from PCB material for the 160 m band.

30 circuit boards, each 1.2 mm thick and clad on both sides with 35 µm copper, active area 135 mm × 120 mm. Nominal gap between the plates: 1 mm. Side plates with 70 µm copper. Soldered with Stannol Kristall 611, Sn96.5Ag3Cu0.5.

#figure(
  grid(
    columns: (auto, auto, auto),
    gutter: 2mm,
    image("images/20260328_113157572_pcb.jpg", height: 5.5cm),
    image("images/20260328_124053037_pcb.jpg", height: 5.5cm),
    image("images/20260328_150438787_pcb.jpg", height: 5.5cm),
  ),
  caption: [Left: circuit boards as delivered by the manufacturer. Center: soldering the plates with a powerful soldering iron — the solder flows very nicely. Right: finished plate stack. The capacitance can be adjusted in steps by mounting the plate stacks vertically with a slight offset.],
)<fig_pcb_capacitor_assembly>

#figure(
  grid(
    columns: (auto, auto, auto),
    gutter: 2mm,
    image("images/20260329_054442547_pcb.jpg", height: 5.5cm),
    image("images/20260329_192158723_pcb.jpg", height: 5.5cm),
    image("images/20260329_103401_072_pcb.jpg", height: 5.5cm),
  ),
  caption: [Left: spacers 3D-printed from PETG; the spacers prevent the plates from touching. Center: fully assembled capacitor. Right: significant heating after brief transmission.],
)<fig_pcb_capacitor_spacers>

Initial tests showed large losses — the capacitor heated up very quickly. The contact points and solder joints remained relatively cool. The losses evidently originate at the plates, presumably in the spacers.

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260330_093718655_pcb.jpg", height: 5.5cm),
    image("images/20260330_115214_541_pcb.jpg", height: 5.5cm),
  ),
  caption: [To corroborate the suspicion of losses in the spacers, two special spacers were fabricated with solid plastic filling the right quarter of the area. Left: the first spacer is only partially inserted into the capacitor; the solid-filled area is visible on the right. Right: after brief transmission, strong heating appeared precisely at the locations with solid plastic. The spacer losses are dominant.],
)<fig_pcb_capacitor_spacer_losses>

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/spacer_coc.png", height: 4cm),
    image("images/20260331_121053_170_pcb.jpg", height: 5.5cm),
  ),
  caption: [Left: new spacers with less material, made from COC (Cyclo Olefin Copolymer). COC should exhibit significantly lower dielectric losses than PETG. Right: the capacitor now heats up by only a few °C after 20 minutes of continuous transmission.],
)<fig_pcb_capacitor_coc>

The SWR versus frequency showed an asymmetric shape — the same behavior as shown later in @fig_comet_measurements. This is discussed further there.

During transmission, the behavior was puzzling: the FT-991A showed an SWR on the order of 2.1 and above and reduced the transmit power from 100 to 60 W to protect its output stage.  The voltage across the capacitor is less than 900 V#sub[rms], which should still be acceptable at a 1 mm plate gap.  Heating and detuning due to losses can be ruled out because the SWR was already poor immediately at the start of transmission. Detuning caused by electrostatic forces changing the plate spacing? Could it be corona discharge? Nothing was visible or audible from a distance, and no ozone smell was detected.


The capacitor was tested for DC voltage withstand: 2500V DC showed no measurable leakage, at 5000V DC a breakdown occurred.


The experiment with the PCB capacitor was discontinued at this point. The behavior remained unexplained. It was fascinating nonetheless.
#pagebreak()
=== Fixed Capacitor Vacuum 4200 pF

A 4200 pF capacitor is formed by combining multiple capacitors.

3 units Comet, CFMN-2800BAC/8-DE-G, 2800 pF, 8/4.8 kV, 75 mm diameter, 52 mm length, weighing 819 g each, M6 threads on both sides. For indoor use, these capacitors are massively oversized, but the optimal values for my application were not available on the second-hand market.

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260408_194552117_comet.jpg", height: 6cm), image("images/20260409_085516241_comet.jpg", height: 6cm),
  ),
  caption: [Left: a single capacitor with 2800 pF. Right: capacitors loosely connected with metal sheets to illustrate the wiring.],
)<fig_comet_capacitor_single>

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260409_125314648_comet.jpg", height: 6cm), image("images/20260409_125750048_comet.jpg", height: 6cm),
  ),
  caption: [Left: assembled 4200 pF capacitor, weighing 2.3 kg. The capacitors are firmly bolted together; the M6 threads provide solid mechanical strength. Right: capacitor mounted on the antenna.],
)<fig_comet_capacitor_assembled>

#figure(
  grid(
    columns: (auto, auto, auto),
    gutter: 2mm,
    image("images/comet_smith.png", height: 6cm), image("images/comet_swr.png", height: 6cm), image("images/20260409_140803896_comet_dummy.jpg", height: 6cm),
  ),
  caption: [Left: Smith chart — the trace has an unusual shape; it should be circular. Center: SWR versus frequency — the shape is unusual; it should be V-shaped. Right: verification measurement with a dummy load connected instead of the antenna.],
)<fig_comet_measurements>

The asymmetric SWR shape is presumably related to the slight asymmetry introduced by the gamma match together with the chokes and the feed cable. The shape is identical to that observed with the PCB capacitor above. It also remains unchanged when the frequency is slightly shifted.

When transmitting with WSPR at 100 W transmitter power on 160 m, the SWR rises to 1.6 (measured with the FT-991A, which is a rather imprecise measurement). On all higher bands, when the antenna impedance is properly matched, the FT-991A shows an SWR of 1.0 — but not on 160 m. When a dummy load is connected instead of the antenna, the SWR is correctly 1.0.

To investigate whether the unusual behavior might be power-dependent, the antenna impedance was measured over a wide power range using a resistance bridge: it behaves linearly down to 1 µW. The impedance measured with the bridge does not agree exactly with the impedance determined by the nanoVNA. The observed effects cannot be explained with the available measurement equipment.

As an example, @fig_14mhz_indoor shows the Smith chart and the SWR at 14 MHz — both exhibiting the textbook-expected shapes: a circular trace in the Smith chart and a V-shaped SWR curve.

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/s11_14mhz_indoor_ok.png", height: 6cm), image("images/swr_14mhz_indoor_ok.png", height: 6cm),
  ),
  caption: [In stark contrast to the unusual behavior shown above, here is a measurement at 14 MHz for comparison. Left: Smith chart — the trace is circular, as expected. Right: SWR versus frequency — the curve is V-shaped, as expected.],
)<fig_14mhz_indoor>

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260409_042836_290_comet_thermo.jpg", height: 6cm), image("images/20260410_160m_ft8_psk.png", height: 6cm),
  ),
  caption: [Left: after 10 minutes of transmitting at 100 W, the Comet capacitors heated up by 3.7 °C, the Jennings capacitor in the center by 0.3 °C, and the metal sheet connecting to the Jennings capacitors by 8 °C. Right: during a test on April 10, 2026, FT8 signals were decoded within a radius of approximately 1500 km. This is quite remarkable considering that the radiated power is at most 70 mW. Source: pskreporter.info.],
)<fig_comet_thermo_ft8>

The weak point is the junction between the main loop sheet and the Comet capacitor sheet, which is connected by only a single M6 screw. This contact point produces the most heat and indirectly warms the Jennings capacitor. Most of the current flows through the Comet capacitors, yet they heat up only slightly. The largest share of the losses occurs in the building, not in the antenna. A better junction would not make a significant difference. The resonant frequency of the antenna shifts downward by 225 Hz due to the heating — negligible for operation.

== Gamma Match <sec_gamma_match>

This section shows a gamma match implementation corresponding to the concept in @fig_gamma_match_rotation.

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260116_154213417.jpg", height: 6cm), image("images/20260116_154405897.jpg", height: 6cm),
  ),
  caption: [Gamma match constructed from 12 mm diameter copper tubing with a total length of 0.7 m.],
)<fig_gamma_match_tubing>


#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260305_114247556.jpg", height: 6cm), image("images/20260305_114308989.jpg", height: 6cm),
  ),
  caption: [Left: small coupling; right: large coupling. The servo_z automatically adjusts the coupling and is connected via a black fiberglass rod (not carbon fiber, which would be electrically conductive).],
)<fig_gamma_match_details>


#figure(
  image("images/20260116_154259848.jpg", width: 50%),
  caption: [Pivot joint in the center of the loop with galvanic connection to the main loop.],
)<fig_gamma_match_mechanism>

The gamma match is quite large. When set to maximum coupling, it encloses 1/4 of the magnetic flux lines of the main loop; such a high coupling is never needed. However, an oversized gamma match does not impose any disadvantages.

In some measurements, far from damping materials, the coupling could not be reduced sufficiently, so I temporarily installed a smaller coupling element.

#figure(
  image("images/20260305_114221234.jpg", width: 50%),
  caption: [Cable routing and placement of the electronic components are exactly in the symmetry plane of the antenna. Left, black: servo_z for coupling adjustment; below: magnetometer for azimuth control. Not shown in the image: servo_h for azimuth control.],
)<fig_coax_connection_gamma_match>

== Azimuth Control <sec_azimuth_control>

#figure(
  image("images/20260306_112306119.jpg", width: 50%),
  caption: [Below the antenna, the servo_h controls the azimuth. The servo axis is centered directly below the rope from which the antenna is suspended from the ceiling. The servo_h is connected to the antenna via a lever and a fiberglass rod. This allows the antenna to be rotated over a range of 220°. Because the antenna radiation pattern is symmetric, a sweep of 180° is sufficient.],
)<fig_servo_h_azimuth>





== Schematic <sec_schematic>

=== Overview
#figure(
  image("images/2025_vacuum_flex_loop.svg", width: 60%),
  caption: [Schematic of the antenna system including tuning servos and magnetometer.],
)<fig_schematic_full>

The upper part of the schematic mirrors the physical layout of the magnetic loop; the components are arranged in positions corresponding to their actual placement on the antenna.

For the data line, a readily available unshielded AWG24 Ethernet patch cable is used. In an additional switching box (not shown in the schematic), relays connect the antenna either to the VNA or to the transmitter output. The transmitter is also inhibited during the tuning process. LEDs mounted on the antenna (not shown in the schematic) indicate the operating state: red signals that transmission is possible, green signals that the transmitter is inhibited and the antenna can be safely approached. These LEDs are always illuminated. The servo and magnetometer supply voltage ("13 V") is only applied during tuning, because the servo electronics could otherwise interfere with the received signal.
#pagebreak()
=== Cable Routing to Frequency Tuning Servo

A common challenge in magnetic loop antenna design is the electrical insulation between the motor and the capacitor.

#figure(
  image("images/cable_routing_typical.png", height: 6cm),
  caption: [Example of a conventional design. The tuning capacitor is mounted vertically at the top of the loop. The motor shaft is coupled to the capacitor via an insulating shaft (blue). The motor cable (red) runs downward along the antenna's symmetry axis. During transmission, the full loop voltage $U_"loop"$ appears across the capacitor. Because the motor and its cable run along the symmetry axis of the loop, a voltage of $U_"loop" slash 2$ is present between the motor and the nearer capacitor terminal. The insulating shaft must withstand this voltage. Furthermore, the capacitive coupling between the motor body and the capacitor introduces an asymmetry in the antenna.],
)<fig_cable_routing_typical>

In contrast, in the magnetic loop antenna presented in this paper, the control cable is routed through the right vertical section of the loop conductor (see center of @fig_cable_routing_servo). Because the tube and cable follow the same path, no voltage is induced between them. No insulation between the motor and capacitor is required. 

#figure(
  grid(
    columns: (auto, auto, auto),
    gutter: 2mm,
    move(dy: -3mm, image("images/cable_routing_image.png", height: 6.7cm)),
    image("images/cable_routing_multi.png", height: 6cm),
    image("images/cable_routing_coax.png", height: 6cm),
  ),
  caption: [Left: the antenna presented in this paper. Center: the control cables (red) run through the right vertical section of the loop conductor; the drive motor can be mounted directly on the capacitor without any insulation. Right: an optional arrangement where the tuning motor is powered via the feed coaxial cable; the RF component is routed to the gamma match while the DC component is carried by the red cable to the motor, with a series inductor and blocking capacitors keeping the RF away from the motor. The loop conductor itself serves as the return path for the motor current.],
)<fig_cable_routing_servo>

Nevertheless, a fairly long shaft is used between the servo and the capacitor so that the servo is located inside the tube, i.e., in a field-free region, and therefore does not cause additional losses (see also @fig_capacitor_assembly).

#pagebreak()
== Key Parameters <sec_key_param>
#table(
  columns: (auto, auto),
  [*Parameter*], [*Value*],
  [name], [cu_1m_100mm_a],
  [Antenna type], [small magnetic loop],
  [Shape], [rectangular],
  [Width (measured between tube centers)], [0.95 m],
  [Height (measured between tube centers)], [0.85 m],
  [Equivalent diameter], [1.014 m],
  [Tubing diameter], [100 mm],
  [Area], [0.78 m²],
  [$L$ estimated from geometry and validated by measurements], [1.55 µH],
  [Tubing wall thickness (thicker than skin depth)], [0.6 mm],
  [Variable capacitor], [KP1-4, 10-500 pF, 7 kVrms, 50 Arms],
  [Fixed capacitor A, 500 pF, switchable], [Jennings JCS-500-10S 500 pF, 4.2 kVrms, 80 Arms],
  [Fixed capacitor B, 500 pF, switchable], [Jennings JCS-500-10S 500 pF, 4.2 kVrms, 80 Arms],
  [Fixed capacitor C, 4200 pF, switchable], [3× Comet CFMN-2800BAC/8-DE-G, 2800 pF 3.4 kVrms, 100 Arms],
  [Tuning drives],
  [Frequency servo_f: Feetech STS3215, 12 V \ Coupling servo_z: Feetech STS3215, 12 V \ Azimuth servo_h: Feetech STS3215, 12 V],

  [Azimuth control], [Bosch BMM350, 3-axis magnetometer],
)

#figure(
  image("images/frequency_ranges.png", width: 100%),
  caption: [Calculated frequency ranges for different capacitor configurations.],
)<fig_frequency_ranges>


#pagebreak()
= Measurements and Findings
== Outdoor Setup


#figure(
  image("images/house_cut.png", width: 95%),
  caption: [Cross-sectional house model used for the measurement setup.],
)<fig_house_cut>

A wooden ladder was secured to the house with ropes. At the top of the ladder, a pulley redirects the rope used to raise the antenna. At maximum elevation, the antenna is 5 m above ground and maintains at least 5 m distance from other metallic objects. The ladder itself only has small metal parts and screws.

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260304_085342185.jpg", height: 9cm), image("images/20260304_100524811.jpg", height: 9cm),
  ),
  caption: [Antenna on the ground and at maximum height.],
)<fig_pictures_outdoor>

== Indoor Setup

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/antenna_indoor.png", height: 5.5cm), image("images/20260223_190752405.jpg", height: 5.5cm),
  ),
  caption: [Indoor antenna setup: left, indoor measurement geometry; right, installation photo.],
)<fig_indoor_setup>

The antenna was suspended from the ceiling on the upper floor of the house, 0.8 m above the floor. The antenna was tested at various positions inside the house; at the position shown, the antenna damping is relatively low.
Above the antenna, the roof has a green layer with moist soil. In the floor below the antenna, there is underfloor heating with plastic pipes coated with aluminum. In addition, a photovoltaic system is installed nearby on the roof, and the canopies are covered with stainless steel sheet metal. The window panes have aluminum frames. Although the house has timber-frame construction, these are still far from optimal indoor conditions.

== Measured Bandwidths
#figure(
  image("images/table_measurements.png", width: 100%),
  caption: [Measured bandwidths. Derived resistances and estimated antenna efficiency.],
)<fig_measured_antenna>
Findings:
- An antenna efficiency of > 80% outdoors at 20 m is a very good value. With even greater distance from surrounding objects, it would likely increase further. This is where the elaborate antenna construction pays off.
- Outdoor efficiency: one would expect efficiency to continue increasing with frequency, but above 14 MHz it decreases again. This is very surprising.

== Dependence on Height Above Ground

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/high_above_ground.png", height: 6cm), image("images/diagram_above_ground.png", height: 6cm),
  ),
  caption: [Estimated loss resistance $R_"loss"$ as a function of height above ground for two frequencies for the 20 m band (14 MHz).],
)<fig_diagram_above_ground>

Findings:
- The loss resistance decreases continuously with increasing height as expected. With even greater distance from surrounding objects, the loss resistance would likely decrease further.
- Measurements were also performed in other bands. There, the dependence was far less regular. It is likely that large metallic structures in the surroundings, such as the long fence or the stainless-steel-covered canopies spanning four row houses, can come into resonance at these frequencies and strongly influence the antenna behavior, even at distances beyond 5 m. A 5 m separation is likely too small considering the wavelengths involved.


== Influence of Roof Moisture

As described in @fig_indoor_setup, the antenna is installed on the upper floor directly below a green roof with moist soil. 
Measurement series were performed under contrasting soil-moisture conditions: one after an extended dry period (soil presumably dry) and one shortly after approximately 10 mm of rainfall.
The measured bandwidths differed noticeably, with the direction of change varying by band — some bands showed a wider bandwidth, others a narrower one. The largest difference was observed in the 30 m band, where the bandwidth was approximately 25% wider under wet conditions than under dry conditions.

This suggests that the moist soil above the antenna acts as a lossy dielectric coupled into the near field of the loop, increasing $R_E$ and thereby reducing antenna efficiency.
#pagebreak()
== Influence of Ferrite Cores on Underfloor Heating Pipes

As described in @fig_indoor_setup, the floor below the antenna contains underfloor heating pipes with aluminium-coated plastic tubing. These conductive pipes lie within the near field of the antenna and are a potential source of environmental losses ($R_E$).

#figure(
  image("images/20260508_clip-on ferrite_tubes.png", width: 50%),
  caption: [Clip-on ferrite cores attached to the exposed underfloor heating pipes on the upper floor. 
  A few cores were also placed on the control wiring of the heating system.],
)<fig_ferrite_heating_pipes>

In an attempt to reduce induced currents in these pipes, clip-on ferrite cores were attached to several exposed pipe sections and to the heating control wiring.
Attaching the cores changed the measured bandwidths: some bands became narrower, others became wider. The largest observed change was an 11% bandwidth increase in the 20 m band.

The overall influence on antenna performance was small — and in most bands slightly detrimental — so the cores were subsequently removed.
#pagebreak()
== Measurement of the H Field
<app_h_field_measurement>

Section @sec_magnetic_field_strength estimates the H-field under free-space conditions. In practice, however, the building contains numerous conductive objects that distort the near field. To quantify the extent of this distortion, the H-field was measured at several locations and compared with the theoretical predictions.

#figure(
  stack(dir: ltr, spacing: 2mm,
    image("images/20260403_174747858.jpg", width: 40%),
    align(bottom, image("images/sensing_loop.png", width: 45%)),
  ),
  caption: [Left: simple self-made H-field probe. The induced voltage is measured with an inexpensive power meter containing an AD8307 logarithmic amplifier. The power meter was verified: despite its low cost, it is remarkably accurate. The combined measurement uncertainty of the probe and power meter is estimated at $plus.minus$ 0.5 dB, which is negligible compared to the field distortions caused by the building. Right: schematic of the sensing loop. The inner conductor forms the loop; the outer conductor provides shielding.
  
  To determine the H-field magnitude, the H-field probe was held at arm's length and rotated until the maximum reading was obtained.],
)<fig_h_field_probe>

The transceiver displays 100 W at $f_0 = 14.1$ MHz. After cable losses, an estimated $P = 94$ W arrives at the antenna. The measured bandwidth $B_"SWR 2.62" = 86.6$ kHz yields $R_T = 0.842 space Omega$ and $I_"main_loop" = 10.5$ A#sub[rms]. From these values, the expected magnetic field strength is calculated using the full retarded magnetic dipole solution, applied to the equivalent-diameter circular approximation of the rectangular loop.

#figure(
  grid(
    columns: (1fr, 1fr),
    gutter: 2mm,
    stack(dir: ttb, spacing: 2mm,
      image("images/h-field_measurements.png", width: 100%),
      image("images/h-field_map_indoor.png", width: 100%),
    ),
    align(bottom, stack(dir: ttb, spacing: 2mm,
      image("images/h-field_point_k_m.png", width: 100%),
      image("images/h-field_point_k_l_m.png", width: 100%),
    )),
  ),
  caption: [Left column, top: measurement points with calculated and measured H-field; the factor shows the ratio of measured to calculated field strength. Left column, bottom: floor plan of the upper story, walls shown in gray; the antenna is shown in red; at the height of the antenna ($Z = 0$, coordinate system as defined in @fig_coordinate_system), several points are measured. Right column, top: measurement points K, M, N, and O in the basement; reinforced concrete is shown with blue hatching. Right column, bottom: measurement points K, L and M.],
)<fig_h_field_measuring>

In summary, the measured field strength agrees surprisingly well with the predicted values.

Near point F, the building's riser pipes are located — thick copper pipes supplying the thermal solar system on the roof. The factor of 2.0 may be explained by this.

When the H-field probe is moved directly along the floor, a strong influence of the underfloor heating — which uses aluminum-coated plastic pipes — is observed.

The measured values at points K, L, and M — located outside the building — are notably large. The building does not appear to attenuate the field significantly.

While the building significantly damps the magnetic loop, it provides only limited shielding of the magnetic field. Thus, damping of the loop and attenuation of the magnetic field are different phenomena.
#pagebreak()
In contrast to the two upper timber-frame stories, the basement is made of reinforced concrete.

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20060705_100023_holz.jpg", height: 8cm),
    image("images/20060331_183157_eisen.jpg", height: 8cm),
  ),
  caption: [Left: impression of the top timber-frame story; at this stage the room was still open, and the antenna was later installed there. The wooden panel still suspended by ropes later became part of the roof. Right: impression of the reinforced-concrete basement level, showing the dense steel reinforcement of one side wall before the concrete was poured.],
)<fig_house_construction>

Points N and O are located in the basement, where the measured factor reaches its minimum value of 0.7. The H-field is likely attenuated by the steel reinforcement, and these points are also closest to the surrounding soil. 

Given the large amount of steel reinforcement, a substantially stronger attenuation might have been expected. However, the measured factor of 0.7 indicates that most of the field still penetrates the reinforced structure.


== Was the elaborately constructed antenna justified?

I use the antenna only indoors because regulations do not allow me to install an antenna on the roof. The effort I invested in reducing the loss resistances is too high for indoor operation.

Here is a concrete example to illustrate this:

At 20 m, I measured an outdoor loss resistance of 0.014 $Omega$. With $R_"loss" = R_L + R_C + R_E$, and assuming $R_E = 0 Omega$, the maximum combined loss resistance of the inductor and capacitor is 0.014 $Omega$. When I use the antenna indoors, $R_"loss"$ increases to 0.607 $Omega$.

This means the loss resistance contributions from the inductor and capacitor become only a very small part of the total losses. The indoor antenna efficiency would therefore remain very similar even if $R_L$ and $R_C$ were higher.

If I were to build another magnetic loop, I would use thinner tubing and air capacitors, since the voltages encountered indoors are sufficiently low.

#pagebreak()
== Is the loop diameter well chosen?

A loop diameter of 1 m was chosen as a practical compromise for indoor use: not so small that capacitor voltages become problematic, and not so large that it sits close to the walls — which, as discussed below, can increase environmental losses.

A smaller loop would be less expensive and easier to handle, though it might perform slightly worse for reception — on HF, especially at lower frequencies where atmospheric noise dominates, this difference is often negligible in practice. A further disadvantage of a smaller loop is the higher voltage that appears across the tuning capacitor for the same transmitted power.

Increasing the loop diameter does not reliably improve the radiated power of an indoor loop. While a larger diameter raises the radiation resistance, it also raises the environmental loss resistance by a similar factor. As the total resistance increases, the loop current decreases accordingly, and the radiated power remains approximately the same.

This may seem to contradict the common claim in the literature that a larger loop diameter improves efficiency — a claim that holds only when antenna-internal losses dominate.

The following thought experiment illustrates why, in the indoor case, antenna efficiency depends only weakly on loop diameter.

#figure(
  image("images/magnetic_dipole_moment_compare.svg", height: 8cm),
  caption: [Comparison of two magnetic loops with diameters of 1.0 m (a) and 0.5 m (b). Both loops produce the same magnetic dipole moment, requiring the smaller loop to carry four times the current. The magnetic field lines differ primarily near the loops.
  The field distribution was calculated using the Biot–Savart law, which is a good approximation in the near-field region (r≪λ).],
)<fig_magnetic_dipole_moment_compare>

#figure(
  image("images/magnetic_dipole_moment_in_box.svg", height: 8cm),
  caption: [Overlay of the field lines of both loops from @fig_magnetic_dipole_moment_compare. The gray hatched region indicates a typical room boundary. Near walls, ceiling, and floor, the field-line pattern is nearly identical for both loops.],
)<fig_magnetic_dipole_moment_in_box>

Because the field-line pattern at the walls is nearly identical for both loops, wall absorption is also similar. In addition, far-field radiation is similar because radiated power is proportional to the square of the magnetic dipole moment.

The key point is this: for a given power delivered to the antenna (for example 100 W), a corresponding magnetic dipole moment is established. If antenna-internal losses are small ($R_L, R_C << R_T$), most of that power is shared between radiation ($R_R$) and environmental losses ($R_E$). A large and a small loop can therefore produce approximately the same dipole moment, and the loop diameter is then not a dominant factor for efficiency.

In some practical indoor cases, increasing the loop size is even expected to reduce efficiency: a larger loop placed closer to a wall will produce a stronger local field at that wall, increasing wall absorption and thus lowering efficiency.

#pagebreak()
== Common-mode currents

A few words on antenna symmetry and common-mode currents:
I made an effort to build the antenna as symmetrically as possible. However, the gamma match alone introduces some asymmetry. For indoor operation, I therefore use a self-built choke combination on both the coax cable and the servo control line: 17 turns on 2 stacked FT240-31 cores, 9 turns on 4 stacked FT240-43 cores, and 9 turns on 3 stacked FT240-52 cores. This combination provides high impedance across the entire frequency range.

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260306_093409237.jpg", height: 8cm), image("images/20251128_141559113.jpg", height: 8cm),
  ),
  caption: [Common-mode choke assemblies used on the coax feed and servo control line. Right: example with RG400, 9 turns on 4 stacked FT240-43 cores. The 3D-printed PETG part keeps the cables in position and separated, thereby reducing parasitic capacitance. I later replaced the RG400 cables with Messi & Paoloni Hyperflex 5, which have lower losses and are more flexible, making them easier to install],
)<fig_common_mode_chokes>

For the outdoor measurement values, I did not use the chokes. I made sure that the feed cables were hanging as centrally as possible relative to the antenna. I installed and removed the chokes again for several test measurements and could not observe any significant influence on the measured bandwidth.

We also performed measurements in which a person held the feed cables by hand. This also showed no significant influence. I therefore conclude that common-mode currents were not significant in my measurements.



== Measurement Setup, Bandwidth Correction
<sec_measurement_setup_bandwidth_correction>

The measurements are performed with a NanoVNA V2 Plus4. The calibration was performed directly at the VNA, not at the antenna feed point. In retrospect, this was incorrect, and I do not recommend performing the measurement this way.

Unfortunately, I forgot to do this, and the outdoor setup has already been dismantled again.

Cables
- 10 m RG8U,
- 5.5 m RG400 (in the chokes, for indoor measurements)
- 2 m RG58.
- About 10 cable connections along the feed line

The cable losses in the following table were measured. These agree very well with the losses specified by the cable manufacturers. A bandwidth correction factor based on these losses was applied, because the measured SWR 2.62 bandwidth at the VNA is larger than at the antenna feed point.

#figure(
  image("images/table_bandwithcorrection.png", width: 70%),
  caption: [Measured indoor and outdoor bandwidths at the VNA, measured cable losses and the resulting correction factors for the bandwidth, corrected bandwidth valid at the antenna feed point.],
)<fig_measured_table_antenna_no_cable>



Details on the bandwidth correction factor can be found in Appendix @app_feeder_loss_q.


I later replaced the cables with lower-loss and more flexible ones: Messi & Paoloni Hyperflex 10, Ultraflex 7, and Hyperflex 5.

== Measurement Results: Heating

I would like to examine one indoor example in more detail.

- Transmit power: 100 W CW @ 28 MHz
- Power loss in cables and connectors: 1 dB, 20 W
- Power delivered to antenna: 80 W
- Damping resistance measured indoors (@fig_measured_antenna) $R_T$: 4.4 Ω

- Power in $R_T$ (damping), all the power fed to the antenna: 80 W
- Radiation resistance calculated (@fig_measured_antenna) $R_"R"$: 1.54 Ω
- Power in $R_"R"$ (radiation): 28 W
- Power in $R_"loss"$, remaining power: 52 W

So I expect that 52 W of power is converted into heat in the antenna or in the surrounding environment.

I would like to estimate how much of this power remains in the antenna itself. For this purpose, I transmit for 10 minutes at 100 W and observe what heats up.

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    box[
      #image("images/20260306_023456_057.jpg", height: 7cm)
      #place(bottom + left, dx: 9%, dy: -5%)[#rect(fill: white, inset: 3pt)[#text(size: 10pt, fill: black)[RG58]]]
      #place(top + right, dx: -5%, dy: 5%)[#rect(fill: white, inset: 3pt)[#text(size: 10pt, fill: black)[RG8U]]]
    ],
    box[
      #image("images/20260306_023550_512.jpg", height: 7cm)
      #place(bottom + left, dx: 3%, dy: -17%)[#rect(fill: white, inset: 3pt)[#text(size: 10pt, fill: black)[RG58]]]
      #place(top + left, dx: 58%, dy: 34%)[#rect(fill: white, inset: 3pt)[#text(size: 10pt, fill: black)[data cable]]]
      #place(top + left, dx: 30%, dy: 20%)[#rect(fill: white, inset: 3pt)[#text(size: 10pt, fill: black)[RG58]]]
    ],
  ),
  caption: [Left: the RG8U feed cable warmed by 1.1°C and the 17-turn choke by 8.2°C, consistent with about 20 W cable/connector loss. Right: three ZCAT1325-0530A clip-on chokes at the antenna warmed by about 8.1°C due to common-mode currents; a control test with a ZCAT choke near the main loop alone showed no noticeable heating.],
)<fig_heating_chokes_1>

#figure(
  image("images/20260306_023416_070.jpg", width: 50%),
  caption: [The antenna itself shows no visible heating (below about 0.3°C at taped measurement points), while the RG58 section from the chokes to the antenna is visibly warmer.],
)<fig_heating_antenna_1>

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260306_023659_769.jpg", height: 7cm), image("images/20260306_133737149.jpg", height: 7cm),
  ),
  caption: [No antenna parts show measurable heating; temperatures are read on painter's tape (emissivity near 1), while shiny metal surfaces can appear hot due to reflected body radiation, so thermal images of reflective objects must be interpreted with care. In the left image, the copper plate surface appears hot, but this is only a reflection of my body heat. The tape labeled A shows the true temperature of the copper plate.],
)<fig_heating_capacitor>



I heat the antenna using a heater with known power. I insert an LED strip into the left section of the main loop and let it run for 10 minutes. The LED power can be determined accurately from the measured current consumption: it is 5 W.

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260306_144719930.jpg", height: 10cm), image("images/20260306_035714_829.jpg", height: 10cm),
  ),
  caption: [Left: view into the left tube section. The LEDs are lit and heat the tube. Right: thermal image of the antenna after 10 minutes with 5 W applied in the left tube section. The temperature rise is clearly visible.],
)<fig_heating_led_5w>

The upper-left area is 24.3°C, and the upper-right area is 22.2°C; the temperature increase is therefore 2.1°C. Conclusion: 5 W of dissipated power is easy to detect. If I transmit with 100 W and cannot measure any heating of the antenna, I assume that the power dissipated in the antenna itself is clearly below 5 W.



#figure(
  image("images/losses.png", width: 100%),
  caption: [Summary of the heating experiment: power budget for 100 W transmit power.],
)<fig_losses_summary>

Findings:
- I have measurable losses of 20 W in the feed cable. These are well characterized losses and I can see them with the thermal camera.
- The antenna does not heat up measurably. I estimate the power dissipated in the clip-on ferrites at 2 W and in the antenna itself at 4 W.
- In free space, the antenna would radiate 28 W based on the radiation resistance $R_"R"$. However, not all of this power will reach the far field, because part of it is absorbed by the building.
- According to the power budget, the building absorbs between 46 W and up to 74 W of RF energy. However, it will not be the full 74 W, because radio operation works well, which suggests that a portion of the power does reach the far field. The H-field measurements in @app_h_field_measurement suggest that the building does not significantly attenuate the H-field. I therefore venture to claim that the majority of the power attributed to $R_"R"$ actually reaches the far field.
- In my indoor setup, the losses are dominated by the building. The antenna itself accounts for only a small fraction of the total losses.



== Is antenna efficiency estimated correctly?

The term antenna efficiency refers to how much power is actually radiated compared to the power delivered to the antenna. However, this is strictly true only in free space, with nothing nearby. This is exactly what we can calculate and state using the standard formulas — correct and well defined. In typical applications on the ground, the earth alone is already in the way, and for that reason alone only a fraction of the power will reach the far field. Especially in the context of magnetic loop antennas, antenna efficiency must be interpreted with caution. It is a useful figure of merit when comparing different magnetic loops against each other. But for the question of how much power actually reaches the far field, the situation is far more complex.


== Measurement uncertainty

Many factors influence the measurement results. Opening a window (with triple-glazed glass and an aluminum frame), slightly rotating the antenna, or routing a cable differently all affect the antenna behavior. When the antenna is outdoors at a height of 5 m and sways in the wind, the effect is even greater.

During measurements at 5 m height and with high Q values, the resonant-circuit trace in the Smith chart was no longer as circular as in textbook examples. I therefore adjusted the frequency slightly each time until the curve looked reasonable, measured the bandwidth, and then continued with the next measurement. Even though the results are given with many digits, this should not obscure the fact that the measurement uncertainty is large.

== Is the radiation resistance correct at higher frequencies?

The investigated antenna has a very large surface area because the tube diameter is 100 mm. Could this possibly be a combination in which the loop antenna also exhibits characteristics of a shortened dipole in the 10 m band? Additional radiation would result in a larger radiation resistance than the value I approximated using the King model. An underestimated radiation resistance could explain the small antenna efficiency determined at higher frequencies, e.g., outdoor in the 10 m band.
I look forward to feedback from antenna experts.



#pagebreak()
= The Journey Is the Reward

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260309_133329952.jpg", height: 7cm),

    image("images/20260309_133332512.jpg", height: 7cm),
  ),
  caption: [Not everything worked on the first attempt — it was a tough journey with many setbacks. But it was fun.],
)<fig_journey_1>

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/20260309_133812026.jpg", height: 7cm), image("images/20251220_084918396.jpg", height: 7cm),
  ),
  caption: [Many things ended up in the bin — or, in the case of this magnetic loop, in the scrap copper collection.],
)<fig_journey_2>
#figure(
  image("images/map.png", width: 55%),
  caption: [Map of digital-mode contacts made during the first months of operation. Source: GridTracker. I had many joyful hours on the air.],
)<fig_first_months_contacts_map>

#pagebreak()
= Acknowledgments

Many thanks to my brother Hans, who invested many days of work to help me develop software for automated measurement and tuning.

Many thanks to Peter Schär, who assisted me during the outdoor measurements — “a bit further to the left, wait, I need to measure again…”.

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/peter_hans.jpg", height: 7cm), image("images/peter_schaer.jpg", height: 7cm),
  ),
  caption: [Left: Peter Märki with his brother Hans Märki; right: Peter Schär measuring antenna height above ground with a laser distance meter. We were concerned that the ladder might fail and the antenna could fall; despite this risk, he lay down beneath the antenna to take the measurement.],
)<fig_acknowledgments>

#figure(
  grid(
    columns: (auto, auto),
    gutter: 2mm,
    image("images/markus_peter.jpg", height: 7cm), image("images/20260710_083956327_peter.jpg", height: 7cm),
  ),
  caption: [The authors: left, Markus Niese with Peter Märki; right, Loopie with Peter Märki.],
)

Many thanks to the numerous other people with whom I had stimulating discussions and received valuable input.

#pagebreak()
= References

- [1] K. Solbach, "Magnetic Loop Antenna: Design, calculations, simulations, equivalent circuit, measurements and improved understanding of the operation," Faculty of Engineering, University of Duisburg‑Essen, Mar. 22, 2022. DOI: 10.17185/duepublico/75498. URN: urn:nbn:de:hbz:465-20220322-135255-6.
- [2] K. Rothammel, *Rothammels Antennenbuch*, 13., aktualisierte und erweiterte Aufl. (in German), DARC Verlag, Baunatal, Germany, 2013.
- [3] F. Dörenberg, "Magnetic loop antenna (magloop)," Nonstop Systems, [Online]. Available: https://www.hellschreiber.com/radio. Accessed: Dec. 31, 2025.

#v(1em)
#set text(size: 8pt)
*Credits:* Green person: José Pedro, CC BY‑NC‑SA 4.0, https://www.printables.com/model/1389190-super-collection-of-miniature-people-194-figures.
#set text(size: 11pt)


= Appendix

== Measurement at SWR 2.62
<app_swr>

The bandwidth of the unloaded parallel RLC resonant circuit is generally defined by the frequencies where the reactive part of the impedance equals the resistive part ($X = R$).
At these points, with a system impedance of $50 Omega$, the input impedance becomes $Z_"in" = 50 Omega (1 plus.minus j)$.

The reflection coefficient $Gamma$  at the band limit is given by:

$
  Gamma = (Z_"in" - 50 Omega) / (Z_"in" + 50 Omega) = (plus.minus j 50 Omega) / (100 Omega plus.minus j 50 Omega) = (plus.minus j) / (2 plus.minus j)
$

The magnitude of the reflection coefficient is the ratio of the magnitudes of the numerator and the denominator:

$ abs(Gamma) = abs(plus.minus j) / abs(2 plus.minus j) $

Using $abs(a + j b) = sqrt(a^2 + b^2)$, we get:

$ abs(plus.minus j) = sqrt(0^2 + 1^2) = 1 $
$ abs(2 plus.minus j) = sqrt(2^2 + 1^2) = sqrt(5) $

Thus:

$ abs(Gamma) = 1 / sqrt(5) $

With this result, the SWR becomes:

$ "SWR" = (1 + abs(Gamma)) / (1 - abs(Gamma)) = (sqrt(5) + 1) / (sqrt(5) - 1) approx 2.62 $


By measuring the bandwidth $B_"SWR 2.62"$ between the frequencies where the SWR reaches 2.62, the intrinsic quality factor (unloaded quality factor) can be calculated directly:

$ Q_0 = f_0 / B_"SWR 2.62" $

== Measurement at 3 dB Bandwidth
<app_bandwidth_3db>

When operating the antenna (transmitting or receiving), the system bandwidth is determined by the loaded quality factor $Q_L$.
In a perfectly matched system (critical coupling), the source impedance of the transceiver is transformed towards the antenna to match the antenna's total loss resistance $R_T$.

Consequently, the effective damping resistance in the loaded circuit $R_"loaded"$ is the sum of the antenna's total resistance $R_T$ and the transformed source resistance:

$ R_"loaded" = R_T + R_"transceiver,transformed" = R_T + R_T = 2 R_T $


The loaded quality factor $Q_L$ is then:

$ Q_L = X_L / R_"loaded" = X_L / (2 R_T) $

Since the 3 dB bandwidth is related to the quality factor we obtain:

$ Delta f_"3dB" = f_0 / Q_L = 2 dot f_0 / Q_0 $

This shows that the bandwidth of the matched system is twice that of the unloaded antenna (where only $R_T$ determines the damping).

== Effect of feeder loss on measured Q factor
<app_feeder_loss_q>

I do not recommend measuring this type of antenna the way I did. It is better to include the feed-line in the VNA calibration. For my measurement approach, the corresponding correction factor calculation is given in @sec_measurement_setup_bandwidth_correction.


When Q is derived from the measured bandwidth, feeder attenuation between the VNA and the antenna feed point biases the result if the trace is evaluated without full calibration/de-embedding. Therefore, I apply a correction factor and briefly justify it from the Lorentz resonance shape combined with transmission-line attenuation.

For a resonator, the reflected-power response around resonance can be approximated by a Lorentz form:

$ P(f) approx 1 / (1 + (2 Q Delta f / f_0)^2) $

Let $L$ be the one-way feeder attenuation in dB. The round-trip attenuation to the antenna and back is then:

$ A = 10^(-2L/10) $

so the power seen by an uncalibrated VNA is:

$ P_"meas"(f) = A dot P(f) $

If the bandwidth is taken at the conventional 3 dB level of the unscaled trace ($P_"meas" = 0.5$), this gives:

$ 0.5 = A / (1 + (B_"meas" / B_"real")^2) $

and therefore:

$ B_"real" = B_"meas" dot k, quad k = sqrt(2 dot 10^(-2L/10) - 1) $

This correction reduces the measured bandwidth to the equivalent value at the antenna feed point.

== Terminology

"Quality factor" and "bandwidth" are referred to differently in the literature. To avoid confusion, it is important to clearly distinguish the terms. The following unambiguous designations are recommended:

- Intrinsic quality factor (or unloaded quality factor) of the antenna
- Loaded quality factor of the antenna (with the transceiver connected)
- Bandwidth at SWR 2.62 of the antenna
- 3 dB bandwidth of antenna with transceiver connected

