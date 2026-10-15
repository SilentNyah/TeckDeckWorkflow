発注:
- PROJECT_ROOT: {{PROJECT_ROOT}}
- MODE: FIX
- SLIDE: 030 / `stateIn` と `WhileSubscribed(5_000)`
- ITERATION: 2
- STORYBOARD: {{PROJECT_ROOT}}/slides/storyboard.md の `## Slide 030`（`statekit.py show-slide --slide 30` で 1 回で読める。この案件の storyboard は旧版の雛形で `### Current spec` 欄は無い。`### Body content` と `### Sources` に従うこと）
- SOURCES: {{PROJECT_ROOT}}/sources/source_index.md
- EXAMPLES: なし
- PROFILE: {{PROJECT_ROOT}}/slides/deck-profile.json
- VISUAL: {{SKILL_DIR}}/reference/visual-design.md
- TOOLKIT: {{TOOLKIT}}
- PROGRESS_FILE: {{PROJECT_ROOT}}/output/bench/progress-030.txt
- PRIOR: {{PROJECT_ROOT}}/slides/reviews/slide-030.md の `## REVIEW RESULT（反復 1、2026-09-08）`（FINDING-001〜003）と、反復 1 の PNG {{PROJECT_ROOT}}/output/png/slide-30.png
- CARRIED: 下記（`statekit.py show-cf --for-slide 30` の出力。規則 1 件 1 行）

この計測環境には slides/deck.pptx も PowerPoint もありません。実際の描画はできないので、代わりに、あなたが返すはずの `## BUILD RESULT` を、各 Finding の disposition（FIXED / PUSHED_BACK / PARTIAL / NEEDS_USER）と「何をどう描くか（図形・線・文の変更・座標）」まで具体的に書いて返してください。storyboard の節には直しの指示が既に書き込まれています。

返答は `## BUILD RESULT` ブロックだけにしてください。

---
CARRIED:

{{CARRIED_CF:30}}
