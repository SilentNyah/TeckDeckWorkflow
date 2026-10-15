## BUILD RESULT
* Slide: 030 / `stateIn` と `WhileSubscribed(5_000)`
* Mode: FIX
* Iteration: 2
* Files touched: slides/deck.pptx (shapes 18, 24, 31–34, 42; new shapes 51–53), assets/diagrams/while_subscribed_timeout.py（変更なし）
* Sources rechecked: SRC-002, SRC-003, SRC-006, SRC-028

### Finding dispositions
| Finding | Disposition | 内容 |
| ------- | ----------- | ---- |
| FINDING-001 | `FIXED` | 左段の段5 に `codehl` でコード 2 行を置いた（`val ui by vm.uiState.collectAsStateWithLifecycle() // 非表示で停止` を `mark_lines=[1]`・`focus=True`、`collectAsState()` の行は反例として減光）。直下に「非表示の間は観測させない（`SRC-003` の推奨）。差は本資料による。」、全幅の注記帯 4 行目に「UI 側の収集がライフサイクル対応であることが前提 ─ `SRC-002` の `Strongly recommended` 項目「Use lifecycle-aware UI state collection.」。」を置いた。縦の余地は段5 の連鎖説明 2 行を全幅 1 行に畳み（表現の変更、削除なし）、注記帯を 2→4 行、2 列の開始を 3.260→3.510in、表のピッチ 0.300→0.230in で作った。最下段 y=5.000/5.160 は不変（`CF-52`）。 |
| FINDING-002 | `FIXED` | 脚注 2 行目（y=5.160）の末尾に「テストでの扱いは Slide 063。」を句として追加。 |
| FINDING-003 | `FIXED` | shape id=42 の `SRC-006` run を Calibri → Consolas。 |

### Carried-forward rules applied
* 【b003 / Slide 025 由来 `CF-52`】最下段の 2 スロット（y=5.000 / 5.160）は動かさない。
* 【b001 由来 `CF-53`】識別子・SRC 番号は mono。
* 【Phase 1 由来 `CF-61`】「リソースを消費し続ける」を画面から落とさない ─ 右段 4 行目で維持。
* 【b003 由来 `CF-76`】推奨度ラベルは項目名と併記（`Strongly recommended`＋「Use lifecycle-aware UI state collection.」）。
* 【2026-09-06 由来 `CF-77`】5 秒の理由は「本資料による」と明示 ─ 注記帯 2 行目で維持。

### Character count
* Counted (本文, `visual-design.md` §5): 1148
* Not counted: `title:` キーメッセージ (41) / `chapter:` 章ラベル (18) / `src:` 出典行 (23) / `label:` 図の名札 ×5 (31) / `legend:` 時間軸 (4)
  （図形名で区別。注記帯の 4 行は述語があるので Counted に入れた）

### Deviations from spec
* Cosmetic（見た目だけ）: 右のコードカードの余白 0.160 → 0.100in。表の見出し高 0.260 → 0.220in。
* Semantic（意味を持つ）: 段5 の連鎖説明を全幅 1 行に畳んだため、「画面が非表示 → 収集が止まる → 購読者が 0 → 猶予に戻る」が 1 文になった。文の順序は storyboard と同じ。**要確認。**

### Fit
* Body: 1148 chars vs budget 450（`R8-7` 超過は承認済みの先例 028＝1030 字に従い、技術的説明は削っていない）／ used 5.16in vs available 5.20in → fits

### Impact on other slides
* Slide 031 の対比表 3 行目の括弧書き ─ **未変更**。R6 notes の候補として報告のみ。

### Points requiring user confirmation
* `collectAsState()` を反例として減光表示したこと（素の `collectAsState()` を「誤り」と読ませない文言にしている）。

### Progress file
* last line: `reported 030 2026-09-09T03:30`
