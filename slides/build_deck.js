// Builds FSO_assignment_presentation.pptx (10 slides, 16:9)
const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");
const { applyTheme } = require("/mnt/skills/public/pptx/scripts/apply_theme.js");

const IMG = (f) => path.join(__dirname, "img", f);
const NOTES = JSON.parse(fs.readFileSync(path.join(__dirname, "notes.json"), "utf8"));

const THEME = {
  name: "FSO Night Link",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "14213D", lt1: "FFFFFF", dk2: "3A4A63", lt2: "EEF2F7",
    accent1: "E4572E", accent2: "1F7A8C", accent3: "2E9E44", accent4: "D99A00",
    accent5: "D6337F", accent6: "6B7A90", hlink: "1F7A8C", folHlink: "6B7A90",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.author = "Sweety Kumari Vishwakarma";
pres.title = "Simplified FSO channel model: assignment solution";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "DARK",
  background: { color: HEX.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.35, w: 8.8, h: 1.5,
        fontFace: THEME.headFontFace, fontSize: 32, bold: true, color: C.background1, valign: "bottom" },
        text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.0, w: 8.8, h: 2.1,
        fontFace: THEME.bodyFontFace, fontSize: 16, color: "C9D3E3", valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "DARK_LIST",
  background: { color: HEX.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.45, w: 8.8, h: 0.8,
        fontFace: THEME.headFontFace, fontSize: 32, bold: true, color: C.background1, valign: "middle", margin: 0 },
        text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 1.45, w: 8.8, h: 3.7,
        fontFace: THEME.bodyFontFace, fontSize: 16, color: "D9E1EE", valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: HEX.lt1 },
  margin: [0.4, 0.5, 0.4, 0.5],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.22, w: 9.0, h: 0.62,
        fontFace: THEME.headFontFace, fontSize: 26, bold: true, color: C.text1, valign: "middle", margin: 0 },
        text: "" } },
    { text: { text: "FSO channel with turbulence and pointing errors  ·  S. K. Vishwakarma",
        options: { x: 0.5, y: 5.28, w: 6.5, h: 0.25, fontFace: THEME.bodyFontFace, fontSize: 9,
          color: C.accent6, margin: 0 } } },
  ],
  slideNumber: { x: 9.1, y: 5.26, w: 0.4, h: 0.28, fontFace: THEME.bodyFontFace, fontSize: 9,
    color: HEX.accent6, align: "right" },
});

// ---------- helpers ----------
let n = 0;
function addSlide(master, section) {
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  s.addNotes(NOTES[n++]);
  return s;
}
function img(s, file, x, y, w, h, name) {
  s.addImage({ path: IMG(file), x, y, w, h, objectName: name || file });
}
function eqImg(s, file, x, y, h, ratio, name) {
  s.addImage({ path: IMG(file), x, y, w: h * ratio, h, objectName: name || file });
}
function card(s, x, y, w, h, fill, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08,
    fill: { color: fill }, line: { color: fill }, objectName: name });
}
function txt(s, runs, opt) {
  s.addText(runs, Object.assign({ isTextBox: true, fontFace: THEME.bodyFontFace, fontSize: 14,
    color: C.text1, valign: "top", margin: 0.05 }, opt));
}
function bullets(items, size = 14, color = C.text1) {
  return items.map((t, i) => {
    const runs = Array.isArray(t) ? t : [{ text: t }];
    return runs.map((r, j) => ({
      text: r.text,
      options: Object.assign({ fontSize: size, color, bullet: j === 0 ? { indent: 14 } : undefined,
        breakLine: j === runs.length - 1 && i < items.length - 1, paraSpaceAfter: size >= 18 ? 12 : 5 }, r.options || {}),
    }));
  }).flat();
}
const OP = { green: HEX.accent3, yellow: HEX.accent4, pink: HEX.accent5 };

