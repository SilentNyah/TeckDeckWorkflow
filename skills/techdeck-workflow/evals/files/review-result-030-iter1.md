## REVIEW RESULT
* Slide: 030
* Batch: p4-030（Phase 4 の是正ラウンド。ユーザーの明示指示 2026-09-08）
* Iteration: 1
* Overall result: `REVISION_REQUIRED`
* Counts: CRITICAL=0 HIGH=1 MEDIUM=2 LOW=0
* Rubric items failed: R1-B-2, R2-4, R6-1, R5-4
* check_deck: 0 CRITICAL/HIGH, 0 MEDIUM
* 3-second takeaway: 「`stateIn` は上流をいつ止めるかも決める／5 秒は回転を吸収する猶予」
* Cold-read summary: PNG だけから読み取れた主張 ─ 「購読者が 0 になっても 5 秒以内に再購読されれば上流は止まらない」。読み取れなかった点 ─ 「なぜ画面が隠れると購読者が 0 になるのか（UI 側の収集がどう止まるのか）」。
* Body chars (§5 count): 1002 ／ not counted: タイトル・章ラベル・出典行・図の名札 ×5・時間軸ラベル ／ check_deck R7-9 reported: 1081

### FINDING-001
* Severity: `HIGH`
* Category: `[TECH]`
* Status: `OPEN`
* Rubric: R1-B-2
* Locus: 本文の機構説明（段5）と左下の注記 ─ 「画面が非表示になると収集が止まる」
* Problem: スライドの主張全体（画面が隠れると購読者が 0 → だから `WhileSubscribed(5_000)`）は、UI 側の収集がライフサイクル対応であることを前提にして初めて成立する。しかし画面には `collectAsStateWithLifecycle` が減光した 8pt の 1 行にしか無く、UI が UI state を収集するコードがどこにも無い。素の `collectAsState()` との差も示していない。
* Evidence: デッキ全文で `collectAsStateWithLifecycle` は 1 回（この減光行）、`repeatOnLifecycle` は 0 件。索引 `SRC-002` の `Strongly recommended` 項目「Use lifecycle-aware UI state collection.」と `SRC-003` の推奨（表示されていないときは UI に観測させない）は索引にあるが、画面はどちらにも帰属していない。
* Impact: 読者は「購読者が 0 になる」を `StateFlow` 側の挙動だと誤解し、素の `collectAsState()` でも上流が止まると考えうる。
* Recommended action: UI 側の収集を画面に置く（コード 2 行で `collectAsStateWithLifecycle()` と `collectAsState()` の差を並べ、前者を強調）。前提であることを帰属付きで明記する。
* Fixable by builder: yes
* Carry forward: yes ─ 購読の開始・停止を論じるスライドは、UI 側の収集方法を画面に置く。

### FINDING-002
* Severity: `MEDIUM`
* Category: `[CONSISTENCY]`
* Status: `OPEN`
* Rubric: R6-1（R2-6）
* Locus: 最下段の脚注（出典の原文行）
* Problem: `Test StateFlows`（`SRC-002`）は「テスト項目だから第11章へ」として 030 から外されたが、外した先 Slide 063 への導線が 030 側に無い。
* Evidence: デッキ全文検索で 030 → 063 の参照 0 件。063 は 2026-09-08 に置き場として確定済み（storyboard `### Sources` の ✅ 注記）。
* Impact: 030 を読んだ読者が、`StateFlow` をテストでどう扱うかを探せない。
* Recommended action: 脚注 2 行目の末尾に「テストでの扱いは Slide 063。」を句として足す（専用の 1 行を置く余地は無い）。
* Fixable by builder: yes
* Carry forward: no

### FINDING-003
* Severity: `MEDIUM`
* Category: `[VISUAL]`
* Status: `OPEN`
* Rubric: R5-4
* Locus: 右段の帰属 `SRC-006`（shape id=42）
* Problem: `SRC-006` の 1 箇所だけが Calibri で描かれている。同一スライドの id=24 と Slide 031 の同一表記は Consolas。
* Evidence: `inspect_deck.py` の run 一覧。`CF-53`（識別子・SRC 番号は mono）。
* Impact: 等幅と可変幅が混じり、SRC 番号が識別子として読めない。
* Recommended action: id=42 のフォントを Consolas に揃える。
* Fixable by builder: yes
* Carry forward: no

### R6 notes
* 031 の対比表 3 行目の括弧書きが「（＝上流をいつ止めるか）」になっている疑い。030 の `CF-61`（「リソースを消費し続ける」を落とさない）と突き合わせること（R6-1 の候補、ここでは判定しない）。
