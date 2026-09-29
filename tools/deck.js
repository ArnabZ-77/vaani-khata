const pptxgen = require("pptxgenjs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625
pres.title = "Vaani Khata - Snapdragon AI Lab Build & Present Challenge";

const INK = "141416", CARD = "1E1E22", ACC = "FF7A45", MUTE = "A0A0AC", WHITE = "FFFFFF", GREEN = "4CC38A";
const H = "Cambria", B = "Calibri";

function base(title, dark = true) {
  const s = pres.addSlide();
  s.background = { color: dark ? INK : WHITE };
  s.addText(title, { x: 0.5, y: 0.35, w: 9, h: 0.8, fontFace: H, fontSize: 32, bold: true, color: dark ? WHITE : INK, isTextBox: true, margin: 0 });
  return s;
}
const txt = (s, t, o) => s.addText(t, Object.assign({ fontFace: B, fontSize: 15, color: WHITE, isTextBox: true, margin: 0, valign: "top" }, o));

// 1. Title
let s = pres.addSlide(); s.background = { color: INK };
txt(s, "SNAPDRAGON® AI LAB BUILD & PRESENT CHALLENGE", { x: 0.6, y: 0.7, w: 8.8, h: 0.4, fontSize: 12, color: ACC, bold: true, charSpacing: 3 });
txt(s, "Vaani Khata", { x: 0.6, y: 1.5, w: 8.8, h: 1.1, fontFace: H, fontSize: 60, bold: true });
txt(s, "Speak your shop's ledger. Hindi, English or Hinglish.\nTranscribed on the Snapdragon NPU. Nothing leaves the laptop.", { x: 0.6, y: 2.8, w: 8.2, h: 1.0, fontSize: 20, color: "D8D8DE" });
txt(s, "Individual entry  ·  Built and measured on a Snapdragon X laptop (Galaxy Book4 Edge, Windows 11 ARM64)", { x: 0.6, y: 4.9, w: 8.8, h: 0.4, fontSize: 12, color: MUTE });

// 2. Problem
s = base("The khata is still on paper");
const probs = [
  ["Paper is fragile", "Kirana shopkeepers track credit (udhaar) in handwritten books. Entries get lost, disputed, or forgotten."],
  ["Apps assume typing and internet", "Cloud ledger apps need connectivity, an account, and typing in English menus during a rush."],
  ["Customer data leaves the shop", "Who owes what is sensitive. Cloud apps upload it. Voice makes that worse."],
];
probs.forEach((p, i) => {
  const y = 1.45 + i * 1.25;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y, w: 9, h: 1.05, fill: { color: CARD }, rectRadius: 0.1 });
  s.addShape(pres.shapes.OVAL, { x: 0.75, y: y + 0.27, w: 0.5, h: 0.5, fill: { color: ACC } });
  txt(s, String(i + 1), { x: 0.75, y: y + 0.27, w: 0.5, h: 0.5, fontFace: H, fontSize: 18, bold: true, color: INK, align: "center", valign: "middle" });
  txt(s, p[0], { x: 1.5, y: y + 0.13, w: 7.8, h: 0.35, fontSize: 18, bold: true });
  txt(s, p[1], { x: 1.5, y: y + 0.5, w: 7.8, h: 0.5, fontSize: 13.5, color: "C4C4CC" });
});

// 3. How it works
s = base("Talk to it like you talk to your helper");
const steps = [["Speak", "Tap once. \"Ramesh ne 500 rupaye udhaar liye.\""], ["Whisper on NPU", "AI Hub Whisper-Base, Hexagon NPU via QNN"], ["Understand", "Entry type, person, amount, item, spoken in Hindi or English"], ["Khata", "Local SQLite. Balances update; ask \"Ramesh ka kitna baaki?\""]];
steps.forEach((p, i) => {
  const x = 0.5 + i * 2.32;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.6, w: 2.1, h: 2.3, fill: { color: i === 1 ? ACC : CARD }, rectRadius: 0.1 });
  txt(s, String(i + 1), { x: x + 0.2, y: 1.75, w: 0.6, h: 0.5, fontFace: H, fontSize: 26, bold: true, color: i === 1 ? INK : ACC });
  txt(s, p[0], { x: x + 0.2, y: 2.35, w: 1.7, h: 0.4, fontSize: 17, bold: true, color: i === 1 ? INK : WHITE });
  txt(s, p[1], { x: x + 0.2, y: 2.8, w: 1.7, h: 1.0, fontSize: 12.5, color: i === 1 ? INK : "C4C4CC" });
});
txt(s, "Auto-detects Hindi vs English. Hindi and English spellings of one name (रमेश / Ramesh) merge into one customer.", { x: 0.5, y: 4.35, w: 9, h: 0.6, fontSize: 15, color: "D8D8DE" });

