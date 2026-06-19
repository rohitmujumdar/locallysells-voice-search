const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
pres.author = "Rohit Mujumdar";
pres.title = "LocallySells Voice Search";

const W = 13.3, H = 7.5;
const C = {
  bg: "0D1117", bg2: "090D13", card: "161B22", card2: "1C2330", border: "2A3140",
  text: "E6EDF3", muted: "8B949E", faint: "5B636E",
  teal: "2DD4BF", blue: "6EA8FF", purple: "A78BFA", orange: "F0A500", green: "3FB950",
};
const HF = "Trebuchet MS", BF = "Calibri";
const shadow = () => ({ type: "outer", color: "000000", blur: 9, offset: 3, angle: 135, opacity: 0.35 });

function bg(slide, color) { slide.background = { color: color || C.bg }; }

function card(slide, x, y, w, h, fill) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, fill: { color: fill || C.card },
    line: { color: C.border, width: 1 }, rectRadius: 0.09, shadow: shadow(),
  });
}
function dot(slide, x, y, color, d) {
  d = d || 0.18;
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color } });
}
function kicker(slide, text, color) {
  slide.addText(text.toUpperCase(), {
    x: 0.7, y: 0.55, w: 11, h: 0.4, fontFace: HF, fontSize: 13, bold: true,
    color: color || C.teal, charSpacing: 3, align: "left", margin: 0,
  });
}
function title(slide, text) {
  slide.addText(text, {
    x: 0.7, y: 0.92, w: 12, h: 0.95, fontFace: HF, fontSize: 34, bold: true,
    color: C.text, align: "left", margin: 0,
  });
}
function footer(slide, n) {
  slide.addText([
    { text: "LocallySells Voice Search", options: { color: C.faint } },
    { text: "     Vapi · Nebius · Insforge", options: { color: C.faint } },
  ], { x: 0.7, y: 7.0, w: 9, h: 0.35, fontFace: BF, fontSize: 10, align: "left", margin: 0 });
  slide.addText(String(n), { x: 12.4, y: 7.0, w: 0.5, h: 0.35, fontFace: BF, fontSize: 10, color: C.faint, align: "right", margin: 0 });
}

// ---------- Slide 1: Title ----------
{
  const s = pres.addSlide(); bg(s, C.bg);
  // faint motif circles
  s.addShape(pres.shapes.OVAL, { x: 10.6, y: -1.6, w: 5.2, h: 5.2, fill: { color: C.teal, transparency: 92 }, line: { color: C.teal, width: 1, transparency: 80 } });
  s.addShape(pres.shapes.OVAL, { x: 11.8, y: 4.2, w: 3.6, h: 3.6, fill: { color: C.purple, transparency: 93 } });

  s.addText("LOCALLYSELLS", { x: 0.8, y: 1.55, w: 11, h: 0.5, fontFace: HF, fontSize: 16, bold: true, color: C.teal, charSpacing: 5, margin: 0 });
  s.addText("Voice Search", { x: 0.75, y: 2.0, w: 11.5, h: 1.5, fontFace: HF, fontSize: 64, bold: true, color: C.text, margin: 0 });
  s.addText("Talk to it like a person. It finds real products by meaning, quotes prices, and takes the order, hands-free.",
    { x: 0.8, y: 3.55, w: 8.7, h: 1.0, fontFace: BF, fontSize: 19, color: C.muted, margin: 0 });

  // sponsor trifecta chips
  const chips = [["Vapi", "voice", C.teal], ["Nebius", "brain + embeddings", C.blue], ["Insforge", "serverless tools", C.purple]];
  chips.forEach((c, i) => {
    const x = 0.8 + i * 3.0;
    card(s, x, 4.95, 2.75, 0.95, C.card);
    dot(s, x + 0.22, 5.18, c[2], 0.22);
    s.addText(c[0], { x: x + 0.55, y: 5.08, w: 2.1, h: 0.35, fontFace: HF, fontSize: 16, bold: true, color: C.text, margin: 0 });
    s.addText(c[1], { x: x + 0.55, y: 5.43, w: 2.1, h: 0.3, fontFace: BF, fontSize: 11, color: C.muted, margin: 0 });
  });

  s.addText([
    { text: "Call it live:  ", options: { color: C.muted } },
    { text: "+1 (458) 273-9589", options: { color: C.green, bold: true } },
  ], { x: 0.8, y: 6.45, w: 11, h: 0.5, fontFace: HF, fontSize: 20, margin: 0 });
}

