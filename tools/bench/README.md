# tools/bench — techdeck-workflow のクレジット消費ベンチマーク

Phase 3 ループの 3 つの役割（オーケストレータ／builder／reviewer）が 1 発注あたりに
消費するトークンと推定 USD を、実案件サイズの fixture で測る。
スキル改良（CF の圧縮、部分読み、出力上限など）の前後で同じ run を回し、同じ表で比べるための道具。

## 測り方の要点

* **計測器は `claude -p --output-format json`。** Agent ツールの完了通知にある token 数は
  「最後の呼び出しのコンテキスト長＋最後の出力」であって累積消費ではない。transcript も
  思考トークンを持たない。headless CLI だけが真の usage（input / cache write / cache read /
  output、thinking 内訳）と `total_cost_usd` を返す。
* S3（builder）/ S4（reviewer）は `--agent techdeck-slide-builder` / `--agent techdeck-slide-reviewer`
  で、インストール済みのエージェント定義（`~/.claude/agents`）のまま走らせる。
* 発注文は手順書どおり **`## Feedback carried forward` 全文を本文に貼る**（`{{CARRIED}}`）。
  これが現行の実コストなので、安く見せるために省かない。
* transcript（`~/.claude/projects/*/<session>.jsonl`）を回収し、tool_use ↔ tool_result で
  「どのファイルが何 KB 実際にコンテキストへ入ったか」を取る（ファイルサイズではない）。
* 価格は `cost.py` の表（定価）。cache write は TTL 別（5 分 1.25×／1 時間 2×）。
  対話セッションと headless は 1 時間 TTL なので、比較用に 5 分換算も出す。
  Fable 5 と 5.1 は cache read の単価だけ違う（0.1× と 0.025×）。

## 使い方

```bash
cd tools
# 1. fixture（実案件の読み取り専用コピー。deck.pptx と .bak は入れない）
python -m bench.make_fixture --source "D:/documents/android/architecture" \
    --dest "../skills/techdeck-workflow-workspace/fixture" --slides 29 30 31 \
    --png-dir output/png-final --extra "../skills/techdeck-workflow/evals/files"

# 2. 実行（直列。--dry-run で prompt だけ描画）
python -m bench.run_bench --evals "../skills/techdeck-workflow/evals/evals.json" \
    --workspace "../skills/techdeck-workflow-workspace" \
    --fixture "../skills/techdeck-workflow-workspace/fixture" \
    --iteration 1 --reps 3 --model claude-fable-5-1

# 3. 採点（evals.json の assertion を正規表現で機械判定）と集計
python -m bench.grade   "../skills/techdeck-workflow-workspace/iteration-1"
python -m bench.analyze "../skills/techdeck-workflow-workspace/iteration-1" \
    --iteration0 "<2026-10-13 の subagents transcript ディレクトリ>"   # 任意

# 3b. 新旧比較（PRD の目標を ✔/✘ で判定。config ごと・シナリオごと）
python -m bench.compare "../skills/techdeck-workflow-workspace/iteration-1" "../skills/techdeck-workflow-workspace/iteration-2" \
    --target S0-turn-start=-30 --target S3-builder-fix=-15 --target S4-reviewer-slide=-15 \
    --out "../skills/techdeck-workflow-workspace/iteration-2/compare.md"

# 4. skill-creator の viewer（静的 HTML）
python <skill-creator>/eval-viewer/generate_review.py "../skills/techdeck-workflow-workspace/iteration-1" \
    --skill-name techdeck-workflow --benchmark "../skills/techdeck-workflow-workspace/iteration-1/benchmark.json" \
    --static "../skills/techdeck-workflow-workspace/iteration-1/review.html"

# テスト
cd .. && python -m unittest discover -s tools/bench/tests -t tools
```

run ごとの成果物: `prompt.md`（送った全文）、`result.json`（CLI の生 JSON）、`outputs/response.md`、
`timing.json`、`transcript.jsonl`、`metrics.json`、`grading.json`、`project/`（その run の作業コピー）。

## iteration-2（PRD v2 の新版）で変えたもの

* `evals/evals-v2.json`: S3 / S4 の発注文が新契約に従う。`{{CARRIED_CF:30}}` は runner が
  `statekit.py show-cf --for-slide 30` を呼んで埋める（126〜130KB → 14KB）。PRIOR はレビュー記録のパス。
* `fixture-v2/`: `fixture/` ＋ `slides/reviews/slide-030.md`（反復 1 の REVIEW RESULT と反復 2 の BUILD RESULT）。
* arm は `--config` で分ける: `--model claude-opus-5-5 --config with_skill_opus55`、
  `--extra "--effort high" --config with_skill_effort_high`（`--extra` は引用符で 1 つの文字列）。

## 新旧比較のとき

* **対照 → 同期の順**で回す（2026-10-13 の教訓）。インストール済みの `~/.claude` を新版に同期する前に
  旧版の run を取り終える。`--config old_skill` / `--config with_skill` でディレクトリを分ける。
* viewer は `with_skill` / `without_skill` の名前で色分けする。旧版を `without_skill` と名付けると
  その色分けが使える。

## スコープ外（意図的）

描画・レンダリングを含む 1 波の計測（PowerPoint COM が直列で遅く、P1〜P5 の対象でもない）。