// =====================================================================
// 1. Title
pres.addSection({ title: "Introduction" });
{
  const s = addSlide("DARK", "Introduction");
  s.addText("A simplified FSO channel model with weak turbulence and pointing errors",
    { placeholder: "title" });
  s.addText([
    { text: "Assignment solution: model, reproduction of Fig. 2, accuracy, outage, and a follow-up",
      options: { breakLine: true } },
    { text: " ", options: { fontSize: 10, breakLine: true } },
    { text: "Sweety Kumari Vishwakarma", options: { bold: true, color: C.background1, breakLine: true } },
    { text: "ICT Lab, TU/e  ·  paper: C. Álvarez Roa et al., ICTON 2024", options: { fontSize: 13 } },
  ], { placeholder: "body" });
  // motif: three operating-point dots
  ["green", "yellow", "pink"].forEach((k, i) => s.addShape(pres.shapes.OVAL,
    { x: 0.6 + i * 0.32, y: 0.8, w: 0.2, h: 0.2, fill: { color: OP[k] }, line: { color: OP[k] },
      objectName: "dot-" + k }));
}

// =====================================================================
// 2. Model
pres.addSection({ title: "Task 1: model" });
{
  const s = addSlide("CONTENT", "Task 1: model");
  s.addText("The channel is a product of three losses", { placeholder: "title" });
  // flow chain
  const steps = ["bits", "OOK {0, 2P}", "h = h_l · h_p · h_a", "+ n", "ML: y > ηhP"];
  const xs = [0.5, 1.75, 3.35, 5.75, 6.85];
  const ws = [1.0, 1.35, 2.15, 0.85, 1.6];
  steps.forEach((t, i) => {
    const hl = i === 2;
    card(s, xs[i], 1.02, ws[i], 0.5, hl ? HEX.dk1 : HEX.lt2, "flow-" + i);
    txt(s, t, { x: xs[i], y: 1.02, w: ws[i], h: 0.5, align: "center", valign: "middle",
      fontSize: 14, bold: hl, color: hl ? C.background1 : C.text1, objectName: "flowtxt-" + i });
    if (i < steps.length - 1) s.addShape(pres.shapes.RIGHT_ARROW, { x: xs[i] + ws[i] + 0.05, y: 1.18,
      w: xs[i + 1] - xs[i] - ws[i] - 0.1, h: 0.18, fill: { color: HEX.accent6 }, line: { color: HEX.accent6 },
      objectName: "arrow-" + i });
  });
  txt(s, "eq. (1):  y = ηhx + n,  perfect CSI at the receiver", { x: 5.75, y: 1.55, w: 3.8, h: 0.28, fontSize: 11, color: C.accent6,
    objectName: "eq1" });

  const cards = [
    { t: "h_l   atmospheric loss", tag: "deterministic", c: HEX.accent6,
      b: ["Beer–Lambert, changes over minutes–hours", "0.2208 dB/km × 3 km → h_l = 0.859"] },
    { t: "h_p   spread + pointing", tag: "random", c: HEX.accent2,
      b: ["w_z = 1.98 m ≫ a = 5 cm → A₀ = 1.27·10⁻³", "Gaussian x, y jitter → R Rayleigh → eq. (6)",
          "h_p/A₀ = e^(−V), V ~ Exp(γ²) → eq. (7), γ = w_zeq / 2σ_s"] },
    { t: "h_a   turbulence", tag: "random", c: HEX.accent1,
      b: ["log-amplitude χ Gaussian (Rytov, CLT)", "h_a = e^(2χ), E[h_a] = 1 → eq. (5)",
          "σ_X² ≈ σ_R²/4, σ_R² = 1.23 Cn² k^(7/6) L^(11/6)"] },
  ];
  cards.forEach((cd, i) => {
    const x = 0.5 + i * 3.05, y = 1.95, w = 2.85, h = 2.95;
    card(s, x, y, w, h, HEX.lt2, "card-" + i);
    txt(s, cd.t, { x: x + 0.15, y: y + 0.12, w: w - 0.3, h: 0.4, fontFace: THEME.headFontFace,
      fontSize: 16, bold: true, objectName: "cardtitle-" + i });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.15, y: y + 0.58, w: 1.25, h: 0.3, rectRadius: 0.06,
      fill: { color: cd.c }, line: { color: cd.c }, objectName: "tag-" + i });
    txt(s, cd.tag, { x: x + 0.15, y: y + 0.58, w: 1.25, h: 0.3, fontSize: 11, bold: true, align: "center",
      valign: "middle", color: C.background1, objectName: "tagtxt-" + i });
    txt(s, bullets(cd.b, 13), { x: x + 0.12, y: y + 1.0, w: w - 0.24, h: h - 1.1, objectName: "cardbody-" + i });
  });
}

