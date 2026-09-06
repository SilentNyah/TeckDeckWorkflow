# Review Report Template

<!--
ファイル名の例:
- slides/reviews/slide-001.md
- slides/reviews/deck-final-review.md

スライド単体のレビューでは、過去のレビュー履歴を上書きせず追記する。
-->

# Review Report

## Review metadata

| Item             | Value                                                    |
| ---------------- | -------------------------------------------------------- |
| Review ID        | `REVIEW-XXX`                                             |
| Review target    | Slide NNN / Entire deck                                  |
| Title            |                                                          |
| Review date      | YYYY-MM-DD                                               |
| Reviewer         | User / techdeck-slide-reviewer / Agent / Other                                     |
| Workflow         | `phase3-slide-review.md` / `phase4-deck-final-review.md` |
| Target version   |                                                          |
| Review iteration | 1                                                        |
| Current status   |                                                          |

## Review target files

* PPTX:
* PDF:
* Image:
* Storyboard:
* Diagram source:
* Example source:

## Overall result

次のいずれかを使用する。

* `PASS`
* `PASS_WITH_MINOR_FIXES`
* `REVISION_REQUIRED`
* `BLOCKED`
* `AWAITING_USER_REVIEW`

### Summary

レビュー結果の概要を記載する。

### Finding counts

| Severity | Count |
| -------- | ----: |
| CRITICAL |     0 |
| HIGH     |     0 |
| MEDIUM   |     0 |
| LOW      |     0 |

## User feedback

ユーザーから受け取ったフィードバックを原文の意味を変えずに整理する。

*
*
*

## Feedback classification

| Feedback | Category                                                           | Action |
| -------- | ------------------------------------------------------------------ | ------ |
|          | Technical accuracy / Explanation / Diagram / Code / Layout / Other |        |

## Technical review

判定項目は `reference/review-rubric.md` §R1 技術的正確性
（`R1-A` 正確性 / `R1-B` 前提・制約・例外 / `R1-C` 用語）が唯一の正である。

#### Notes

*

## Explanation review
判定項目は `reference/review-rubric.md` §R2 説明の十分性 が唯一の正である。

### Notes

*

## Diagram review
判定項目は `reference/review-rubric.md` §R3 図 が唯一の正である。

### Notes

*

## Code review
判定項目は `reference/review-rubric.md` §R4 コード が唯一の正である。

### Notes

*

## Visual and rendering review
判定項目は `reference/review-rubric.md` §R5 表示・レンダリング が唯一の正である。

### Notes

*

## Findings

### FINDING-001: 指摘タイトル

* Severity: `CRITICAL` / `HIGH` / `MEDIUM` / `LOW`
  （`R8` の既定は `R8-1`・`R8-7` のみ `HIGH`、`R8-9` は `LOW`、他は `MEDIUM`）
* Category: `[TECH]` `[EXPLAIN]` `[DIAGRAM]` `[CODE]` `[SOURCE]` `[CONSISTENCY]`
  `[LAYOUT]` `[VISUAL]` のいずれか
* Rubric: 引用する項目ID（例 `R8-1`）。**引ける項目が無い指摘は指摘ではない**
* Affected area:
* Related Source IDs:
* Status: `OPEN` / `RESOLVED` / `DEFERRED` / `REJECTED`
* Fixable by builder: `yes` / `no` ─ 理由
* Carry forward: `yes` / `no` ─ 後続スライドへ効く一文

#### Problem

問題を具体的に記載する。

#### Evidence

問題と判断した根拠を記載する。

#### Impact

読者理解、技術的正確性、表示品質への影響を記載する。

#### Recommended action

推奨する修正を記載する。

#### Required workflow

* `phase1-research.md`
* `phase2-structure.md`
* `phase3-slide-review.md`
* `phase4-deck-final-review.md`
* `No additional workflow`

#### Resolution

修正内容または対応しなかった理由を記載する。

必要に応じてFindingを追加する。

## Revision summary

### Implemented changes

*
*
*

### Not implemented

| Requested change | Reason |
| ---------------- | ------ |
|                  |        |

### Files updated

*
*
*

### Diagrams updated

*
*

### Examples updated

*
*

### Sources rechecked

* `SRC-XXX`
*

## Impact on other slides

* Impact exists: Yes / No
* Affected slides:
* Reason:
* Recommended action:

他スライドを無断で変更せず、影響のみを記録する。

## Re-rendering result

* PPTX rendered:
* PDF rendered:
* Image rendered:
* Remaining layout issues:

## State transition

* Previous state:
* New state:
* Reason:

例:

```text
REVISION_REQUIRED
    ↓ 修正完了
AWAITING_REVIEW
```

エージェント自身の判断で `APPROVED` に変更しない。

## Points requiring user confirmation

*
*
*

## Approval

* User decision:
* Date:
* Comment:

## Review history

| Iteration | Date       | Result | Main changes |
| --------: | ---------- | ------ | ------------ |
|         1 | YYYY-MM-DD |        |              |
