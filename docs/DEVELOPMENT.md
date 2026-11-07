# 開発ガイド (環境・MZ-1500 仕様・CLI デバッグ手法まとめ)

本プロジェクト (魔境騎士パラディオン) の開発に必要な環境情報、MZ-1500 ハードウェア
仕様の要点、エミュレータ CLI を使ったデバッグ手法をまとめる。
詳細なデバッグ記録は `docs/DEBUG_STATE.md`、進捗は `docs/PROGRESS.md`、
ゲームデザインは `docs/DESIGN.md` を参照。

---

## 1. 環境・リポジトリ一覧

| 項目 | 場所 |
|---|---|
| ゲーム (本プロジェクト) | `c:\tools\mz1500action` |
| エミュレータ (C#, GUI + CLI) | `C:\tools\mz1500_emulator_csharp` |
| ROM (IPL/EXT/FONT) | `C:\tools\mz1500_emulator_csharp\romsample\` |
| アセンブラ | z88dk `z80asm` (`C:\z88dk\bin` を PATH へ) |
| Python 3 | PCG/譜面生成、ツール類 (`tools\`) |
| リファレンスサンプル | `qdfsample\MeikyuEnoTobiraA/B.qdf` (2面ディスクロードの実サンプル) |
| サンプル解析結果 | `tmp\parsed\MeikyuEnoTobiraA/B.qdf_00.bin` |
| エミュレータ開発規約 | `C:\tools\mz1500_emulator_csharp\.clinerules` (Conventional Commits 等) |

### ディレクトリ方針
- `src\` ソース / `docs\` ドキュメント / `tools\` 恒久ツール / `out\` ビルド出力
- `tmp\` は**使い捨てスクラッチ領域**。調査ログや一時スクリプトはここに置き、
  定期的に消してよい。恒久ツールは `tools\` に置く
  (現行: `code_compare.py` / `checkmzt.py` / `mztparse.py` / `qdfparse.py` は `tools\` 移動済み)

---

## 2. ビルド

### ゲーム側
```powershell
cd c:\tools\mz1500action
powershell -ExecutionPolicy Bypass -File build.ps1
```
- PCG アート (`tools\pcggen.py`) と譜面 (`tools\musicgen.py`) を再生成した後、
  z80asm で A面/B面をアセンブルし `tools\mkmzt.py` で MZT パック。
- 出力: `out\ParadionA.mzt` (A面: ローダ+PCG 24KB, load/exec 2000h)、
  `out\ParadionB.mzt` (B面: ゲーム本体, load/exec 1200h)
- `out\sideb.bin` は B面の生イメージ (実アドレス 1200h-3B73h 程度)。
  デバッグの diff 基準として使う。
- `src\sideb\main.lis` / `main.sym` はビルドのたびに**再生成される** (常に最新)。
  sym の値は **org 相対** (実アドレス = sym値 + 1200h) なので注意。

### エミュレータ側
```powershell
cd C:\tools\mz1500_emulator_csharp
dotnet build -c Release
dotnet run --project src\Mz1500.Cli -c Release --no-build -- <オプション>
```
- GUI (`Mz1500.Gui`) は手入力での動作確認用。ヘッドレス検証は CLI を使う。

---

## 3. E2E 起動コマンド (定型)

```powershell
cd C:\tools\mz1500_emulator_csharp
dotnet run --project src\Mz1500.Cli -c Release --no-build -- `
  --roms romsample `
  --qd c:\tools\mz1500action\out\ParadionA.mzt `
  --qd-swap c:\tools\mz1500action\out\ParadionB.mzt@700 `
  --key 0D@900 `
  --frames 3600 --no-text `
  --ppm c:\tools\mz1500action\out\frame.ppm
```
- frame 700 で B面へディスク差し替え、frame 900 に CR (15フレーム押下)、
  **ゲームは frame 989 前後から開始** (IPLロード ~240f + メッセージ + CR待ち + チェインロード)。
- 実行は**決定論的**: 同一パラメータなら同一結果。ダンプ範囲を変えた複数回実行の
  比較が可能 (watch フックの有無は結果に影響しない)。

---

## 4. CLI オプション リファレンス

| オプション | 意味 |
|---|---|
| `--frames N` | 実行フレーム数 (60fps) |
| `--roms DIR` | ROM ディレクトリ (既定 `romsample`) |
| `--qd FILE` | QD イメージ挿入 (A面) |
| `--qd-swap FILE@frame` | 指定フレームでディスク差し替え (B面ロード用)。複数可 |
| `--tape FILE` | テープ挿入 |
| `--key KEY[@frame]` | キー押下 (16進 VK コード or 1文字)。**15フレーム押下で自動リリース**。複数可。例: `0D`=CR, `20`=SPACE, `26`=↑, `25`=←, `27`=→, `28`=↓ |
| `--watch-write ADDR` | 指定アドレス (16進) への書き込み監視。複数可 |
| `--dump ADDR,LEN` | 実行終端時点のメモリダンプ。**最後の 1 つのみ有効** |
| `--dump-at FRAME@ADDR,LEN` | **指定フレーム到達時点**のメモリダンプ。複数指定可 |
| `--ppm FILE` | 最終フレームの画像出力 |
| `--wav FILE` | サウンド出力 |
| `--no-text` | テキスト画面ダンプを抑制 (既定では 40x25 を ASCII 変換して表示) |
| `--raw` | テキスト VRAM 生コード + 属性ダンプ |
| `--soundtest` | 内蔵サウンドテストプログラムを実行 |
| `--no-opm` / `--opm-clock HZ` | YM2151 (FM) の無効化/クロック指定 |

### --watch-write の仕様
- アドレスごとに **(PC, value) が変化した書き込みのみ**ログ (最大 200 件)。
  毎フレーム同じ値を書く場合は 1 回しか記録されないが、値が変われば必ず記録される。
- ログ形式:
  `frame N: write AAAAh=VVh from PC PPPPh HL=xxxx BC=xxxx DE=xxxx SP=xxxx`
- PC は「書き込み命令の**次の命令**のアドレス」になることがある
  (3 バイト命令 `ld (nn),a` なら実アドレス = 報告PC - 3)。
- 用途: 変数の変化追跡、**ワイルドライト犯人の PC 特定**。

### --dump / --dump-at の仕様
- **D000h-EFFFh (VRAM ウィンドウ) は常に 00h を返す** (Peek 経路の制約)。
  VRAM の実内容は `--ppm` かテキスト画面ダンプで確認する。
- B000h-BFFFh (ワーク/ミラー) とコード領域 (1200h-) は正しく読める。
- `--dump` は終端 1 回のみ。**途中フレームのスナップショットは `--dump-at` を使う**
  (「あるフレーム時点でどこが壊れているか」の特定に必須)。

## 5. 典型的デバッグ手順

### 5.1 コード領域破壊の検出 (「自機の左移動」バグで実績あり)
1. スナップショット取得:
   `--dump-at 989@1200,2974` (frame 989 時点のコード領域 1200h-3B73h)
2. ビルドイメージと diff:
   ```powershell
   python tools\code_compare.py <ダンプログ>
   ```
   → `DIFF AAAAh: expected xxh, RAM has yyh` で破壊バイト一覧が出る。
3. 破壊アドレスに `--watch-write AAAA` を付けて再実行 → **書き込み犯人の PC** が取れる。
4. PC を `main.sym` (org 相対: 実アドレス = 値 + 1200h) で逆引きし、
   `main.lis` で該当命令を確認。
5. 犯人ルーチン修正後、再度 diff を取り **diff = 0** を確認。

### 5.2 ビルド産物と実行イメージの一致確認
- `python tools\checkmzt.py` — `out\ParadionB.mzt` 内部のバイト列を解析し、
  read_keys 等の特徴バイトパターン位置を報告する。
- **ソースと bin/lis、bin と mzt の不一致** (並行編集・古い mzt の実行) は
  デバッグを完全に混乱させる。実行前に必ず整合を確認すること。

### 5.3 変数監視
主要ワークアドレス (詳細は `src\sideb\main.asm` 冒頭の defc 一覧):

| アドレス | 内容 |
|---|---|
| B000 | tick (フレームカウンタ) |
| B001 | **W_KEYS** (bit0=上 1=下 2=左 3=右 4=射撃 5=CR 6=C) |
| B003 | W_STATE (0=FIELD 1=BOSS 2=CLEAR 3=DEATH 4=GAMEOVER 5=ENDING) |
| B004 | W_STAGE (1-5) |
| B005-7 / B008-A | スコア / ハイスコア (BCD 3B) |
| B00B | 残機 |
| B00E-F | ボス出現タイマ |
| B040-47 | **自機スロット** (+0 状態, +1 attr, +2 x2, +3 y, +4 code, +5 t, +6/7 描画セル) |
| B040-DF | オブジェクトテーブル 20 slot × 8B (弾=1-4, 敵弾=5-8, 敵=9-14, アイテム=15-16, 爆発=17-19) |
| B0E0-E8 | サウンド変数 (V_BGM_PTR/DUR/ACT/LOOP, V_SE_PTR/ACT) |

### 5.4 画面確認
- テキスト画面: `--no-text` を付けずに実行 (MZ 表示コードを ASCII 変換して 40x25 表示)
- グラフィック: `--ppm out\xxx.ppm` で frame buffer 出力
- PNG 変換: `python tools\ppm2png.py out\xxx.ppm` — **引数は PPM のみ**
  (出力先は指定しない。同名 `.png` を 2 倍拡大で生成する)

### 5.5 MZT / QDF の解析
- `python tools\mztparse.py <mzt>` — 128B ヘッダ (attr/name/size/load/exec) と本体を分解
- `python tools\qdfparse.py <qdf>` — QD ブロック構造の解析
- `python tools\checkmzt.py` — ParadionB.mzt 内部のバイトパターン検証 (→ 5.2)
- `python tools\dumpanalyze.py <dumpA> <dumpB>` — 2 つのダンプの比較解析
  (※ CLI の `--dump` は最後の 1 つのみ有効。複数範囲は実行を分けること)
- `python tools\symlookup.py <sym> <addr>` — main.sym のシンボル検索
  (sym 値は org 相対。実アドレス = 値 + 1200h)

## 6. MZ-1500 ハードウェア仕様要点 (エミュレータ実装準拠)

※ `docs\mz1500_specification\Memory_Bank.md` の E0h-E3h の記述は実装と混同がある。
**エミュレータ (`Mz1500Memory.cs`) とそのテストが正。**

### CPU・メモリ
- Z80A @ 3.579545 MHz。命令単位実行 + T 状態管理 (Z80dotNet)。
- バンク切替 (OUT 命令):
  - `OUT E0h` : 0000h-0FFFh → RAM / `OUT E2h` : → モニタ ROM (BIOS 呼び出しには E2h)
  - `OUT E1h` : D000h-FFFFh → RAM / `OUT E3h` : → VRAM & I/O (**通常はこちら**)
  - `OUT E5h,n` : PCG プレーン選択 (1=B 2=R 3=G, 0=CG) / `OUT E6h` : PCG 解除

### VRAM / PCG
- VRAM: D000=テキストコード, D400=PCGコード, D800=テキスト属性, DC00=PCG属性
  (bit3=表示, bit7-6=バンク)
- PCG パターン実体: プレーン p・セル c = `PCGRAM[p*2000h + c*8 .. +7]`
- 優先度 `OUT F0h` (03h = PCG 表示 + PCG 前面) / パレット `OUT F1h`

### 8255 PPI (メモリマップド E000h-E003h)
- E000=Port A (キーストローブ out), E001=Port B (キーマトリクス in),
  E002=Port C, E003=制御ワード
- **E003 に 8Bh (PA=out, PB=in, PC=in) を書くこと**。モニタは PC を出力のままに
  するため、これを書かないと V-BLANK (PC bit7) 読みが壊れる。
  89h にすると PB が出力モードになりキー読みが全ビット立つ (過去のバグ)。

### キーマトリクス
- E000 (Port A) にストローブ (下位 4bit = 桁 0-9 を active-low で選択) を書き、
  E001 (Port B) を読む。**押下ビット = 0**。何も押していなければ FFh。
- 主要桁: 桁 0 bit0 = CR / 桁 4 bit5 = C / 桁 6 bit4 = SPACE /
  **桁 7 bit2=← bit3=→ bit4=↓ bit5=↑**
- 実機ではストローブ書き込み直後の Port B 読みはマトリクスが未安定の可能性が
  あるため、`read_keys` はストローブ後 `nop` ×4 を挟んでいる (エミュレータでは即時反映)。

### V-BLANK / 割り込み
- V-BLANK: 8255 Port C (E002) **bit7 = 0 の間** (走査線 199-261, 約 14,100T/フレーム)。
  E002 読みには 8255 を PC 入力モード (E003=8Bh) にする必要あり。
- サウンド割り込み (IM1 + 1038h フック + 8253) は**廃止済み**。
  現行は V-BLANK 同期メインループから `sound_update` を 1 フレーム 1 回呼ぶ。
- モニタはソフトリセット時 1038h に `jp 038Dh` を再書き込みする
  (1038h をフックに使う方式はリブートで壊れる)。

### サウンド / PIT
- PSG: `OUT E9h` = 両チャンネル同時 (`F2h`=左, `F3h`=右)。SN76489AN 形式。
- YM2151 (OPM): アドレス 0708h / データ 0709h。
- 8253 PIT: E004-E007。

### CPU ウェイト
- 表示期間 (各走査線クロック 0-159) 中の VRAM/PCG アクセスは H-BLANK
  (クロック 160/165) までストール。V-BLANK 中は自由。
- **VRAM への長い LDIR (840B) は V-BLANK をはみ出す** (~0.3 フレーム、その間割り込み不可)。

### ディスク (QD) / モニタ
- `EXT.ROM $EA0E`: 「QD から次ファイルをロードして実行」の標準チェインロード入口
  (B面の起動はここへの JP で行う。ロード中の書き込みは PC FAE9h として watch に現れる)。
- モニタはソフトリセット時 1038h へ `jp 038Dh` を再書き込み (上記参照)。

---

## 7. MZT / QDF 形式

- MZT: 128 バイトヘッダ (attr=01h, name 17B を 0Dh 埋め, size/load/exec は LE16 ×3 @0x12) + 本体
- エミュレータは `.mzt` を挿入時に QD ブロックへ変換 (BSD 1026B 分割)
- QDF ブロック: A5 + flag + size(LE16) + data + CRC16-ARC、SYNC = 0x16
- A面の PCG 転送は「チャンクテーブル (db plane / dw src / dw dst)」方式で 12 セグメント転送
- B面ゲームはチェインロードで RAM 1200h に読まれるため、A面のメモリ
  (2000h-8B00h の PCG 元データ) は残骸として残る (B面ロードで 2000h-3B73h は上書き)

## 8. 落とし穴集 (過去に実際にハマった点)

1. **sym の値は org 相対**。実アドレス = sym値 + 1200h。
   (`--watch-write` など実アドレスを指定する場面では必ず +1200h すること)
2. **`--dump` は最後の 1 つのみ有効**。複数範囲は `--dump-at` を使うか、
   実行を分ける (決定論的なので結果は同一)。
3. **D000h-EFFFh のダンプは常に 00h**。VRAM 内容は `--ppm` で確認。
4. **PowerShell の `>` リダイレクトは UTF-16LE**。ログは `| Out-File -Encoding utf8` で出す。
5. **watch の PC 報告は「書き込み命令の次の命令」になることがある**
   (`ld (nn),a` なら報告 PC - 3 が命令アドレス)。
6. **並行編集に注意**。別セッション/別 AI がソースや out\ を触ると
   「実行したバイナリ ≠ ディスクのソース」という最悪の混乱になる。
   タイムスタンプ確認 + `tools\checkmzt.py` で実行イメージの整合を取ること。
7. **z80asm 文法**: `defc NAME = expr` (NAME defc = は不可)、16進リテラルは
   先導 0 必須 (`FFh` → `0FFh`)、UTF-8 BOM で invalid character、出力は `-o=file` 形式。
8. **レジスタ契約**: 各サブルーチンのヘッダコメント (入力/出力/破壊) に従う。
   破壊に書かれていないレジスタは保存して戻る規約。
   「LD B,L / LD C,H は BC = HL のバイトスワップ」といった演算系バグは
   watch のレジスタ併記 (HL/BC/DE/SP) で発見できる。
9. **ブレッドクラム (B0EF/B0F0/B0F4/B0F5) は現行ビルドには存在しない** (削除済み)。
   使いたい場合はソースへ再追加すること。docs の古い記述は鵜呑みにしない。
10. **デバッグ用コードの後始末**: 原因確定後は TEMP DEBUG ストアを削除する。

---

## 9. コミット規約

- 両リポジトリとも **Conventional Commits**: `<type>(<scope>): <要約>` (要約は日本語可)
- type: `feat` / `fix` / `docs` / `test` / `refactor` / `perf` / `chore`
- 区切りのいいところ (実装・検証完了時点) でコミット。未コミットの変更を残さない。
- push はユーザー指示時のみ。

---

## 10. 関連ドキュメント

| ドキュメント | 内容 |
|---|---|
| `docs\DEBUG_STATE.md` | デバッグ記録 (§2 ハード仕様詳細, §8 MZT/QDF, §11 確認コマンド, §12 左移動バグ解決) |
| `docs\PROGRESS.md` | 進捗ログ (新しいものが上) |
| `docs\DESIGN.md` | ゲームデザイン仕様 |
| `docs\mz1500_specification\` | MZ-1500 仕様書 (※ Memory_Bank.md はエミュレータ実装と混同あり。実装が正) |
| `C:\tools\mz1500_emulator_csharp\.clinerules` | エミュレータ開発ルール |
| `C:\tools\mz1500_emulator_csharp\docs\` | エミュレータ仕様ドキュメント |