// ---------- Slide 2: Problem ----------
{
  const s = pres.addSlide(); bg(s, C.bg);
  kicker(s, "The problem", C.orange);
  title(s, "Finding the right product is the friction");
  // big stat left
  card(s, 0.7, 2.3, 5.3, 3.9, C.card);
  s.addText("1,100", { x: 0.9, y: 2.7, w: 4.9, h: 1.4, fontFace: HF, fontSize: 80, bold: true, color: C.orange, margin: 0 });
  s.addText("products in the catalog, browsed one category tap at a time.", { x: 0.95, y: 4.2, w: 4.8, h: 1.0, fontFace: BF, fontSize: 17, color: C.muted, margin: 0 });
  s.addText("LocallySells is an Uber Eats for licensed smoke shops.", { x: 0.95, y: 5.45, w: 4.8, h: 0.7, fontFace: BF, fontSize: 13, italic: true, color: C.faint, margin: 0 });

  // right: points
  const pts = [
    ["People don't think in SKUs", "They think \"something smooth and light\" or \"those minty pouches,\" not exact brand names."],
    ["Tapping through menus is slow", "Especially on a phone, especially for a long tail of 1,100 items."],
    ["The clerk experience is missing", "No one to just ask. Customers give up before finding what they want."],
  ];
  pts.forEach((p, i) => {
    const y = 2.3 + i * 1.34;
    card(s, 6.25, y, 6.35, 1.18, C.card);
    dot(s, 6.5, y + 0.27, C.orange, 0.62);
    s.addText(String(i + 1), { x: 6.5, y: y + 0.27, w: 0.62, h: 0.62, fontFace: HF, fontSize: 22, bold: true, color: C.bg, align: "center", valign: "middle", margin: 0 });
    s.addText(p[0], { x: 7.4, y: y + 0.18, w: 5.0, h: 0.4, fontFace: HF, fontSize: 17, bold: true, color: C.text, margin: 0 });
    s.addText(p[1], { x: 7.4, y: y + 0.58, w: 5.05, h: 0.5, fontFace: BF, fontSize: 12.5, color: C.muted, margin: 0 });
  });
  footer(s, 2);
}

// ---------- Slide 3: What we built ----------
{
  const s = pres.addSlide(); bg(s, C.bg);
  kicker(s, "The idea", C.teal);
  title(s, "A voice agent you just talk to");
  const cards = [
    ["Conversational search", C.teal, "Ask naturally. It finds products by meaning, not just brand keywords, and quotes real prices."],
    ["Voice ordering", C.purple, "\"Two packs of Marlboro Red to 123 Main St.\" It confirms, gives an order number and ETA."],
    ["Safe by design", C.green, "Refuses callers under 21, never invents products or prices, declines medical advice."],
  ];
  cards.forEach((c, i) => {
    const x = 0.7 + i * 4.1;
    card(s, x, 2.5, 3.8, 3.6, C.card);
    dot(s, x + 0.35, 2.9, c[1], 0.5);
    s.addText(c[0], { x: x + 0.35, y: 3.65, w: 3.2, h: 0.7, fontFace: HF, fontSize: 21, bold: true, color: C.text, margin: 0 });
    s.addText(c[2], { x: x + 0.35, y: 4.45, w: 3.2, h: 1.5, fontFace: BF, fontSize: 14.5, color: C.muted, margin: 0 });
  });
  footer(s, 3);
}