// =====================================================================
// 3. Change of variable
{
  const s = addSlide("CONTENT", "Task 1: model");
  s.addText("One change of variable explains the model", { placeholder: "title" });
  eqImg(s, "eq_z.png", 0.5, 0.98, 0.5, 10.889, "eq-z");
  eqImg(s, "eq_10.png", 0.6, 1.62, 0.33, 10.077, "eq-10");
  eqImg(s, "eq_14.png", 5.1, 1.55, 0.45, 6.962, "eq-14");
  txt(s, "Gaussian (turbulence) minus exponential (pointing): one shape parameter κ",
    { x: 0.5, y: 2.12, w: 9.0, h: 0.3, fontSize: 13, italic: true, color: C.accent6, objectName: "eq-caption" });
  img(s, "s_pdf_z.png", 0.5, 2.48, 9.0, 9.0 / 3.47, "pdf-z");
}

// =====================================================================
// 4. Instability
{
  const s = addSlide("CONTENT", "Task 1: model");
  s.addText("Why eq. (10) breaks for small σ_s, and the fix", { placeholder: "title" });
  eqImg(s, "eq_nan.png", 0.5, 1.0, 0.56, 8.177, "eq-nan");
  txt(s, "green point, γ² = 68: double precision holds only e^−745 … e^709", {
    x: 0.5, y: 1.62, w: 4.7, h: 0.3, fontSize: 12, italic: true, color: C.accent6, objectName: "nan-cap" });
  txt(s, bullets([
    "Each factor is of size e^(±κ²/2); the product is O(1) but no factor is representable",
    "Small σ_s → large γ² → exponent grows like κ²/2 = γ⁴σ_R²/2",
    [{ text: "Fix: ", options: { bold: true } }, { text: "add exponents first, use log Q (scipy log_ndtr)" }],
  ], 14), { x: 0.5, y: 2.05, w: 4.6, h: 1.95, objectName: "nan-bullets" });
  eqImg(s, "eq_log.png", 0.6, 4.1, 0.36, 9.74, "eq-log");
  txt(s, "exact and stable everywhere — no approximation needed for the PDF", {
    x: 0.5, y: 4.55, w: 4.7, h: 0.3, fontSize: 12, italic: true, color: C.accent2, objectName: "log-cap" });
  img(s, "fig_instability.png", 5.35, 1.65, 4.15, 4.15 / 1.349, "instab");
}

// =====================================================================
// 5. Fig 2 reproduced
pres.addSection({ title: "Task 2: Fig. 2" });
{
  const s = addSlide("CONTENT", "Task 2: Fig. 2");
  s.addText("Fig. 2 reproduced: Monte Carlo, exact (16), (17), (18)", { placeholder: "title" });
  img(s, "fig_ber.png", 0.4, 0.95, 5.6, 5.6 / 1.349 > 4.2 ? 4.2 : 5.6 / 1.349, "ber");
  const rows = [
    ["", "Δ17 ours", "Δ17 paper", "Δ18 ours"],
    ["green", "0.0004", "≈ 0", "0.75"],
    ["yellow", "0.018", "0.02", "0.44"],
    ["pink", "1.30 *", "0.18", "1.37"],
  ];
  s.addTable(rows.map((r, i) => r.map((c, j) => ({ text: c, options: {
      bold: i === 0 || j === 0, color: j === 0 && i > 0 ? OP[c] : HEX.dk1,
      fill: { color: i === 0 ? HEX.lt2 : HEX.lt1 }, align: j === 0 ? "left" : "center" } }))),
    { x: 6.2, y: 1.0, w: 3.3, colW: [0.75, 0.85, 0.85, 0.85], fontFace: THEME.bodyFontFace, fontSize: 13,
      border: { type: "solid", pt: 0.5, color: "D5DCE6" }, rowH: 0.36, objectName: "delta-table" });
  txt(s, "Δ in dB at the HD-FEC limit 3.84·10⁻³.  * depends on the lower integration limit (next slide)",
    { x: 6.2, y: 2.85, w: 3.3, h: 0.55, fontSize: 11, color: C.accent6, objectName: "table-note" });
  txt(s, bullets([
    "8 of 9 operating points: Δ17 within 0.015 dB of the paper",
    "MC (4·10⁶ bits/point) within 2.7σ of exact (16) at 40 of 41 powers",
    "(18) is 0.4–0.8 dB pessimistic, as in the paper",
  ], 13), { x: 6.2, y: 3.5, w: 3.3, h: 1.65, objectName: "ber-bullets" });
}

