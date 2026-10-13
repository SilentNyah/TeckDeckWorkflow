---
name: techdeck-workflow
description: Phase-gated process for building a technical explainer slide deck (PPTX) that a reader must understand alone, without a speaker. Use when starting a brand-new deck project in an empty or bare folder (scaffolding the directory tree, TASK.md, a deck profile and a first deck), when the project already has TASK.md plus slides/storyboard.md and slides/review_state.md, or when asked to research a technical topic for a deck, propose or revise a deck outline, build a chapter or any batch of new slides, fix one or more named slides, apply PowerPoint reviewer comments (comment-import-rNNN rounds), or run a whole-deck final review before finalizing. Builds slides in batches by default and runs a builder-agent / reviewer-agent loop until no CRITICAL or HIGH findings remain, then hands the batch to the user for approval. Enforces never self-approving a slide, split-don't-delete, and evidence-based push-back on technically wrong feedback.
---

# Technical deck workflow

A four-phase pipeline with hard stops. Every phase ends by reporting and stopping —
phases never auto-advance.

## 0. Start of every turn

1. Read `TASK.md` → goal / audience / reading mode / target version / scope /
   required topics / **`Current phase`** / deliverable.
   **If `TASK.md` does not exist, this is Phase 0** — read
   `workflows/phase0-project-setup.md` and assume nothing else exists either.
   If `Current phase` is missing, infer it (§4) and **propose adding the field**.
   Never guess silently.
2. Read `slides/deck-profile.json` if present (palette, fonts, geometry, language,
   conventions). If absent, propose creating one — see `reference/deck-profile.md`.
3. Route to **exactly one** workflow (§1), read that file, follow it, stop where it says stop.
   Do not execute a phase you were not routed to.

## 1. Routing

| Current phase / request shape | Read |
| --- | --- |
| Phase 0 / no `TASK.md`, empty folder, "start a new deck project" | `workflows/phase0-project-setup.md` |
| Phase 1 / research a topic, user pasted URLs | `workflows/phase1-research.md` |
| Phase 2 / outline, chapter order, slide split | `workflows/phase2-structure.md` |
| Phase 3 / create new slides — **the default** | `workflows/phase3-batch-build.md` |
| Phase 3 / create exactly one slide (user asked 「1枚だけ」) | `workflows/phase3-slide-creation.md` |
| Phase 3 / chat feedback on one or more slides | `workflows/phase3-slide-review.md` |
| Phase 3 / the PPTX carries PowerPoint comments | `workflows/phase3-pptx-comment-review.md` |
| Phase 4 / all slides APPROVED **and** user asks to finalize | `workflows/phase4-deck-final-review.md` |

Before any Phase 3 work also read `slides/review_state.md` and `slides/storyboard.md`;
add `slides/reviews/` and `slides/review-input/` when comments are involved.

## 2. Phase 3 sub-routing

**Batch build (default)** — user asked for new slides, a chapter, or 「続き」.
Target = the `NOT_STARTED` slides of the next chapter. Build → review → fix loop per slide;
every slide exits at `AWAITING_REVIEW`, never `APPROVED`.
See `workflows/phase3-batch-build.md`.

**Single slide** — user explicitly asked for one slide, or the batch resolves to one.
Same loop, batch of one.

**Chat review** — user gave feedback in conversation, or specific slides are
`AWAITING_REVIEW` / `REVISION_REQUIRED`. Revise the named slides only — naming several is fine.

**PPTX comment review** — a deck carries PowerPoint comments, or a new commented file
landed in `slides/review-input/`. Batch: handle every commented slide in one pass,
but only commented slides. Two intake modes:

* **Mode A** — a separate commented file already exists in `slides/review-input/`.
* **Mode B** — comments were added directly to the working `slides/deck.pptx`.
  **First action: snapshot it to `slides/review-input/deck-review-rNNN.pptx` before any edit.**
  Mode B is the common case in practice.

## 3. Non-negotiable gates

