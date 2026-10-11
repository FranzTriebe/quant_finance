---
name: model-docs
description: Use when Franz asks to document a quant model, indicator, screener or methodology in LaTeX, either as a full methodology document or as a 1 to 2 page model brief, or to bring an existing model write-up into the house format.
---

# Model documentation in LaTeX

Two document types share one style file (`modeldoc.sty`, below) so every model write-up looks the same:

| Type | Length | Reader | Question it answers |
|---|---|---|---|
| **Methodology** (full) | 5 to 15 pages | Validator, successor, developer | Can I reproduce and challenge every number? |
| **Model brief** | 1 to 2 pages, hard limit | PM, IC member, colleague | What does it decide, how do I read it, when should I not trust it? |

If Franz does not say which, ask once. If he is away, write the brief when the source is short or high level and the methodology when there is code or a detailed spec. When both are wanted, write the methodology first and derive the brief from it, never the other way round.

Reference documents this was built from: colleague write-ups *Systematic Corporate Bond Screener* (Fluri, May 2026) and *FX Indicator and Currency-Hedging Methodology* (July 2026). Content structure follows SR 11-7, PRA SS1/23, the ECB Guide to Internal Models, S&P DJI and MSCI index methodologies, Model Cards (Mitchell et al. 2019) and Knuth's *Mathematical Writing*, scaled down for internal investment-office models.

## Workflow

1. **Collect facts before writing.** Read the code, config, notebooks and any notes. List every formula, parameter, data identifier and threshold actually implemented. Ask for what is missing only if it changes the structure; otherwise insert `\tbd{...}`.
2. **Never invent.** No guessed tickers, owners, repo paths, backtest numbers or validation claims. Missing facts become `\tbd{...}` and are listed for Franz at the end.
3. **Separate implemented from proposed.** The body describes what the code does today, in the present tense. Ideas, recommended extensions and "should" statements go only in a section called *Extensions (not implemented)*. The bond screener reference mixes the two; do not copy that.
4. **Write `modeldoc.sty`** (block below) next to the `.tex` file, then fill the matching skeleton.
5. **Prose pass.** Reread every paragraph, caption and table cell against *Prose style* below and rewrite what fails. Then search the `.tex` once more for the tells that survive a first rewrite: contrasts, closers, triads, dashes, the banned words.
6. **Compile** with `latexmk -pdf -interaction=nonstopmode -halt-on-error file.tex`. Fix every error and every `Overfull \hbox`.
7. **Render and look.** `pdftoppm -r 70 -png file.pdf pg` and view each page. Check the checklist at the end. For the brief, confirm `pdfinfo` shows at most 2 pages.
8. **Deliver** the PDF and the `.tex` + `.sty`, plus a short list of every `\tbd`.

## Full methodology: section structure

Keep this order and these titles. Drop a section only if it truly does not apply, never renumber to hide a gap. Sections 9 and 10 can be one short table each for low-materiality internal tools.

0. **Title block** (`\mdtitle` + `mdmeta`): pairs or universe, output field, version and date, status (implemented / unit-tested / validated), owner, code location.
   **Summary box** (`keybox`): Question, Approach, Use. Three short paragraphs, readable on their own.
1. **Purpose and intended use**: the single decision supported, users, frequency, and an explicit *Out of scope* row. Say what the output is *not* (forecast, probability, recommendation).
2. **Conventions and notation**: quoting convention, sign convention ("positive always means ..."), units, indices ($i$ bond, $j$ issuer, $t$ date), and a captioned notation table.
3. **Data**: captioned table with input, exact identifier (Bloomberg ticker and field), unit, frequency, which component uses it. Then run-in paragraphs *Missing data*, *Calculation date*, *Not handled* (vintages, lags, stale data).
4. **Methodology**: optional overview diagram, then one subsection per component, each in the same pattern:
   bold economic question; raw quantity equation; symbol definitions in a "where" sentence; scaled signal equation; one line mapping extremes to outcomes; what the component does *not* do.