// ---------- Slide 4: Architecture ----------
{
  const s = pres.addSlide(); bg(s, C.bg);
  kicker(s, "How it works", C.blue);
  title(s, "Three platforms, one conversation");

  // flow row of 4 nodes
  const nodes = [
    ["Caller", C.text, "speaks & listens"],
    ["Vapi", C.teal, "speech in/out,\nthe live call loop"],
    ["Nebius brain", C.blue, "Qwen3-30B decides\nwhat to do"],
    ["Insforge function", C.purple, "search + order tools,\non a serverless edge"],
  ];
  const nx = 0.7, nw = 2.75, gap = 0.42, ny = 2.65, nh = 1.95;
  nodes.forEach((n, i) => {
    const x = nx + i * (nw + gap);
    card(s, x, ny, nw, nh, C.card);
    dot(s, x + 0.25, ny + 0.28, n[1], 0.22);
    s.addText(n[0], { x: x + 0.55, y: ny + 0.2, w: nw - 0.7, h: 0.4, fontFace: HF, fontSize: 16, bold: true, color: n[1] === C.text ? C.text : n[1], margin: 0 });
    s.addText(n[2], { x: x + 0.25, y: ny + 0.75, w: nw - 0.5, h: 1.0, fontFace: BF, fontSize: 12.5, color: C.muted, margin: 0 });
    if (i < nodes.length - 1) {
      s.addShape(pres.shapes.LINE, { x: x + nw + 0.05, y: ny + nh / 2, w: gap - 0.1, h: 0, line: { color: C.faint, width: 1.5, endArrowType: "triangle" } });
    }
  });
  // return path note
  s.addShape(pres.shapes.LINE, { x: nx + 0.4, y: ny + nh + 0.45, w: 10.5, h: 0, line: { color: C.teal, width: 1.5, dashType: "dash", beginArrowType: "triangle" } });
  s.addText("spoken answer with real prices, back to the caller", { x: nx + 0.4, y: ny + nh + 0.55, w: 10.5, h: 0.4, fontFace: BF, fontSize: 12.5, italic: true, color: C.teal, margin: 0 });

  // bottom strip: data + embeddings under Insforge
  card(s, 6.92, 5.95, 5.68, 1.0, C.card2);
  s.addText([
    { text: "Inside Insforge:  ", options: { color: C.muted } },
    { text: "198-product catalog + vectors", options: { color: C.orange, bold: true } },
    { text: "   +   ", options: { color: C.faint } },
    { text: "Nebius embeddings for semantic match", options: { color: C.blue, bold: true } },
  ], { x: 7.15, y: 6.2, w: 5.3, h: 0.55, fontFace: BF, fontSize: 12.5, margin: 0, valign: "middle" });
  s.addText("The caller hears one smooth conversation. The agent never touches the rest of the LocallySells platform.", { x: 0.7, y: 6.25, w: 6.0, h: 0.7, fontFace: BF, fontSize: 12.5, color: C.muted, margin: 0 });
  footer(s, 4);
}

// ---------- Slide 5: Semantic search (standout) ----------
{
  const s = pres.addSlide(); bg(s, C.bg);
  kicker(s, "The standout feature", C.blue);
  title(s, "Search that understands intent");
  s.addText("Every product is embedded with Nebius. Each query is matched by meaning, not keywords. Exact brands still win via a keyword hybrid.",
    { x: 0.7, y: 1.85, w: 11.8, h: 0.6, fontFace: BF, fontSize: 15, color: C.muted, margin: 0 });

  const rows = [
    ["\"a smooth, light cigarette\"", "Marlboro Lights, Marlboro Gold"],
    ["\"an easy starter vape for a beginner\"", "SMOK Novo Starter Kit"],
    ["\"those little white minty pouches\"", "ZYN Cool Mint, $5.49"],
    ["\"Marlboro Reds\"  (exact brand)", "Marlboro Red King Size, $8.99"],
  ];
  const ry = 2.75, rh = 0.95, rgap = 0.18;
  // headers
  s.addText("YOU SAY", { x: 0.95, y: ry - 0.45, w: 5, h: 0.35, fontFace: HF, fontSize: 12, bold: true, color: C.faint, charSpacing: 2, margin: 0 });
  s.addText("IT FINDS", { x: 7.15, y: ry - 0.45, w: 5, h: 0.35, fontFace: HF, fontSize: 12, bold: true, color: C.faint, charSpacing: 2, margin: 0 });
  rows.forEach((r, i) => {
    const y = ry + i * (rh + rgap);
    card(s, 0.7, y, 5.9, rh, C.card);
    s.addText(r[0], { x: 1.0, y, w: 5.4, h: rh, fontFace: BF, fontSize: 15.5, italic: true, color: C.text, valign: "middle", margin: 0 });
    // arrow
    s.addShape(pres.shapes.LINE, { x: 6.68, y: y + rh / 2, w: 0.34, h: 0, line: { color: C.blue, width: 2, endArrowType: "triangle" } });
    card(s, 7.1, y, 5.5, rh, C.card2);
    dot(s, 7.32, y + rh / 2 - 0.08, C.blue, 0.16);
    s.addText(r[1], { x: 7.6, y, w: 4.9, h: rh, fontFace: HF, fontSize: 15.5, bold: true, color: C.text, valign: "middle", margin: 0 });
  });
  footer(s, 5);
}