* エージェント自身の判断でスライドを `APPROVED` にしない。承認はユーザーの明示的な指示のみ。
* エージェント自身の判断で PPTX コメントを `CLOSED` にしない。
* **新規作成は既定でバッチ（まとめて作成）。** 単枚モードはユーザーが明示的に求めた場合のみ。
* バッチの既定対象は `NOT_STARTED` のスライドのみ。`AWAITING_REVIEW` / `REVISION_REQUIRED` /
  `APPROVED` のスライドは、ユーザーの明示指示がない限りバッチに含めない。
* **レビュー用エージェントの判定は承認ではない。** `PASS` / `PASS_WITH_MINOR_FIXES` は
  レビュー総合判定（`status-vocabulary.md` の名前空間(3)）であり、スライド状態(1)の
  `APPROVED` とは別の名前空間である。**ループの成功時の終端は常に `AWAITING_REVIEW`。**
* `slides/deck.pptx` は1ファイルである。**ビルドとレンダリングは常に直列**。
  並列化してよいのはレビューだけ。
* 承認済みスライドを、ユーザーの指示または PowerPoint コメントなしに変更しない。
* **技術的な正確性と説明の十分性を、見栄えや簡潔さより優先する。**
  ただし**十分性は文章量ではない。** 図・ピクトグラムへの置換は削減ではない
  （`reference/editorial-rules.md` / `reference/visual-design.md` §5）。
* 内容が1枚に収まらない場合は、説明を削らずスライド分割を提案する。
* **各スライドにキーメッセージを1つ置く。** 2行以内、改行位置は storyboard が決める。
  重要語は文中で1〜3語強調する。規定は `reference/visual-design.md`。
* 技術的に誤ったフィードバックやコメントは、そのまま反映せず、根拠と理由を報告する。
* `slides/review-input/` 配下を編集しない。ラウンド番号を再利用しない。
* **仕様は 5 つの面にある**（storyboard / `review_state.md` の規則 / 発注文 / 図の生成器 /
  `source_index.md`）。**1 つ直したら同じ編集で全部を掃く。** 訂正は本文を書き換え、注記の追記で
  済ませない（`workflows/phase3-batch-build.md`「仕様面」）。
* **発注文に出典の本文を書かない。** 「storyboard の `### Sources` に従え」「索引の `SRC-NNN` を読め」
  と参照だけを書く。レビュー担当への誤った転記は捕まえる側を壊す（同「発注文の契約」）。
* 各 workflow の末尾で停止して報告する。フェーズを自動で進めない。

The push-back rule is load-bearing: when a comment is technically wrong, **do not apply it**.
Verify against primary sources first, then report the evidence. When the user's point is
partly right, reflect the correct part and say precisely how you reframed it.

## 4. Phase inference (when `TASK.md` lacks `Current phase`)

| Condition | Phase |
| --- | --- |
| No `TASK.md`, or no `slides/` directory | **Phase 0** |
| `TASK.md` exists but no `slides/outline.md` | Phase 1 |
| Outline exists, `review_state.md` absent or all `NOT_STARTED` | Phase 2 |
| Any row not `APPROVED` | Phase 3 |
| All `APPROVED` **and** user asked to finalize | Phase 4 |

Phase 0 creates the tree and a deck, but **not** `outline.md` / `storyboard.md` /
`review_state.md` — those are Phase 2 outputs, and an empty `outline.md` would push a
brand-new project straight to Phase 2 by this table.

## 5. Project files

