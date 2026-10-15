あなたは techdeck-workflow のオーケストレータです。Phase 4 の是正ラウンド p4-030 で、Slide 030 の反復 2 を回しています。

必ず最初に手順書を読み、それに従ってください:
- 手順書: {{SKILL_DIR}}/workflows/phase3-batch-build.md（特に「発注文の契約」の節）
- 評価用エージェントの定義: {{AGENTS_DIR}}/techdeck-slide-reviewer.md

プロジェクト（PROJECT_ROOT）: {{PROJECT_ROOT}}
- slides/storyboard.md, slides/review_state.md, sources/source_index.md があります。
- レビュー結果（反復 1）: {{PROJECT_ROOT}}/review-result-030-iter1.md
- ビルダーの報告（反復 2 の FIX）: {{PROJECT_ROOT}}/build-result-030-iter2.md
- 反復 2 のレンダリング済み PNG: {{PROJECT_ROOT}}/output/png/slide-30.png（前後は slide-29.png / slide-31.png）

やること: 評価用エージェント techdeck-slide-reviewer に渡す「発注文（dispatch）」の全文を書いて返してください。ユーザーが待っているので、1 回で通る、自己完結した発注文にしてください（レビュー担当が迷わないよう、必要な事実は発注文に入れてください）。

返答は発注文の全文だけにしてください。前置きや解説は不要です。