5. **Aggregation and output**: combination formula, mapping from score to decision, final output field, and a small table of outputs at the extremes and at neutral.
6. **Parameters**: one table with symbol, value, meaning, basis (estimated / calibrated / judgement / policy). Note bounds that can never bind.
7. **Worked examples**: a table with extreme, neutral and one real saved output, every intermediate value shown, plus a sentence on any counter-intuitive case (rounding, caps).
8. **Testing and validation**: three rows, *Tested*, *Not tested*, *Not implemented*. Then one bold sentence stating honestly what the evidence supports. Mention look-ahead and timing assumptions.
9. **Limitations and mitigants**: two-column table, each limitation paired with a concrete mitigant or usage rule. No generic disclaimers.
10. **Implementation and operation**: repository and commit, entry point, configuration, output fields, fallback.
11. **Extensions (not implemented)**: only if there are proposals.
- **Appendix A Compact specification**: all equations in one `align*` block, no prose.
- **Appendix B Change log**: version, date, change, reason.
- **References**: only if literature is cited. Numbered, with URL.

Add `\tableofcontents` only above 8 pages.

## Model brief: section structure

Same title block, then exactly these sections. Every sentence must help someone *use* the model correctly, in plain language (see *Prose style*).

- **Decision question** (`keybox`): one question, one sentence on what the model does not decide.
- **1 Intuition**: bold lead sentence, then 3 to 5 sentences without formulas: what makes the model hedge more / buy / rank higher, and what makes it do the opposite. One small TikZ flow diagram (inputs, weights, score, decision) if there are several components.
- **2 Inputs**: table with input, identifier, used for.
- **3 How the score is built**: the combination in words (what counts how much), optionally one displayed equation followed by the same statement in words.
- **4 How to read the output**: table mapping score levels (low, neutral, high) to the action, and the one fact a user most likely gets wrong (e.g. neutral is not the floor).
- **5 Worked example**: one recent real output walked through in 2 to 3 lines, ending with "In words: ...".
- **6 Limitations**: 4 to 6 bullets, the ones that would change a decision.

Footer of the title block points to the full methodology. No references, no change log, no appendix.

## Writing rules

1. **British English** by default; German only if asked. Present tense for what the model does.
2. **No dashes as punctuation** (no em or en dashes, no " - ", no `--` in prose or tables). Use a full stop, comma, colon or brackets. Ranges are written "25\% to 35\%". Prefer the open form of compounds where it reads fine (*out of sample*, *per pair*, *risk free rate*); keep the hyphen only where dropping it makes a numeric or technical modifier ambiguous (*one-month rate*, *63-observation window*).
3. **Bold first sentence** only on paragraphs that carry a key point, and the bold sentence must be a claim with content ("The final hedge never falls below the floor."), not a label or a teaser. At most one or two per section.
4. **Short sentences.** One idea per sentence. One line per source sentence in the `.tex` for clean diffs.
5. **Every symbol is defined** in a "where ..." sentence right after the equation where it first appears, and in the notation table. Never reuse a symbol for two things. Never start a sentence with a symbol.
6. **Number important equations** and refer to them with `\Cref{eq:...}`. Unnumbered `equation*` only in the brief.
7. **State sign conventions and units explicitly**: decimal vs. percent, % vs. pp vs. bp, simple vs. log returns, quote direction.
8. **Show what is not in the model**: a "What X is not" line per component and an *Out of scope* row.
9. **Cautious claims.** Say "is designed to", "tests show"; never "predicts", "outperforms" without numbers and a sample period.
10. **Numbers**: Swiss formatting, apostrophe thousands separator (`\num{12500}` gives 12'500), point decimal, ISO code before amounts (CHF 1'000). Same number of decimals within a column.
11. **Code names** (fields, functions, tags) in `\code{...}`, escape underscores (`\code{policy\_point}`).
12. **Open points** always as `\tbd{...}`, never a plausible-looking placeholder.

## Prose style: technical, plain, no AI tells

