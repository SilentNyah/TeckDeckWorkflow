# AGENTS.md（`slides/` 配下）

この配下の作業は、`techdeck-workflow` スキルの編集規約に従う。

```text
{{SKILL_DIR}}/reference/editorial-rules.md
```

あわせて次も確認する。

* ルートの `../AGENTS.md`
* 現在のフェーズに対応する workflow（`{{SKILL_DIR}}/workflows/`）
* 配色・フォント・表記規約は `deck-profile.json`

**この配下で特に効く原則:**

* 技術的な正確性と説明の十分性を、見栄えや簡潔さより優先する。
* speaker notes が無くても、スライド本文だけで技術内容を理解できるようにする。
* 情報が1枚に収まらない場合は、内容を削らずスライド分割を提案する。
* 図・本文・コード・出典の内容を一致させる。
* `review-input/` 配下は読み取り専用。編集しない。
* レビュー用エージェントの判定（`PASS` 等）は承認ではない。承認はユーザーのみ。
* `slides/deck.pptx` は1ファイル。ビルドとレンダリングは直列に行う。