// =====================================================================
// 6. Green & pink
{
  const s = addSlide("CONTENT", "Task 2: Fig. 2");
  s.addText("Two cases the paper could not resolve", { placeholder: "title" });
  img(s, "s_green_pink.png", 0.5, 0.92, 9.0, 9.0 / 2.7, "green-pink");
  card(s, 0.5, 4.33, 4.4, 0.85, HEX.lt2, "cap-green-bg");
  txt(s, [{ text: "Green: ", options: { bold: true, color: OP.green } },
    { text: "(16) literally → NaN at every P. In log form it is finite and lies on the Monte Carlo points." }],
    { x: 0.6, y: 4.38, w: 4.2, h: 0.75, fontSize: 13, valign: "middle", objectName: "cap-green" });
  card(s, 5.1, 4.33, 4.4, 0.85, HEX.lt2, "cap-pink-bg");
  txt(s, [{ text: "Pink: ", options: { bold: true, color: OP.pink } },
    { text: "(14) has a 1/(z+κ) pole at ĥ, so (17) diverges like ln(1/δ). Δ17 = 0.21 dB (δ=0.1) … 1.30 dB (δ=10⁻⁶)." }],
    { x: 5.2, y: 4.38, w: 4.2, h: 0.75, fontSize: 13, valign: "middle", objectName: "cap-pink" });
}

// =====================================================================
// 7. Task 3
pres.addSection({ title: "Task 3: accuracy" });
{
  const s = addSlide("CONTENT", "Task 3: accuracy");
  s.addText("Area under (14) and accuracy are set by κ", { placeholder: "title" });
  img(s, "fig_area.png", 0.4, 0.92, 9.2, 9.2 / 2.868, "area");
  eqImg(s, "eq_area.png", 0.5, 4.25, 0.36, 10.316, "eq-area");
  txt(s, bullets([
    "erfc argument ≈ κ/√2 → error of (13) ≈ 1/κ²",
    "more turbulence or less jitter → larger κ",
    "bounded Q (Börjesson–Sundberg): |Δ| < 0.004 dB at all 9 points",
  ], 13), { x: 4.45, y: 4.12, w: 5.1, h: 1.1, objectName: "area-bullets" });
}