// 4. Why NPU - chart + stats
s = base("Why the NPU: measured on this laptop");
s.addChart(pres.charts.BAR, [{ name: "Encoder latency, 30 s audio (ms)", labels: ["Hexagon NPU (fp16)", "Oryon CPU (fp32)"], values: [45, 1030] }], {
  x: 0.5, y: 1.4, w: 5.2, h: 3.4, barDir: "bar", chartColors: [ACC], showValue: true, dataLabelColor: WHITE, dataLabelFontSize: 13, dataLabelPosition: "outEnd",
  catAxisLabelColor: "D8D8DE", catAxisLabelFontSize: 13, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
  showLegend: false, showTitle: true, title: "Whisper-Base encoder latency (ms, lower is better)", titleColor: "D8D8DE", titleFontSize: 12,
});
[["~23x", "faster than CPU (typical of 5 runs; 6.6x in the slowest outlier run)"], ["45x", "real-time: a 10.8 s spoken clip transcribed end to end in ~240 ms"], ["0 bytes", "of audio or ledger data leave the device"]].forEach((p, i) => {
  const y = 1.4 + i * 1.15;
  txt(s, p[0], { x: 6.0, y, w: 3.5, h: 0.6, fontFace: H, fontSize: 32, bold: true, color: i === 2 ? GREEN : ACC });
  txt(s, p[1], { x: 6.0, y: y + 0.6, w: 3.5, h: 0.5, fontSize: 12, color: "C4C4CC" });
});
txt(s, "Baseline: open whisper-base encoder (same architecture) on the ONNX Runtime CPU EP. Full runs in docs/benchmark.md.", { x: 0.5, y: 4.95, w: 9, h: 0.35, fontSize: 10.5, color: MUTE });

// 5. Product
s = base("The working app");
s.addImage({ path: path.join(ROOT, "docs", "img", "app.png"), x: 0.5, y: 1.3, w: 4.6, h: 4.18 });
[["Tap to speak", "Mic in the browser, audio processed by a localhost Python server. No account."], ["Live ledger and balances", "Credit, payment and sale entries with the exact words heard for each."], ["Ask by voice", "\"How much does Ramesh owe?\" answers from the local database."], ["Offline badge", "Works with Wi-Fi off. Latency shown on screen every time."]].forEach((p, i) => {
  const y = 1.3 + i * 1.05;
  txt(s, p[0], { x: 5.4, y, w: 4.1, h: 0.35, fontSize: 17, bold: true, color: ACC });
  txt(s, p[1], { x: 5.4, y: y + 0.36, w: 4.1, h: 0.6, fontSize: 13, color: "D8D8DE" });
});

// 6. Deployment & accessibility
s = base("Built to actually be deployed", false);
const cols = [["Runs where shops are", "Any Snapdragon X Windows laptop. One setup script downloads the AI Hub model. No GPU, no cloud, no monthly bill."], ["Accessible by voice", "Hindi and English today. No typing, no menus. The same NPU model family scales to more Indian languages."], ["Private by design", "Server binds to 127.0.0.1. Data lives in one SQLite file on the shopkeeper's own machine."]];
cols.forEach((p, i) => {
  const x = 0.5 + i * 3.05;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.5, w: 2.85, h: 2.6, fill: { color: "F3F1EC" }, rectRadius: 0.1 });
  txt(s, p[0], { x: x + 0.2, y: 1.7, w: 2.45, h: 0.7, fontFace: H, fontSize: 18, bold: true, color: INK });
  txt(s, p[1], { x: x + 0.2, y: 2.45, w: 2.45, h: 1.6, fontSize: 13, color: "3A3A42" });
});
txt(s, "Next: Llama 3.2 3B on the NPU for free-form sentences, GST-ready sales summaries, and more languages with Whisper-Small.", { x: 0.5, y: 4.4, w: 9, h: 0.7, fontSize: 15, color: INK });

// 7. Honest status
s = base("What is real today");
txt(s, "Working, measured on-device", { x: 0.5, y: 1.4, w: 4.3, h: 0.4, fontSize: 16, bold: true, color: GREEN });
txt(s, [
  { text: "Whisper-Base encoder + decoder on the Hexagon NPU (QNN)", options: { bullet: true, breakLine: true } },
  { text: "Speech to ledger entries, balances, spoken balance queries", options: { bullet: true, breakLine: true } },
  { text: "Hindi/English name merging, offline operation", options: { bullet: true, breakLine: true } },
  { text: "Reproducible benchmark script and logged results", options: { bullet: true } },
], { x: 0.5, y: 1.9, w: 4.3, h: 2.6, fontSize: 14, color: "D8D8DE", paraSpaceAfter: 8 });
txt(s, "Known limits", { x: 5.2, y: 1.4, w: 4.3, h: 0.4, fontSize: 16, bold: true, color: ACC });
txt(s, [
  { text: "Sentence parsing is rule-based, so unusual phrasing can be missed", options: { bullet: true, breakLine: true } },
  { text: "Whisper-Base accuracy drops on noisy shops and heavy accents", options: { bullet: true, breakLine: true } },
  { text: "CPU baseline is the same architecture from an open ONNX export, not the identical file", options: { bullet: true } },
], { x: 5.2, y: 1.9, w: 4.3, h: 2.6, fontSize: 14, color: "D8D8DE", paraSpaceAfter: 8 });
txt(s, "Vaani Khata: private, instant voice bookkeeping, powered by the Snapdragon NPU.", { x: 0.5, y: 4.75, w: 9, h: 0.5, fontFace: H, fontSize: 16, bold: true, color: ACC });

pres.writeFile({ fileName: path.join(ROOT, "docs", "VaaniKhata_Pitch.pptx") }).then(f => console.log("wrote", f));
