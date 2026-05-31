# 設計意図ドキュメント

<!-- ENTRY:2026-05-31_16-20 -->
## 変更 2026-05-31 16:20

<!-- AUTO:START -->
タップ穴（#featureName）が M6x1.00 から M8x1.25 にサイズアップされ、下穴径 5.0→6.8 mm・ざぐり径 11.25→14.25 mm と全寸法が拡大している。これは締結強度を高めるためにより大きなネジ規格を採用したことを示す。また「押し出し 4」の深さが 30→40 mm に延長されており、部品本体の厚みが増す形でネジ締結部の強化と形状拡大が同時に行われている。

### 変更 (2 件)
- **#featureName** (hole) — `cBoreDepth`: 6 mm → 8 mm、`cBoreDiameter`: 11.25 mm → 14.25 mm、`cSinkDiameter`: 13.44 mm → 17.92 mm、`featureName`: M6x1.00 ↧ #holeDepthV3 → M8x1.25 ↧ #holeDepthV3、`holeDiameter`: 5.000 mm → 6.800 mm、`isoHoleTableEx`: M6 / 1.00 mm (Coarse) / Straight tap → M8 / 1.25 mm (Coarse) / Straight tap、`majorDiameter`: 6 mm → 8 mm、`tapClearance`: 2.0 → 1.6、`tapDrillDiameter`: 5.000 mm → 6.800 mm
- **押し出し 4** (extrude) — `depth`: 30 mm → 40 mm

変更なし: 8 件
<!-- AUTO:END -->

<!-- INTENT:START -->

<!-- INTENT:END -->
<!-- /ENTRY:2026-05-31_16-20 -->

<!-- ENTRY:2026-05-31_16-16 -->
## 変更 2026-05-31 16:16

<!-- AUTO:START -->
前回スナップショットから 3 件のフィーチャーが追加された（削除・変更なし）。「スケッチ 2」と「押し出し 4」は新たな形状要素の付加を示しており、「hole（#featureName）」は穴あけ加工の追加を表している。モデルは基本形状の拡張と穴加工の組み込みにより、より実用的な部品形状へと進化している。

### 追加 (3 件)
- **#featureName** (hole) — featureId: `FRqWJvvBhjiTIdX_1`
- **スケッチ 2** (newSketch) — featureId: `F8w6iZBNwBlU7zC_1`
- **押し出し 4** (extrude) — featureId: `FBpmpB25gYsKu5a_1`

変更なし: 7 件
<!-- AUTO:END -->

<!-- INTENT:START -->

<!-- INTENT:END -->
<!-- /ENTRY:2026-05-31_16-16 -->

このドキュメントは `/review-diff` コマンドによって自動更新されます。

各エントリは以下の構造を持ちます：
- `<!-- AUTO:START -->〜<!-- AUTO:END -->` — 自動生成された差分サマリー（編集しないでください）
- `<!-- INTENT:START -->〜<!-- INTENT:END -->` — 設計意図・変更理由・今後の方針などを自由に記述する欄