// ---------- Slide 6: Voice ordering ----------
{
  const s = pres.addSlide(); bg(s, C.bg);
  kicker(s, "Second capability", C.purple);
  title(s, "Voice ordering, end to end");
  const steps = [
    ["Ask", "\"I'll take two packs of Marlboro Red.\""],
    ["Confirm", "Agent confirms the items and the price."],
    ["Address", "Caller gives a delivery address out loud."],
    ["Done", "Order number, ETA, and a 21+ ID reminder."],
  ];
  const sx = 0.7, sw = 2.75, gap = 0.42, sy = 2.6, sh = 2.1;
  steps.forEach((st, i) => {
    const x = sx + i * (sw + gap);
    card(s, x, sy, sw, sh, C.card);
    dot(s, x + 0.3, sy + 0.32, C.purple, 0.6);
    s.addText(String(i + 1), { x: x + 0.3, y: sy + 0.32, w: 0.6, h: 0.6, fontFace: HF, fontSize: 22, bold: true, color: C.bg, align: "center", valign: "middle", margin: 0 });
    s.addText(st[0], { x: x + 0.3, y: sy + 1.05, w: sw - 0.5, h: 0.45, fontFace: HF, fontSize: 18, bold: true, color: C.text, margin: 0 });
    s.addText(st[1], { x: x + 0.3, y: sy + 1.5, w: sw - 0.55, h: 0.55, fontFace: BF, fontSize: 12.5, color: C.muted, margin: 0 });
    if (i < steps.length - 1) s.addShape(pres.shapes.LINE, { x: x + sw + 0.05, y: sy + sh / 2, w: gap - 0.1, h: 0, line: { color: C.faint, width: 1.5, endArrowType: "triangle" } });
  });
  card(s, 0.7, 5.25, 11.9, 1.0, C.card2);
  s.addText([
    { text: "Working today, mocked fulfillment.  ", options: { color: C.green, bold: true } },
    { text: "The order number and ETA are real to the caller. Payment and delivery dispatch are the next step, not a research problem.", options: { color: C.muted } },
  ], { x: 1.0, y: 5.25, w: 11.4, h: 1.0, fontFace: BF, fontSize: 14, valign: "middle", margin: 0 });
  footer(s, 6);
}

// ---------- Slide 7: Evals ----------
{
  const s = pres.addSlide(); bg(s, C.bg);
  kicker(s, "Quality", C.green);
  title(s, "Tested with evals, not vibes");
  // big stat
  card(s, 0.7, 2.45, 4.0, 3.7, C.card);
  s.addText("6 / 6", { x: 0.85, y: 3.0, w: 3.7, h: 1.4, fontFace: HF, fontSize: 76, bold: true, color: C.green, align: "center", margin: 0 });
  s.addText("core eval suite passing", { x: 0.85, y: 4.35, w: 3.7, h: 0.5, fontFace: HF, fontSize: 16, bold: true, color: C.text, align: "center", margin: 0 });
  s.addText("search, ordering, 21+ refusal, no hallucination, order guardrail", { x: 0.95, y: 4.85, w: 3.5, h: 1.0, fontFace: BF, fontSize: 12.5, color: C.muted, align: "center", margin: 0 });

  const pts = [
    ["Simulated callers, AI-graded", "A test caller talks to the agent; an AI grader scores the transcript against a rubric. Two suites: core flows and rambling conversational personas."],
    ["The evals caught a real bug", "They found a silent-agent failure before any live demo: the 70B brain was timing out. We switched to the faster Qwen3-30B, plus search and order fixes."],
    ["Quality from measurement", "Every change re-runs the suites. The conversational personas confirmed natural-language search resolves vague intent to real products."],
  ];
  pts.forEach((p, i) => {
    const y = 2.45 + i * 1.27;
    card(s, 4.95, y, 7.65, 1.12, C.card);
    dot(s, 5.2, y + 0.45, C.green, 0.2);
    s.addText(p[0], { x: 5.55, y: y + 0.16, w: 6.9, h: 0.4, fontFace: HF, fontSize: 16, bold: true, color: C.text, margin: 0 });
    s.addText(p[1], { x: 5.55, y: y + 0.54, w: 6.95, h: 0.5, fontFace: BF, fontSize: 12, color: C.muted, margin: 0 });
  });
  footer(s, 7);
}