Adapted from the `natural-writing` skill (itself based on blader/humanizer and Wikipedia's *Signs of AI writing*). If that skill is available, its pattern list applies too, but **this section overrides its "Franz's voice" part**: a model document is reference text, not a letter.

**Register depends on the document type.** Both are neutral and impersonal: "we" only for a decision the team made, never "I", no enthusiasm, no persuasion, no story about how the model was built.

*Methodology: technical.* Written for a quant or validator. Precise terms (OAS, PPP gap, real carry, clipped, half-up rounding), symbols and equations. The subject of most sentences is the model or a variable ("The score is clipped to ...", "A positive gap means ..."). Each sentence states a definition, a rule, a number, a consequence or a limit.

*Brief: plain language.* Written for a portfolio manager, client adviser or IC member who will act on the output but will not read code or equations. Test: a colleague without quant training understands every sentence on first reading.
- Explain every technical term in everyday words at first use, or replace it: "PPP" becomes "long-run fair value based on price levels (PPP)", "real carry" becomes "the interest advantage after inflation", "clipped" becomes "capped".
- Internal variable names (*pressure*, `policy_point`, $p_V$) do not appear in the prose. Use what they mean.
- At most one displayed equation, and the sentence after it says the same thing in words. If the logic fits in two sentences, drop the equation.
- Describe direction with cause and action: "If the dollar looks expensive, the model hedges more."
- Numbers in the form the reader acts on (hedge ratio in %, ranks), with one concrete example.
- Still precise: plain does not mean vague. Keep the real thresholds, weights and caps.

**What a methodology sounds like**

> Valuation is the proportional gap between spot and the PPP rate. A gap of +20% or more gives full pressure towards hedging. Inside that range the signal is linear; outside it is clipped.

**What a brief sounds like**

> The model compares the dollar with its long-run fair value based on price levels. If the dollar is 20% or more above that value, this signal pushes fully towards hedging more.

**What neither may sound like**

> At its core, the valuation component isn't just a measure of mispricing; it's a powerful lens on long-term fair value, ensuring that the model remains robust across diverse market regimes.

**Tells to remove, strongest first.** One sighting of 1 to 5 justifies a rewrite.

1. **Not X but Y.** "isn't just X, it's Y", "rather than", "This does not mean X. It means Y." State the claim. *Exception that matters here:* scope statements are required in model docs ("The score is not a probability", *Out of scope* rows, "What carry is not"). Keep them only when a reader would plausibly assume the opposite, and write them as plain negative facts, without the contrasting flourish.
2. **Closers and fragments.** A last sentence that repeats the paragraph ("This makes the model robust.", "That is the key insight."), rows of fragments, "In short, ...". End on the last concrete fact.
3. **Sayings that sound deep.** "at its core", "the real question", "fundamentally", "the heart of", "X is the language of Y".
4. **Run-ups.** "Let's look at", "It is worth noting that", "Importantly,", "Note that" as an opener for routine content. Start with the content.
5. **Arguing with no one.** Rejecting alternatives nobody proposed ("One might be tempted to use a regression, but ..."). Alternatives belong in the doc only if they were actually considered; then say why they were rejected, with a reason.
6. **Forced triads.** Lists of three abstract nouns ("robustness, transparency and flexibility"). Three real components are fine.
7. **Inflated or vague words.** robust, crucial, key, powerful, comprehensive, seamless, sophisticated, leverage (verb), ensure, enhance, delve, landscape, pivotal, underscore, highlight (verb), valuable, notably, essentially, effectively, serves as, plays a role. Replace with the specific fact, or *is* / *has*. "Robust" is allowed only with a stated test ("stable when the window changes from 42 to 84 observations").
8. **-ing riders.** "..., ensuring consistency", "..., reflecting market conditions". Keep only if the claim is true and stated elsewhere; otherwise cut.
9. **Stacked hedges.** "could potentially", "may arguably". One qualifier where the evidence needs it. Cautious claims about performance are still required (see rule 9 above).
10. **Bold and headings by rule.** No bold labels on every bullet, no title case headings, no emojis or arrows as decoration.
11. **Writing about the document.** "This section describes ...", "As shown in the table above", "The following subsections explain ...". A one-line pointer to a figure or table is fine when the reader needs to go there; otherwise just state the content.
12. **Chat residue.** "Here is", "I hope", "Let me know", "Certainly". Never in a document.

**Two tests for every sentence.** Does it add something the reader did not have from the previous sentence, the equation or the table? Could a validator check it against the code or the data? If both answers are no, cut it.

**Keep it human, not bland.** Plain is not monotone: vary sentence length, give the economic reason for a design choice in one sentence where the code shows it, and flag something surprising in the model ("Two bounds for EUR/CHF can never bind.") rather than smoothing it over.

## LaTeX and layout rules

- `\documentclass[10pt,a4paper]{article}` plus `\usepackage{modeldoc}`, `\shorttitle{...}`, `\doctype{Methodology}` or `\doctype{Model brief}`.
- **Black only.** No colour anywhere: text, boxes, diagrams, plots. Distinguish plot series by line style (solid, dashed, grey, dotted), already set in the style.
- **Tables**: `booktabs` only (`\toprule`, `\midrule`, `\bottomrule`), no vertical lines, text columns `L` (ragged right X), numbers centred or right. Captions above tables, below figures. Use `table`/`figure` floats with `[htbp]`, `\caption` and `\label` when the object is referenced; plain `tabularx` for small inline key/value tables.
- Tables never squeeze text into narrow columns that hyphenate words; widen with `P{..}` or split the table.
- **Diagrams** with TikZ styles `box` and `arr`. Use explicit `\\` line breaks in boxes; never let box text hyphenate.
- **Plots** with `pgfplots` and real data from the model, or skip the plot.
- **Keep equation and its "where" sentence together**: put `\needspace{8\baselineskip}` *before* the heading or paragraph if a page break would split them.
- `\Cref` for all cross references (gives "Table 3", "Equation (4.2)").
- Section-numbered equations are automatic. Run-in sub-points use `\subsubsection{Missing data}` (rendered bold, inline).
- The title block never sits on its own page.

## Pre-delivery checklist

- [ ] Compiles without errors, no overfull boxes, no `??` references
- [ ] Brief is at most 2 pages
- [ ] Every equation symbol defined; notation table matches the text
- [ ] Every parameter in the parameter table and identical to the code
- [ ] Worked examples recomputed (run the arithmetic in Python, do not trust mental maths)
- [ ] Sign convention stated and consistent in text, table and examples
- [ ] Implemented vs. not implemented clearly separated
- [ ] Tested / not tested stated honestly, no unsupported performance claim
- [ ] No colour, no dashes as punctuation, Swiss number format, British spelling
- [ ] Prose pass done: no contrasts, closers, run-ups or banned words; every bold sentence is a claim
- [ ] All `\tbd` items listed in the reply

## `modeldoc.sty`

Write this file verbatim next to the document.

```latex
% modeldoc.sty : shared style for model and methodology documentation
% Black only, A4, Latin Modern, numbered sections, booktabs tables.
\NeedsTeXFormat{LaTeX2e}
\ProvidesPackage{modeldoc}[2026/10/06 v1.0 Model documentation style]

% ---------- Fonts and encoding ----------
% Latin Modern with T1 if installed (standard TeX Live, MiKTeX);
% otherwise Computer Modern in OT1 so fonts stay scalable.
\IfFileExists{lmodern.sty}{\RequirePackage[T1]{fontenc}\RequirePackage{lmodern}}{}
\RequirePackage[utf8]{inputenc}
\RequirePackage[british]{babel}
\RequirePackage{microtype}

% ---------- Page ----------
\RequirePackage[a4paper,left=2.5cm,right=2.5cm,top=2.7cm,bottom=2.5cm,headsep=0.8cm]{geometry}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.55em}
\linespread{1.05}
\clubpenalty=10000
\widowpenalty=10000

% ---------- Maths ----------
\RequirePackage{amsmath,amssymb,mathtools,bm}
\numberwithin{equation}{section}
\DeclareMathOperator{\clip}{clip}
\DeclareMathOperator*{\argmin}{arg\,min}
\DeclareMathOperator*{\argmax}{arg\,max}

% ---------- Numbers: Swiss style ----------
\RequirePackage{siunitx}
\sisetup{group-separator={'},group-minimum-digits=4,output-decimal-marker={.},
         detect-all,range-phrase={ to },list-final-separator={ and }}

% ---------- Tables ----------
\RequirePackage{booktabs,tabularx,array}
\newcolumntype{L}{>{\raggedright\arraybackslash}X}
\newcolumntype{P}[1]{>{\raggedright\arraybackslash}p{#1}}
\renewcommand{\arraystretch}{1.2}
\setlength{\tabcolsep}{5pt}

\RequirePackage{needspace}   % \needspace{6\baselineskip} keeps an equation with its "where" lines

% ---------- Lists ----------
\RequirePackage{enumitem}
\setlist{itemsep=0.15em,topsep=0.2em,parsep=0pt,leftmargin=1.4em}

% ---------- Colour: black only ----------
\RequirePackage{xcolor}
\RequirePackage{tikz}
\usetikzlibrary{arrows.meta,positioning,calc}
\tikzset{
  box/.style={draw=black,line width=0.5pt,rounded corners=1pt,align=center,
              font=\small,inner sep=4pt,minimum height=8mm,
              execute at begin node={\hyphenpenalty=10000}},
  arr/.style={-{Latex[length=2mm]},line width=0.5pt}}
\RequirePackage{pgfplots}
\pgfplotsset{compat=1.18,
  every axis/.append style={font=\small,axis line style={line width=0.5pt},
    tick style={black},grid style={dashed,black!35},legend style={draw=none,fill=none}},
  cycle list={{black,line width=1pt},{black,dashed,line width=1pt},
              {black!55,line width=1pt},{black,dotted,line width=1.2pt}}}

% ---------- Captions ----------
\RequirePackage[font=small,labelfont=bf,labelsep=period,skip=4pt]{caption}
\captionsetup[table]{position=top}

% ---------- Section headings ----------
\RequirePackage{titlesec}
\titleformat{\section}{\large\bfseries}{\thesection}{0.8em}{}
\titleformat{\subsection}{\normalsize\bfseries}{\thesubsection}{0.8em}{}
\titleformat{\subsubsection}[runin]{\normalsize\bfseries}{}{0pt}{}[.]
\titlespacing*{\section}{0pt}{1.4em}{0.5em}
\titlespacing*{\subsection}{0pt}{1.0em}{0.3em}
\titlespacing*{\subsubsection}{0pt}{0.6em}{0.6em}

% ---------- Header and footer ----------
\RequirePackage{fancyhdr,lastpage}
\newcommand{\@mdshort}{}
\newcommand{\@mdtype}{}
\newcommand{\shorttitle}[1]{\renewcommand{\@mdshort}{#1}}
\newcommand{\doctype}[1]{\renewcommand{\@mdtype}{#1}}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\@mdshort}
\fancyhead[R]{\small\@mdtype}
\fancyfoot[R]{\small \thepage\ / \pageref{LastPage}}
\renewcommand{\headrulewidth}{0.4pt}
\fancypagestyle{plain}{\fancyhf{}\renewcommand{\headrulewidth}{0pt}
  \fancyfoot[R]{\small \thepage\ / \pageref{LastPage}}}

% ---------- Boxes ----------
\RequirePackage[skins,breakable]{tcolorbox}
\newtcolorbox{keybox}[1][]{enhanced,colback=white,colframe=black,boxrule=0.5pt,
  arc=0pt,left=6pt,right=6pt,top=4pt,bottom=4pt,fonttitle=\bfseries\small,
  coltitle=black,colbacktitle=white,titlerule=0.4pt,toptitle=2pt,bottomtitle=2pt,
  before skip=0.8em,after skip=0.8em,#1}

% ---------- Title block ----------
% \mdtitle{Title}{Subtitle}
% \begin{mdmeta} Key & Value \\ ... \end{mdmeta}
\newcommand{\mdtitle}[2]{%
  \thispagestyle{plain}%
  {\noindent\rule{\linewidth}{0.8pt}\par\vspace{0.6em}}%
  {\noindent\LARGE\bfseries #1\par}%
  \ifx\relax#2\relax\else{\vspace{0.3em}\noindent\large #2\par}\fi
  \vspace{0.6em}}
\newenvironment{mdmeta}
  {\noindent\small\begin{tabular}{@{}p{3.1cm}@{}p{\dimexpr\linewidth-3.1cm\relax}@{}}}
  {\end{tabular}\par\vspace{0.4em}{\noindent\rule{\linewidth}{0.4pt}\par}\vspace{0.6em}}

% ---------- Semantic helpers ----------
\newcommand{\lead}[1]{\textbf{#1}\ }              % run-in lead: \lead{Purpose.}
\newcommand{\code}[1]{\texttt{\small #1}}          % code names, fields, tickers
\newcommand{\tbd}[1]{\textbf{[TBD: #1]}}           % open point, never silently filled
\newcommand{\pp}{\ensuremath{\,\text{pp}}}         % percentage points, upright in text and maths
\newcommand{\bp}{\ensuremath{\,\text{bp}}}         % basis points

\setcounter{tocdepth}{1}

% ---------- Links ----------
\RequirePackage[hidelinks]{hyperref}
\RequirePackage[nameinlink,noabbrev,capitalise]{cleveref}

\endinput
```

## Skeleton: full methodology

```latex
\documentclass[10pt,a4paper]{article}
\usepackage{modeldoc}
\shorttitle{<Model name>}
\doctype{Methodology}

\begin{document}

\mdtitle{<Model name>}{<One line: what it decides, with which signals>}
\begin{mdmeta}
Universe    & <assets, pairs, issuers> \\
Output      & <output and field name, e.g. \code{policy\_point}> \\
Version     & <x.y, Month YYYY> \\
Status      & <Implemented / unit-tested / validated out of sample> \\
Owner       & \tbd{owner} \\
Code        & \tbd{repository and entry point} \\
\end{mdmeta}

\begin{keybox}[title=Summary]
\lead{Question.} <The single decision question.>

\lead{Approach.} <Signals, how combined, how mapped to the decision. Two or three sentences.>

\lead{Use.} <What it is an input to, and what it is not.>
\end{keybox}

\section{Purpose and intended use}\label{sec:purpose}
\textbf{<Lead sentence: the decision it supports.>} <Context.>

\begin{tabularx}{\linewidth}{@{}P{3.2cm}L@{}}
\toprule
Users & \\
Frequency & \\
Decision supported & \\
Out of scope & \\
\bottomrule
\end{tabularx}

\section{Conventions and notation}\label{sec:conventions}
<Quote convention, sign convention, units.> \Cref{tab:notation} lists all symbols.

\begin{table}[htbp]
\caption{Notation}\label{tab:notation}
\begin{tabularx}{\linewidth}{@{}lLl@{}}
\toprule
Symbol & Meaning & Unit \\
\midrule
 &  &  \\
\bottomrule
\end{tabularx}
\end{table}

\section{Data}\label{sec:data}
\begin{table}[htbp]
\caption{Model inputs}\label{tab:data}
\begin{tabularx}{\linewidth}{@{}lLll@{}}
\toprule
Input & Identifier & Unit & Component \\
\midrule
 &  &  &  \\
\bottomrule
\end{tabularx}
\end{table}
\subsubsection{Calculation date} <...>
\subsubsection{Missing data} <...>
\subsubsection{Not handled} <vintages, publication lags, stale data>

\section{Methodology}\label{sec:method}
\subsection{<Component>}
\textbf{Economic question: <...>?}
<Raw quantity:>
\begin{equation}
 <...>
\label{eq:raw1}
\end{equation}
where <every new symbol>.
<Scaled signal:>
\begin{equation}
 <...>
\label{eq:sig1}
\end{equation}
<Extremes mapped to outcomes.> \textbf{What it is not.} <...>

\section{Aggregation and output}\label{sec:output}
\subsection{Combined score}
\subsection{Mapping to the decision}
\subsection{Final output}

\section{Parameters}\label{sec:params}
\begin{table}[htbp]
\caption{All parameters}\label{tab:params}
\begin{tabularx}{\linewidth}{@{}llLl@{}}
\toprule
Symbol & Value & Meaning & Basis \\
\midrule
 &  &  &  \\
\bottomrule
\end{tabularx}
\end{table}

\section{Worked examples}\label{sec:examples}

\section{Testing and validation}\label{sec:validation}
\begin{tabularx}{\linewidth}{@{}P{4.2cm}L@{}}
\toprule
Tested & \\
Not tested & \\
Not implemented & \\
\bottomrule
\end{tabularx}

\section{Limitations and mitigants}\label{sec:limits}
\begin{tabularx}{\linewidth}{@{}LL@{}}
\toprule
Limitation & Mitigant or usage rule \\
\midrule
 &  \\
\bottomrule
\end{tabularx}

\section{Implementation and operation}\label{sec:impl}
\begin{tabularx}{\linewidth}{@{}P{3.2cm}L@{}}
\toprule
Repository & \\
Entry point & \\
Configuration & \\
Output fields & \\
Fallback & \\
\bottomrule
\end{tabularx}

% \section{Extensions (not implemented)}  % only if there are proposals

\appendix
\section{Compact specification}
\begin{align*}
 <all equations>
\end{align*}

\section{Change log}
\begin{tabularx}{\linewidth}{@{}llL@{}}
\toprule
Version & Date & Change \\
\midrule
1.0 & <Month YYYY> & First documented version \\
\bottomrule
\end{tabularx}

\end{document}
```

## Skeleton: model brief

```latex
\documentclass[10pt,a4paper]{article}
\usepackage{modeldoc}
\shorttitle{<Model name>}
\doctype{Model brief}

\begin{document}

\mdtitle{<Model name>}{<One line in plain words>}
\begin{mdmeta}
Universe  & \\
Output    & \\
Version   & \\
Owner     & \tbd{owner} \\
Full spec & <title and date of the methodology document> \\
\end{mdmeta}

\begin{keybox}[title=Decision question]
<One question.> The model does \emph{not} <...>.
\end{keybox}

\section{Intuition}
\textbf{<Lead sentence.>} <3 to 5 sentences, no formulas.>

\begin{center}
\begin{tikzpicture}[node distance=4mm and 6mm]
  \node[box,text width=3.6cm] (a) {<Signal A>\\[-1pt]\footnotesize <raw input>\\[-2pt]\footnotesize weight <w>};
  \node[box,text width=3.6cm,below=of a] (b) {<Signal B>\\[-1pt]\footnotesize <raw input>\\[-2pt]\footnotesize weight <w>};
  \node[box,text width=1.8cm,right=10mm of $(a)!0.5!(b)$] (s) {Score\\[-1pt]\footnotesize <range>};
  \node[box,text width=2.4cm,right=of s] (d) {<Decision>\\[-1pt]\footnotesize <range>};
  \draw[arr] (a.east) -- (s.west); \draw[arr] (b.east) -- (s.west); \draw[arr] (s) -- (d);
\end{tikzpicture}
\end{center}

\section{Inputs}
\begin{tabularx}{\linewidth}{@{}lLl@{}}
\toprule
Input & Identifier & Used for \\
\midrule
 &  &  \\
\bottomrule
\end{tabularx}

\needspace{10\baselineskip}
\section{How the score is built}
\begin{equation*}
 <one core equation>
\end{equation*}
where <symbols in plain words>. <Weight split in words.>

\section{How to read the output}
\begin{tabularx}{\linewidth}{@{}lL l@{}}
\toprule
Score & Meaning & Action \\
\midrule
Low &  &  \\
Neutral &  &  \\
High &  &  \\
\bottomrule
\end{tabularx}

\textbf{<The one thing users most often misread.>}

\section{Worked example}
<Real recent output, 2 to 3 lines with the arithmetic.> In words: <...>.

\section{Limitations}
\begin{itemize}
  \item <Capital letter, no trailing full stop>
\end{itemize}

\end{document}
```
