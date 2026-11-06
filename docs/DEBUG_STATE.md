# 魔境騎士パラディオン デバッグ記録

このドキュメントは、MZ-1500向け自作シューティング「魔境騎士パラディオン」の
デバッグ記録である。割り込み方式に関する古い記録は履歴として残し、現在は
V-BLANK同期のメインループからサウンドを更新する方式に変更済み (2026-11-07)。

---

## 0. 一言サマリー

**再発していたフリーズは、サウンド割り込みからの復帰後にモニタへ逸脱する問題だった。
8253/IM1の割り込み経路を廃止し、フレームループ内でサウンド更新を行うことで解消。
`shot_hit_bg` のフィールド外分岐にあったpush/pop不整合も修正した。
QD 2段階起動で3600フレーム動作し、サウンド出力も確認済み。**

---

## 1. プロジェクト構成

| 項目 | 内容 |
|---|---|
| ゲームプロジェクト | c:\tools\mz1500action |
| エミュレータ (C#) | C:\tools\mz1500_emulator_csharp (GUI + CLI。CLI はデバッグ用拡張済) |
| アセンブラ | z88dk z80asm (C:\z88dk\bin) |
| ROM | C:\tools\mz1500_emulator_csharp\romsample\{IPL,EXT,FONT}.ROM |
| 実証済みリファレンス | qdfsample\MeikyuEnoTobiraA/B.qdf (2面ディスクロードの実サンプル。解析済みは tmp\parsed\) |

### ビルド & 実行
`powershell
# ビルド (PCG生成 → z80asm → MZTパック)
cd c:\tools\mz1500action
powershell -ExecutionPolicy Bypass -File build.ps1
# → out\ParadionA.mzt (A面: ローダ+PCG 24KB, load/exec 2000h)
# → out\ParadionB.mzt (B面: ゲーム本体, load/exec 1200h)

# E2E テスト (A面起動 → 700fでB面差し替え → 900fでCR → ゲーム開始)
cd C:\tools\mz1500_emulator_csharp
dotnet run --project src\Mz1500.Cli -c Release --no-build --
  --roms romsample
  --qd c:\tools\mz1500action\out\ParadionA.mzt
  --qd-swap c:\tools\mz1500action\out\ParadionB.mzt@700
  --key 0D@900 --frames 3600 --no-text
  --ppm c:\tools\mz1500action\out\frame.ppm --wav c:\tools\mz1500action\out\game.wav
`
- ゲームはフレーム ~969 頃に開始 (IPLロード ~240f + メッセージ + CR待ち + チェインロード)。
- --key 0D@900 は CR。--key は複数指定可 (16進仮想キーコード or 1文字)。
- --qd-swap FILE@frame は実行中ディスク差し替え (CLIに追加した機能)。
- --watch-write ADDR(16進) は指定アドレスへの書き込みを (frame, PC, value) でログ (最大60件、同PC連続は重複排除←**改善の余地**)。


---

## 2. 確立済みのハードウェア知識 (エミュレータの実装/テストと突き合わせ済み)

**※ 注意: `docs\mz1500_specification\Memory_Bank.md` の E0h-E3h の説明は実装と混同がある。
エミュレータ (`Mz1500Memory.cs`) とそのテストが正。以下は実装準拠:**

- OUT E0h: 0000h-0FFFh → RAM / OUT E2h: → モニタROM (BIOS呼び出しには E2h 状態が必要)
- OUT E1h: D000h-FFFFh → RAM / OUT E3h: → VRAM & I/O (**通常はこちら**)
- OUT E5h,n: PCG プレーン選択 (1=B 2=R 3=G, 0=CG ROM) / OUT E6h: PCG解除
- VRAM: D000=テキストコード, D400=PCGコード, D800=テキスト属性, DC00=PCG属性 (bit3=表示, bit7-6=バンク)
- PCG パターン実体: プレーンp・セルc = PCGRAM[p*2000h + c*8 .. +7]
  (エミュレータ TextScreenRenderer: pcgCode = (D400byte<<3) | ((attr&0xC0)<<5))
- 優先度 OUT F0h (03h = PCG表示+PCG前面) / パレット F1h (未使用=恒等)
- V-BLANK: 8255 ポートC (E002) **bit7 = 0 の間** (走査線199-261, 約14,100T/フレーム)
  - **E002 を読むには 8255 を PC 入力モードにする必要あり: E003h に 8Bh を書く**
    (PA=out PB=in PC=in。モニタは PC を出力のままにするため、書かないと bit7 読みが壊れる)
- キーボード: E000 にストローブ (下位4bit=桁0-9), E001 を読む (押下 bit=0)
  - 桁7: bit2=← bit3=→ bit4=↓ bit5=↑ / 桁0: bit0=CR / 桁6: bit4=SPACE / 桁4: bit5=C
- サウンド割り込み (**旧方式・現在不使用**):
  - 旧実装は IM1 + RAMフック1038h + 8253 ch1/ch2 + 8255 PC2ゲートを使用。
  - 割り込み復帰後にモニタへ逸脱する再発を確認したため、現在はPC2ゲートを閉じ、
    割り込みを使わずメインループから `sound_update` を1フレームに1回呼び出す。
  - BGM/SEと `W_TICK` はこの更新で進行する。
- PSG: OUT E9h = 両チャンネル同時 (F2h=左, F3h=右)。SN76489AN 形式
- CPU ウェイト: 表示期間 (各走査線クロック0-159) 中の VRAM/PCG アクセスは H-BLANK (クロック160/165) までストール。
  V-BLANK 中は自由。**VRAM への長い LDIR (840B) は V-BLANK をはみ出す (~0.3フレーム、その間割り込み不可)**
- EXT.ROM $EA0E: 「QD から次ファイルをロードして実行」の標準チェインロード入口
- モニタはソフトリセット時 1038h に `jp 038Dh` (ブリンクハンドラ) を再書き込みする
---

## 3. 現在の動作状況 (ここまで動いているもの)

1. **2段階QDロード完全動作**: A面ロード → PCG転送 (OUT E5h でB/R/Gプレーンへ計24KB) →
   タイトル+「B面挿入」メッセージ表示 → CR待ち → **JP $EA0E** でB面をロードしてゲーム開始
2. **フレーム更新**: メインループの `sound_update` でBGM/SEとtickを更新
3. **描画**: 森タイル背景 (PPM緑ピクセル多数を確認)、ステータスバー "SCORE HI REST STAGE" 正常表示、
   自機 (中央 x2=76,y=140)、弾 (SPACEで発射、上昇を実測: B048h スロット = 01 4A 4E 50...)
4. **入力**: 矢印/SPACE/CR のビットが正しく立つ (モードワード 8Bh 修正後)
5. **BGM**: メインループ更新で60秒 WAV にPSG音出力を確認
6. **安定動作区間**: QD 2段階起動から3600フレームまで正常動作

---

## 4. 過去のフリーズ記録 (2026-11-07 解決)

以下の症状・ブレッドクラム・仮説は修正前の調査記録。原因はサウンドISR復帰後のモニタ逸脱で、
ハードウェア割り込みを廃止してメインループから `sound_update` を呼ぶ方式に変更した。
また `shot_hit_bg` のフィールド外分岐にあったpush/pop不整合も修正。
QD A→B差し替えで3600フレーム動作し、tick/ステージタイマ進行と60秒PSG WAVを確認済み。

### 症状
- **ゲーム tick が特定値 (実行毎に 80〜530 とばらつく) に達するとフリーズする**
- フリーズ後の状態 (RAMダンプ B000h-B005h + ブレッドクラム B0EEh-B0F5h):
  - `W_TICK`(B000) 凍結、`W_KEYS`(B001) に**存在し得ない値 (40h/21h/C4h)** = ワイルドライトの痕跡
  - `W_STATE`(B003) が 00 だったり 03 だったり (実行毎に異なる)
  - フリーズ後はさらに **JP 0000 → IPL リブート → B面自動再ロード → ゲーム再起動** の
    サイクルに入ることがある (tick がリセットされて再カウントされる)
  - エミュレータ CLI の最終 PC は ROM 内 (0616h / 02DEh / 09E7h など = モニタのアイドル・
    INKEY待ち・E008テンポポーリング) → **暴走ジャンプが ROM に着地した痕跡**
- クラッシュ→リブート→自動ロードのサイクルで「一見動いているように見える」ため、
  長時間実行の tick 値比較では見かけ上不規則な増減に見える (**mod 256 に注意**)

### フリーズ時点のブレッドクラム (最新ビルド・実測値)
| セル | 意味 | フリーズ時の値 |
|---|---|---|
| B0F0 | メインループ段階 (1=wait_vb 2=render 3=wait_vb_end 4=game_tick 5=完了) | **02 (render_objects 内)** または 04/00 |
| B0EF | レンダ段階 (2A=消去 2B=ボス消去 2C=スクロール 2D=描画 2E=ボス描画 2F=ステータス 46-49=PLAIN経路) | **2C (do_scroll_shift 後) や 49 など** |
| B0F5 | GK_FIELD段階 (40=入口 41=player 42=scroll 43=spawn 44=shots 45=eshots 46=enemies 47=pwups 48=expls 49=collide 4A=stage_flow 4B=msgs) | **40/49/4B など実行毎に異なる** |

- B0F0=02 と B0F5=40 の組合せ (render 中なのに GK は入口) は整合しない →
  **ブレッドクラム自体がワイルドライトで破壊されている可能性が高い**
- B0EF=2C (do_scroll_shift 通過後) や 49 (collide_field) の時もあり、固定点ではない

### 重要な実測事実
- **`--watch-write B001` の結果: 1450フレームで B001 への書き込みは 1 回のみ**
  (frame 971, PC 16F6h = read_keys の `ld (W_KEYS),a`)
  → ただしウォッチログは「同一PC連続書き込みを重複排除」するため、
  tick が進んでいた事実と矛盾する。**重複排除を (PC,value) ベースに変更するか無効化して再調査すること**
- フリーズ確定フレームの直前まで tick は 1/フレームで正常増加

---

## 5. 修正前の主な仮説 (履歴)

| # | 仮説 | 確認方法 |
|---|---|---|
| H1 | **1038h フック破壊**: snd_init が 1038h に `C3`,`sound_isr` を書く。モニタはリブート時に `jp 038Dh` を再書き込みする。ゲーム中に誰かが 1038h を上書きすると次の INT で暴走 (IM1 なので RST38→1038h は毎フレーム通過) | フリーズ後 `--dump 1038,3` で `C3 xx xx` が残っているか確認。`--watch-write 1038` と `1039` で書き込み PC を特定 |
| H2 | **敵のバウンド アンダーフロー**: `EN_DXL: dec a / jp m,EN_DXS2` が x2=FFh を格納 → col 63 → CELLADDR が行の境界を跨いで VRAM/ミラー末尾 (B770-B7FF, D780-D7FF) に書く。直接クラッシュではなくミラー/ステータス領域破壊が後続で悪化する可能性 | EN_DX 系を x2=[4,152] にクランプして再試行 |
| H3 | **fill_row の行ラップ**: W_MAPROW が 8→0 で `dec a` → FFh → ソース = マップベース+10200B = イメージ外読み取り。クラッシュではなくゴミ行描画だが修正候補 | fill_row を「現インデックスを使用→次を計算」形式に書き換え (dec a を排除) |
| H4 | **チェインロード後の SIO 割り込み残留**: $EA0E の QD ドライバは SIO 割り込みを使用。ロード完了後のディスク停止 (DCD 変化) で SIO INT。IM1+フック (sound_isr) に飛ぶだけなら無害のはずだが未検証 | snd_init 先頭に SIO リセット (chA/chB に 18h, WR1=0) を戻して比較 |
| H5 | **expls_update とレンダ側 anim の二重適用** (attr bit0 のレンダ側アニメ + expls_update 側 code 計算) — 表示破れのみでクラッシュではない | 観察 |
| H6 | **8253 ch2 再アームと ch1 エッジの位相ずれ**: 実レート 0.66〜1.0/フレームで変動。フリーズとは無関係と考えられるが BGM テンポの揺らぎ要因 | ch1=87 固定で現在は実用上問題なし |
| H7 | **スタック**: SP=BF00。ISR+呼び出し深さは最大 ~40B。BF00 より上 (BF01+) は未使用領域 | — |

---

## 6. 過去に修正したバグ (再発防止の参考記録)

1. z80asm 文法: `defc NAME = expr` 形式 (NAME defc = は不可)、16進リテラルは先導0必須 (FFh→0FFh)、
   UTF-8 BOM で「invalid character」、出力オプションは `-o=file` 形式
2. 8255 モードワード: 8Bh (PA出力/PB入力/PC入力)。89h だと PB が出力モードでキー読みが全ビット立つ (7Fh)
3. 割り込み方式の履歴: PIO+IM2 (GALAGA方式) はIPLブート環境下で動作せず、IM1+1038hフック方式を試行。
   後にISR復帰時のモニタ逸脱が判明し、現在は割り込みを使わないフレーム更新へ変更。
4. RO_D1 描画パスの 2x2→1x1 フォールスルーによる `pop bc` 二重実行 → スタック破壊 (大クラッシュ)
5. ループカウンタ保護: RO_E1/RO_D1 には push bc/pop bc 必要 (ERASE2X2 等が BC 破壊)。
   ただし EVP_L/PUW_L/NVP_L は元々ヘッドで push しているため追加すると二重 push で
   逆にスタック破壊 → 整合済み (patch 履歴に注意)
6. is_breakable が HL を破壊 → 呼び出し側のミラーポインタ消失 → コード領域 (4xxx) へ書き込み → push hl で修正
7. ERASE1X1 の方向が逆 (VRAM読み→ミラー書き) → ミラー破壊 → 修正
8. 敵アニメ計算 (`res 0,e` → `and 1 / add a,a / add a,a`) 修正
9. spawn_eshot_at が DE 未設定でアドレス8付近に書く → 修正
10. X座標 1バイト溢れ → 全座標を 2px 単位 (x2) に変更、col=x2>>2
11. BCD スコア定数 (30/100/5000 を BCD でなく素の数値にしていた) → 030h/0100h/05000h
12. メッセージ表示コードの 10進/16進混在 ("SCORE"→"MLOCE") → 全面 16進化
13. GK_DEATH と msgs_update の W_MSGTIMER 二重減算 → リスポーン 65535 tick 遅延 → msgs_update を GK_DEATH から除去
14. 自機初期 x (152px vs 76 x2単位) 修正
15. エミュレータ CLI 機能追加: `--qd-swap FILE@frame` (ディスク差し替え), 複数 `--key` (同時押し), `--watch-write ADDR` (書き込みウォッチ), `Mz1500Memory.WriteWatch` フック

---

## 7. 修正前の調査メモ (履歴)

以下の再現手順と仮説は修正前のもの。現在の確認には「11. 最終確認コマンド集」を使う。

1. **再現** (確実に再現する):
   ```
   cd C:\tools\mz1500_emulator_csharp
   dotnet run --project src\Mz1500.Cli -c Release --no-build -- `
     --roms romsample --qd c:\tools\mz1500action\out\ParadionA.mzt `
     --qd-swap c:\tools\mz1500action\out\ParadionB.mzt@700 `
     --key 0D@900 --frames 1400 --no-text --dump B000,4 --dump 1038,3 --watch-write B001
   ```
   (確認点: tick=CEh で凍結 / keys=40h 等の異常値 / 1038h が `C3 xx xx`(sound_isr) のままか、
    `C3 8D 03`(モニタ) に戻っていたらリブートが起きた証拠)
2. **--watch-write の重複排除を (PC,value) ベースに変更するか無効化**して、
   read_keys (PC 16F6h) 以外の書き込み手が現れないか全量を見る。特にフリーズ直前 30 フレーム。
   (実装位置: Program.cs の watchLog/lastWatchPc 部分)
3. **1038h (フック) と B0D0-B0E8 (サウンド変数 V_BGM_*/V_SE_*) へのウォッチ**を優先。
   サウンド変数は W_WORKTOP (B0E0) 以降に配置済みでオブジェクトテーブル (B040-B0DF) とは
   非重表格だが、実メモリで確認すること。
4. **サブシステム分離テスト** (game.asm/code.asm を一時修正してフリーズの有無を比較):
   - `spawn_update` を `ret` にして敵なし → 敵経由か判定
   - code.asm `init_stage` 末尾の `jp play_bgm` を止めて無音 → BGM/ISR 経由か判定
   - video.asm `scroll_logic` 無効化 → スクロール経由か判定
   - `enemies_update` を `ret` に → 敵移動/バウンド経由か判定
   いずれかでフリーズが消えれば範囲は絞れる
5. **修正候補の実装メモ**:
   - fill_row ラップ (H3): `ld a,(W_MAPROW) / ld e,a / inc a / cp (W_MAPCNT) / jr nz,+1 / xor a / +1: ld (W_MAPROW),a / ld a,e / …40倍…` 形式に書き換える (dec a を排除)
   - 敵バウンド (H2): x2 が FFh になったら 04h に補正するガードを EN_DX 系に追加
6. **デバッグ用ブレッドクラムは現行ビルドにまだ入っている** (B0F0/B0EF/B0F4/B0F5 への書き込み)。
   原因確定後に削除すること。`src/sideb/{code,game,video}.asm` 内を
   `0B0F0h` / `0B0EFh` / `0B0F4h` / `0B0F5h` で検索。
7. **エミュレータ CLI への追加機能** (--qd-swap / 複数 --key / --watch-write / Mz1500Memory.WriteWatch フック)
   は Cline が追加したもの。`C:\tools\mz1500_emulator_csharp\.clinerules` の規約に従い
   conventional commit でのコミット推奨 (**未コミット**)。

---

## 8. MZT/QDF 形式の知見 (ロード回りをいじる場合)

- MZT: 128バイトヘッダ (attr=01h, name 17B を 0Dh 埋め, size/load/exec は LE16 ×3 @0x12) + 本体
- エミュレータは .mzt を挿入時に QD ブロックへ変換 (BSD 1026B 分割)
- 「迷宮への扉」実サンプルのブロック: A5+flag+size(LE16)+data+CRC16-ARC、SYNC=0x16
- 解析ツール: `tmp\mztparse.py` / `tmp\qdfparse.py`
- A面の PCG 転送は「チャンクテーブル (db plane / dw src / dw dst)」方式で 12 セグメント転送
- B面ゲームはチェインロードで RAM 1200h に読まれるため、A面のメモリ (2000h-8B00h の PCG 元データ) は残骸として残る
  (fill_row の暴走インデックスがここを読んでも「ゴミタイル」になるだけ)

---

## 9. ゲームバランス設計 (実装済みデータの意図)

docs/DESIGN.md 参照。5面 (魔界の森/岩場/墓地/火山/幻魔城)、ボスは面ごとに HP 24/32/40/48/56(+形態2)、
コンティニューは C キー、残機 2、10000点で 1UP。ステージテーブルは data.asm の STAGE_TABLE (16B/面)。
現在は試験用に BGM を共通化 (BGM_FIELD1/2)。

---

## 10. 既知の軽微な問題 (クラッシュ以外・優先度低)

- ~~スクロール時に全オブジェクト再描画のため 1 フレーム当たりの負荷が高く、
  スクロール フレームでは game_tick が詰め込めない (軽い処理落ち)~~ (継続課題)
- ~~敵のアニメコードオフセットが (t>>3)&1 * 4 のため、2フレーム目のパターンが +4 (仕様通りだが要調整)~~ (継続課題)
- ~~ボス描画のセル保存が VRAM アドレス基準 (D400+...) で、BOSS_ERASE はミラー基準 (B400+...) を
  想定している → render_boss_draw が呼ばれると +2000h の補正ずれが起きる可能性 (未発動・要確認)~~
  **確認済み: render_boss_draw が保存時に -2000h 補正しており整合済み。ボス経路の修正不要**
- ~~敵弾の ERASE1X1 がミラーに 10h/11h (弾コード) を書き込む件~~ (修正済み)
  - **2026-11 追加修正**: ERASE1X1 の属性書き込みが `セル+2000h` (F000h領域) に飛んでおり
    旧セルの PCG 属性 (4Ah=バンク1) が残り、通過軌跡がバンク1パターンで描画されていた
    (炎状の残像連鎖・黒い軌跡) → `+0800h` (DC00h 基準) に修正
- **2026-11 追加修正**: スクロール方向の逆転 (地形が下から入る → 上から入る下シフト LDDR 方式へ)
- **2026-11 追加修正**: ERASE2X2 の D レジスタ寿命バグ (BR 値退避なしに `ld de,39` を再ロード →
  自機右下セルへ毎フレーム 00h を書き込み、スクロールで黒列として蓄積)
  → BR 値は書き込み時にミラーから読み直す方式へ
- ジョイスティック未対応 (キーボードのみ)
- BGM は全面共通の暫定曲。tools/musicgen.py (譜面→PSGストリーム生成) が今後の課題

### 10a. 調査用ツール・注意点 (2026-11 追加)

- `tools/ppm2png.py`: CLI の --ppm 出力を PNG 化 (2x 拡大) して画面を確認する
- `tools/dumpanalyze.py`: 2 回の --dump (VRAM/ミラー) を比較解析
  - **注意**: CLI の `--dump` は**最後の 1 つのみ有効** (複数指定不可。複数範囲は複数回実行する)
  - **注意**: PowerShell の `>` リダイレクトは UTF-16LE で出力される (ツール側で自動判別済み)
  - **注意**: `--dump` による D000h-EFFFh (VRAM ウィンドウ) の読み出しは常に 00h を返す
    (Peek 経路の制約)。VRAM の実内容は --ppm か --watch-write で確認すること。
    ミラー (B400h) とワーク (B000h) は正しく読める
- `tools/symlookup.py`: main.sym のシンボルは **org 相対** (実アドレス = 値 + 1200h)。
  --watch-write の PC 報告は「書き込み命令の**次の命令**の PC」になることがある
- `scroll` 関連の検証方法: 1 スクロール間隔 (6f) 差で --dump B400,370 を 2 回取り、
  「後フレームの行 r == 前フレームの行 r-1」を確認すれば下シフト (前進方向) を機械検証できる

---

## 11. 最終確認コマンド集

```powershell
# ビルド
cd c:\tools\mz1500action
powershell -ExecutionPolicy Bypass -File build.ps1

# フリーズ再現 (tick 凍結・keys 異常値を観察)
cd C:\tools\mz1500_emulator_csharp
dotnet run --project src\Mz1500.Cli -c Release --no-build -- `
  --roms romsample --qd c:\tools\mz1500action\out\ParadionA.mzt `
  --qd-swap c:\tools\mz1500action\out\ParadionB.mzt@700 `
  --key 0D@900 --frames 1400 --no-text --dump B000,4 --dump 1038,3 --watch-write B001

# 単体ブート (チェインロードを介さない比較テスト用。B面だけを直接起動)
python c:\tools\mz1500action\tools\mkmzt.py --name "PB" --load 1200 --exec 1200 `
  -o c:\tools\mz1500action\out\testB.mzt c:\tools\mz1500action\out\sideb.bin
dotnet run --project src\Mz1500.Cli -c Release --no-build -- `
  --roms romsample --qd c:\tools\mz1500action\out\testB.mzt --frames 2000 --no-text
```

- ワークエリア主要オフセットは `src\sideb\main.asm` 冒頭の defc 一覧を参照
  (tick=B000, keys=B001, state=B003, stage=B004, score=B005-7, lives=B00B,
   playtimer=B00E/F, O_TBL=B040 (20slot×8B), sound vars=B0E0+)
- ブレッドクラム: B0EF(レンダ段階) B0F0(メイン段階) B0F5(GK段階)

以上。このバグは「動くものを作る」段階は越えており、あとはメモリ破壊源を 1 つ特定するだけの段階まで来ている。
エミュレータのウォッチ機能とブレッドクラムの併用で、数回の実行で犯人が特定できる見込み。