| Path | Role | Written by |
| --- | --- | --- |
| `TASK.md` | 目的・読者・対象版・範囲・現フェーズ | Phase 0 + user |
| `AGENTS.md` | スキルへの案内とプロジェクト固有の原則 | Phase 0 |
| `.gitignore` | バックアップ・レンダリング成果物の除外 | Phase 0 |
| `slides/deck-profile.json` | 配色・フォント・寸法・表記規約 | Phase 0 |
| `slides/AGENTS.md`, `examples/AGENTS.md` | 配下向けの規約ポインタ | Phase 0 |
| `sources/source_index.md` | 出典 `SRC-NNN` | Phase 1 |
| `notes/findings.md` | 調査結果 | Phase 1 |
| `notes/open_questions.md` | 未解決の問い `OQ-NNN` | Phase 1 |
| `notes/glossary.md` | 用語 | Phase 1 |
| `notes/visual-references.md` | 見た図と構造の型 `VIS-NNN` | Phase 1 |
| `sources/images/` | 調査で見た図の保存先（**貼らずに翻案する**） | Phase 1 |
| `notes/decisions.md` | 決定 `DEC-NNN` | 全フェーズ |
| `slides/outline.md` | 章構成 | Phase 2 |
| `slides/storyboard.md` | スライドごとの詳細設計 | Phase 2 |
| `slides/review_state.md` | 進行状態 | Phase 2〜4 |
| `slides/deck.pptx` | 作業中デッキ | Phase 3 |
| `slides/review-input/` | コメント付き原本（**読み取り専用**） | user |
| `slides/review-output/` | ラウンドごとの修正版 | Phase 3 |
| `slides/reviews/` | コメント記録・レビュー記録 | Phase 3〜4 |
| `examples/` | 完全版サンプルコード | Phase 1・3 |
| `assets/diagrams/` | 編集可能な図のソース | Phase 3 |
| `output/pdf/`, `output/pptx/` | レンダリング結果・最終成果物 | Phase 3〜4 |

## 6. Status vocabulary

Slide state: `NOT_STARTED` `DRAFTING` `AWAITING_REVIEW` `REVISION_REQUIRED` `APPROVED`
`BLOCKED` `CUT` `REUSED`

PPTX comment state: `OPEN` `APPLIED` `VERIFIED` `NEEDS_CLARIFICATION` `REJECTED` `CLOSED`

Full definitions, the review-verdict / severity / finding sets, and the ID schemes:
**`reference/status-vocabulary.md`** — that file is the single source of truth.

## 7. Approval handling

**Single slide.** 「OK」「承認」 → set `APPROVED`, **then stop**.
「OK、次へ」 → (1) set `APPROVED` → (2) read `workflows/phase3-batch-build.md`
→ (3) build the next batch → (4) set each slide `AWAITING_REVIEW` and stop.

**Multiple slides** (a batch, or a comment round). 「すべてOK」 → all slides in the round `APPROVED`.
Only some named → only those. **Scope unclear → leave everything at `AWAITING_REVIEW`
and ask.** Some need rework → only those become `REVISION_REQUIRED`.

## 8. Final review preconditions

All six must hold before Phase 4 starts:
no `AWAITING_REVIEW`, no `REVISION_REQUIRED`, no `BLOCKED`, no unresolved PPTX comments,
no `NEEDS_CLARIFICATION`, every slide `APPROVED` — **plus** an explicit user instruction
to finalize. If any fail, report the gaps and do not start.

## 9. Tooling

Any read / edit / render / comment-extraction on a `.pptx` → use the **`pptx-toolkit`** skill.

* **A missing deck is created, never improvised.** If `slides/deck.pptx` does not exist —
  including when Phase 3 is reached without it — run `pptx-toolkit/scripts/new_deck.py`
  before drawing anything. A bare `Presentation()` is 4:3 with a white canvas, and this
  toolchain's default text colour is near-white: the result is invisible text at the wrong
  size.
* **Snapshot `slides/deck.pptx` before every batch edit.** Batch edits are not undoable.
* **Rendering after every slide change is mandatory.** The checklist is
  `reference/review-rubric.md` §R5 — the single canonical copy.
* **Batch a wave's rendering into one PowerPoint COM session.**
  `render_deck.py <deck> --slides 31-37 --png-dir <out>` — one launch, not seven.
  **Never run two renders concurrently:** COM attaches to the running instance, so the
  first `app.Quit()` kills the other export.
* Editable diagram sources live in `assets/diagrams/`; update them whenever the diagram changes.
* **State files are written through `scripts/statekit.py`**, not through ad-hoc one-off scripts:
  ledger rows in `review_state.md`, storyboard fields, `### Sources` rows, `source_index.md`
  appends, review-record appends. It asserts section boundaries and exactly-one match and keeps
  the file's line endings. `statekit.py next-id SRC` / `dupes` guard numbering.