// ---------- Slide 8: Real calls ----------
{
  const s = pres.addSlide(); bg(s, C.bg);
  kicker(s, "Proof", C.teal);
  title(s, "Real calls, on a live number");
  // left stat callouts
  const stats = [["+1 (458) 273-9589", "live inbound number"], ["$0.02–0.31", "cost per call"], ["Success: true", "Vapi call analysis"]];
  stats.forEach((st, i) => {
    const y = 2.5 + i * 1.25;
    card(s, 0.7, y, 4.4, 1.08, C.card);
    s.addText(st[0], { x: 0.95, y: y + 0.14, w: 4.0, h: 0.5, fontFace: HF, fontSize: 22, bold: true, color: C.teal, margin: 0 });
    s.addText(st[1], { x: 0.97, y: y + 0.64, w: 4.0, h: 0.35, fontFace: BF, fontSize: 12.5, color: C.muted, margin: 0 });
  });
  // right: mini call log
  card(s, 5.4, 2.5, 7.2, 3.83, C.card);
  s.addText("Vapi  ›  Logs  ›  Calls", { x: 5.65, y: 2.65, w: 6.7, h: 0.35, fontFace: BF, fontSize: 12, color: C.faint, margin: 0 });
  const log = [
    ["Type", "Duration", "Ended", "Cost"],
    ["Inbound", "3m 39s", "Customer", "$0.31"],
    ["Inbound", "1m 44s", "Customer", "$0.16"],
    ["Inbound", "51s", "Customer", "$0.07"],
    ["Inbound", "17s", "Customer", "$0.03"],
  ];
  const rowY = 3.15, rowH = 0.62, colX = [5.65, 7.7, 9.5, 11.6];
  log.forEach((r, ri) => {
    const y = rowY + ri * rowH;
    if (ri > 0) s.addShape(pres.shapes.LINE, { x: 5.65, y: y - 0.04, w: 6.7, h: 0, line: { color: C.border, width: 0.75 } });
    r.forEach((cell, ci) => {
      const isH = ri === 0;
      s.addText(cell, { x: colX[ci], y, w: 1.9, h: rowH, fontFace: isH ? HF : BF, fontSize: isH ? 11.5 : 13.5, bold: isH, color: isH ? C.faint : (ci === 0 ? C.teal : C.text), valign: "middle", margin: 0 });
    });
  });
  s.addText("Inbound phone calls placed to the live assistant during testing. Costs are real, fractions of a cent per second.",
    { x: 0.7, y: 6.45, w: 11.9, h: 0.5, fontFace: BF, fontSize: 12.5, italic: true, color: C.muted, margin: 0 });
  footer(s, 8);
}

// ---------- Slide 9: Close ----------
{
  const s = pres.addSlide(); bg(s, C.bg);
  s.addShape(pres.shapes.OVAL, { x: -1.7, y: 4.0, w: 5.2, h: 5.2, fill: { color: C.teal, transparency: 93 } });
  s.addShape(pres.shapes.OVAL, { x: 11.2, y: -1.5, w: 4.4, h: 4.4, fill: { color: C.purple, transparency: 92 } });
  s.addText("Try it yourself", { x: 0.8, y: 1.7, w: 11, h: 1.0, fontFace: HF, fontSize: 46, bold: true, color: C.text, margin: 0 });
  s.addText("Call and ask for \"something smooth and light\" or \"an easy vape to start with.\"", { x: 0.82, y: 2.85, w: 10, h: 0.6, fontFace: BF, fontSize: 18, color: C.muted, margin: 0 });

  card(s, 0.8, 3.75, 6.0, 1.2, C.card);
  s.addText([{ text: "Call  ", options: { color: C.muted } }, { text: "+1 (458) 273-9589", options: { color: C.green, bold: true } }], { x: 1.1, y: 3.75, w: 5.5, h: 1.2, fontFace: HF, fontSize: 26, valign: "middle", margin: 0 });
  card(s, 7.0, 3.75, 5.5, 1.2, C.card);
  s.addText("github.com/rohitmujumdar/", { x: 7.3, y: 3.95, w: 5.0, h: 0.45, fontFace: BF, fontSize: 16, color: C.text, margin: 0 });
  s.addText("locallysells-voice-search", { x: 7.3, y: 4.35, w: 5.0, h: 0.45, fontFace: HF, fontSize: 17, bold: true, color: C.teal, margin: 0 });

  // trifecta
  const chips = [["Vapi", "voice", C.teal], ["Nebius", "brain + embeddings", C.blue], ["Insforge", "serverless tools", C.purple]];
  chips.forEach((c, i) => {
    const x = 0.8 + i * 3.0;
    card(s, x, 5.35, 2.75, 0.95, C.card);
    dot(s, x + 0.22, 5.58, c[2], 0.22);
    s.addText(c[0], { x: x + 0.55, y: 5.48, w: 2.1, h: 0.35, fontFace: HF, fontSize: 16, bold: true, color: C.text, margin: 0 });
    s.addText(c[1], { x: x + 0.55, y: 5.83, w: 2.1, h: 0.3, fontFace: BF, fontSize: 11, color: C.muted, margin: 0 });
  });
  s.addText("Built for the Multimodal Midsummer Hackathon", { x: 0.8, y: 6.75, w: 11, h: 0.4, fontFace: BF, fontSize: 13, italic: true, color: C.faint, margin: 0 });
}

pres.writeFile({ fileName: "../LocallySells_Voice_Search.pptx" }).then((f) => console.log("wrote", f));