// =====================================================================
// 8. Outage
pres.addSection({ title: "Task 4: outage" });
{
  const s = addSlide("CONTENT", "Task 4: outage");
  s.addText("Stretch (b): a coded link sees outage, not average BER", { placeholder: "title" });
  img(s, "s_outage.png", 0.4, 0.95, 5.0, 5.0 / 1.439, "outage");
  txt(s, [{ text: "10⁷ – 5·10⁷", options: { fontSize: 30, bold: true, color: C.accent2, fontFace: THEME.headFontFace, breakLine: true } },
    { text: "symbols per fade (10 GBd, T_c = 1–5 ms) ≫ codeword: each codeword sees one h", options: { fontSize: 13 } }],
    { x: 5.65, y: 0.98, w: 3.9, h: 1.15, objectName: "stat-symbols" });
  eqImg(s, "eq_out.png", 5.65, 2.2, 0.255, 14.821, "eq-out");
  txt(s, "extra power for P_out = 10⁻³ vs. average-BER design", { x: 5.65, y: 2.6, w: 3.9, h: 0.3,
    fontSize: 12, italic: true, color: C.accent6, objectName: "pen-cap" });
  const pen = [["green", "6.9 dB"], ["yellow", "5.5 dB"], ["pink", "3.6 dB"]];
  pen.forEach(([k, v], i) => {
    const x = 5.65 + i * 1.32;
    card(s, x, 2.95, 1.2, 1.0, HEX.lt2, "pen-bg-" + k);
    txt(s, [{ text: v, options: { fontSize: 22, bold: true, color: OP[k], fontFace: THEME.headFontFace, breakLine: true } },
      { text: k, options: { fontSize: 12, color: C.text2 } }],
      { x, y: 3.0, w: 1.2, h: 0.9, align: "center", valign: "middle", objectName: "pen-" + k });
  });
  txt(s, "Average BER mixes good blocks with rare BER≈½ fades that no FEC fixes; it is the right metric only with very deep interleaving.",
    { x: 5.65, y: 4.1, w: 3.9, h: 1.0, fontSize: 13, objectName: "outage-msg" });
}

// =====================================================================
// 9. What next
pres.addSection({ title: "Task 5: what next" });
{
  const s = addSlide("CONTENT", "Task 5: what next");
  s.addText("What next: how deep must the interleaver be?", { placeholder: "title" });
  img(s, "s_interleaver.png", 0.4, 0.95, 4.9, 4.9 / 1.408, "interleaver");
  txt(s, [{ text: "Proposal", options: { bold: true, fontFace: THEME.headFontFace, fontSize: 16, breakLine: true } },
    { text: "Power needed for a codeword-failure target vs. interleaver depth N (latency N·T_c), derived for this channel.",
      options: { fontSize: 13 } }], { x: 5.55, y: 0.98, w: 4.0, h: 0.95, objectName: "prop" });
  txt(s, [{ text: "First result (Monte Carlo)", options: { bold: true, fontFace: THEME.headFontFace, fontSize: 16, breakLine: true } }]
    .concat(bullets(["N < 130: interleaving does not help; one BER≈½ block fails the codeword",
      "N = 1024 (≈1 s at 1 ms): still 1.1 dB from the infinite-interleaver result"], 13)),
    { x: 5.55, y: 1.98, w: 4.0, h: 1.35, objectName: "result" });
  txt(s, [{ text: "Why it matters", options: { bold: true, fontFace: THEME.headFontFace, fontSize: 16, breakLine: true } }]
    .concat(bullets(["the design number for real FSO / satellite links with latency budgets",
      "tractable: EMG model, closed-form N=1, Chernoff bound via E[e^(sZ)] = e^(s²/2) κ/(κ+s)",
      "points to CSI-based erasures of deep fades"], 13)),
    { x: 5.55, y: 3.38, w: 4.0, h: 1.8, objectName: "why" });
}

// =====================================================================
// 10. Summary
pres.addSection({ title: "Summary" });
{
  const s = addSlide("DARK_LIST", "Summary");
  s.addText("Summary", { placeholder: "title" });
  s.addText(bullets([
    "z = W − E′ with κ = γ²σ_R: (10) is κe^(κz+κ²/2)Q(z+κ), (14) is φ(z)/(1+z/κ)",
    "(10) fails as ∞·0; in log form it is exact everywhere and matches Monte Carlo",
    "Fig. 2 reproduced; Δ17 within 0.015 dB at 8 of 9 points; pink: (17) diverges at ĥ",
    "accuracy ↑ with κ; a bounded Q gives |Δ| < 0.004 dB everywhere",
    "coded links: outage is closed form, 3.6–6.9 dB above average-BER design; next: finite interleaver depth",
  ], 18, "D9E1EE"), { placeholder: "body" });
}

(async () => {
  const out = path.join(__dirname, "FSO_assignment_presentation.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("written", out);
})();