* **Renumbering after a split goes through `scripts/renumber.py --insert-after N`** (dry-run first).
  It rewrites page references, prev/next links, chapter maps, appendix page lists, the progress
  table and carried-forward origins, and lists the hits on `APPROVED` slides separately so the user
  can be asked once.
* **図形・アイコン・コードのハイライトは自前で組まない。**
  `deckkit.shape()`（プリセット図形すべて）、`pictogram.draw()`（33種）、
  `codehl.code_block()`（`code_palette` を適用）を使う。
  新しい `prst` を使ったら**必ず一度レンダリングして開けることを確認する**
  （その図形に無い調整値名を書くと、`check_deck.py` は通るのに PowerPoint が拒否する）。

## 10. Output language

Deck content, state files and review records follow `deck-profile.json` `language`.
Conversation with the user follows the user's language.
Code identifiers and status tokens are always ASCII.

## 11. File resolution

For `workflows/*.md` and `templates/*.md`: use `<project>/<same path>` when it exists,
otherwise this skill's copy. A project may override a single workflow locally;
do not fork the set wholesale.

## Reference files

| File | When to read |
| --- | --- |
| `reference/status-vocabulary.md` | any state transition, or an unfamiliar status token |
| `reference/state-schema.md` | writing `review_state.md`, `decisions.md`, `source_index.md` |
| `reference/editorial-rules.md` | writing or revising slide content (**Phase 3 必読**) |
| `reference/visual-design.md` | キーメッセージ・強調・分量・図の使い方 (**Phase 3 必読 / R8 の実体**) |
| `reference/examples-rules.md` | adding or changing `examples/` |
| `reference/review-rubric.md` | reviewing any slide (**the only rubric — R1〜R7**) |
| `reference/deck-profile.md` | palette / font / geometry questions, new project setup |
| `templates/` | creating any new record: storyboard entry, source, finding, review report, comment import, TASK.md |
| `templates/scaffold/` | Phase 0 file templates (`{{SKILL_DIR}}` / `{{PROJECT_NAME}}` are substituted by `scripts/init_project.py`) |
| `scripts/init_project.py` | Phase 0: create the tree, state-file stubs and the first deck |
| `scripts/statekit.py` | any write to `review_state.md` / `storyboard.md` / `source_index.md` / `slides/reviews/`; `next-id`, `dupes` |
| `scripts/renumber.py` | a split or insertion changed slide numbers |
| `pptx-toolkit` `templates/presets/` | `dark` / `light` colour presets — the starting point for a new project |

## 12. Quality loop agents

Phase 3 builds through two subagents (`workflows/phase3-batch-build.md`).

| Agent | Role | Tools | Can write state? |
| --- | --- | --- | --- |
| `techdeck-slide-builder` | builds / fixes slides in `deck.pptx` | Read Write Edit Glob Grep Bash | **no** — never `review_state.md` |
| `techdeck-slide-reviewer` | reviews the rendered PNG against `reference/review-rubric.md` | Read Glob Grep Bash | **no** — has no Write/Edit at all |

このターン（オーケストレータ）だけが `slides/review_state.md` を書く。
**判断を持つエージェントは書けず、書けるエージェントは判断を持たない。**

評価用エージェントにはビルダーの言い分を渡さない。新しい文脈で成果物だけを見せる。
これは現在の「自己レビュー」が構造的に持てない独立性である。

ループの合格バーは「未解決の `CRITICAL` / `HIGH` が 0」＝ `phase4-deck-final-review.md`
の最終化基準と同一。**満たしても終端は `AWAITING_REVIEW`。`APPROVED` はユーザーのみ。**

エージェントが使えない環境では、同じループをこのターン内で実行する
（`workflows/phase3-batch-build.md` の「サブエージェントが使えない場合」）。
手順もバーも同一で、失われるのは独立性と並列性だけである。
