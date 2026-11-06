; ============================================================
; 魔境騎士パラディオン - Side B ゲーム本体 (定義部)
; (EXT.ROM $EA0E が本ファイルを 1200h にロードし 1200h から実行)
;
; モジュール構成 (include 順):
;   code.asm    エントリ / メインループ / 全体初期化
;   stage.asm   ステージ初期化 / 道中進行 / エンディング
;   field.asm   プレイフィールド補充 / スクロール
;   player.asm  自機 (移動 / 発射 / 被弾)
;   shot.asm    自弾 / 敵弾
;   enemy.asm   敵移動 / スポーン / 撃破
;   item.asm    パワーアップ
;   fx.asm      爆発
;   boss.asm    ボス
;   collide.asm 当たり判定
;   game.asm    状態ディスパッチ
;   ui.asm      スコア / メッセージ
;   util.asm    共通ユーティリティ (タイマ / スロット検索 / 乱数)
;   video.asm   ビデオプリミティブ (V-BLANK / 描画 / 消去)
;   render.asm  オブジェクト / ボス / スコア欄 描画パス
;   input.asm   キー入力
;   sound.asm   サウンドドライバ
;   data.asm / map_data.asm / sound_data.asm   データ
;
; 各サブルーチンは先頭コメントに入力 / 出力 / 破壊するレジスタを明記。
; 原則: 「破壊」に書かれていないレジスタは内容を保存して戻る。
; ============================================================
        include "include/mz1500.inc"
        include "include/pcgmap.inc"

        org 1200h

; ---------------- ワークエリア ----------------
defc W_TICK = WORK_BOTTOM + 000h   ; ISR フレームカウンタ
defc W_KEYS = WORK_BOTTOM + 001h   ; bit0=上 1=下 2=左 3=右 4=射撃 5=CR 6=C
defc W_KEYS_PREV = WORK_BOTTOM + 002h
defc W_STATE = WORK_BOTTOM + 003h   ; ST_xxx
defc W_STAGE = WORK_BOTTOM + 004h   ; 1-5
defc W_SCORE = WORK_BOTTOM + 005h   ; BCD 3 バイト
defc W_HISCORE = WORK_BOTTOM + 008h   ; BCD 3 バイト
defc W_LIVES = WORK_BOTTOM + 00Bh
defc W_SCROLLCNT = WORK_BOTTOM + 00Ch
defc W_SCROLLINT = WORK_BOTTOM + 00Dh
defc W_PLAYTIMER = WORK_BOTTOM + 00Eh   ; 2B ボス出現までのフレーム
defc W_SPAWNCNT = WORK_BOTTOM + 010h
defc W_SPAWNINT = WORK_BOTTOM + 011h
defc W_MAPROW = WORK_BOTTOM + 012h   ; 次に補充するマップ行インデックス
defc W_STAGETBL = WORK_BOTTOM + 013h   ; 2B ステージ定義テーブル
defc W_MAPROWS = WORK_BOTTOM + 015h   ; 2B マップ行テーブル先頭
defc W_MAPCNT = WORK_BOTTOM + 017h   ; 行テーブル行数
defc W_MSGTIMER = WORK_BOTTOM + 018h   ; メッセージ表示残りフレーム (2B)
defc W_MSGTXT = WORK_BOTTOM + 01Ah   ; 2B 表示中メッセージ (VRAM上の実体)
defc W_PLRSPD = WORK_BOTTOM + 01Ch   ; 自機移動量 (2 or 4)
defc W_PLRTWIN = WORK_BOTTOM + 01Dh   ; ツインショット
defc W_PLRSHIELD = WORK_BOTTOM + 01Eh   ; シールド
defc W_PLRINV = WORK_BOTTOM + 01Fh   ; 無敵残り
defc W_PLRCD = WORK_BOTTOM + 020h   ; 射撃クールダウン
defc W_PREVSTATE = WORK_BOTTOM + 021h
defc W_BOSSHP = WORK_BOTTOM + 022h
defc W_BOSSFIRE = WORK_BOTTOM + 023h
defc W_BOSSFIREINT = WORK_BOTTOM + 024h
defc W_BOSSMODE = WORK_BOTTOM + 025h   ; 0=進入 1=戦闘 2=形態2
defc W_SCROLLEDUE = WORK_BOTTOM + 026h   ; 1=render 先頭でスクロール実行
defc W_STATDIRTY = WORK_BOTTOM + 027h   ; 1=スコア欄再描画
defc W_SESHOT = WORK_BOTTOM + 028h   ; 2B SE(射撃) ストリーム
defc W_SEEXPL = WORK_BOTTOM + 02Ah   ; 2B SE(爆発) ストリーム
defc W_BOSS = WORK_BOTTOM + 030h   ; ボス O_S 構造 (8B)
defc W_UPMARK = WORK_BOTTOM + 038h   ; 1UP 済みの万位バイト
defc W_RAND = WORK_BOTTOM + 03Ah     ; 乱数保持
defc W_SCRATCH = WORK_BOTTOM + 03Ch   ; 2B 判定用一時ポインタ
defc W_SCRATCH2 = WORK_BOTTOM + 03Eh   ; 2B 一時座標 (x2,y)
; オブジェクトテーブル: 20 スロット x 8 バイト
;  +0 状態(0=空) +1 attr(bit0=anim bit1=1x1) +2 x +3 y +4 code +5 t +6/7 描画セル
defc O_TBL = WORK_BOTTOM + 040h
defc O_SLOTS = 20
defc O_LEN = 8
defc O_PLAYER = 0
defc O_SHOTS = 1                    ; 1-4
defc O_ESHOTS = 5                    ; 5-8
defc O_ENEMIES = 9                    ; 9-14
defc O_PWUPS = 15                   ; 15-16
defc O_EXPLS = 17                   ; 17-19
defc W_WORKTOP = O_TBL + O_SLOTS * O_LEN

defc ST_FIELD = 0
defc ST_BOSS = 1
defc ST_CLEAR = 2
defc ST_DEATH = 3
defc ST_GAMEOVER = 4
defc ST_ENDING = 5

        include "sideb/code.asm"
        include "sideb/stage.asm"
        include "sideb/field.asm"
        include "sideb/player.asm"
        include "sideb/shot.asm"
        include "sideb/enemy.asm"
        include "sideb/item.asm"
        include "sideb/fx.asm"
        include "sideb/boss.asm"
        include "sideb/collide.asm"
        include "sideb/game.asm"
        include "sideb/ui.asm"
        include "sideb/util.asm"
        include "sideb/video.asm"
        include "sideb/render.asm"
        include "sideb/input.asm"
        include "sideb/sound.asm"
        include "sideb/data.asm"
        include "sideb/map_data.asm"
        include "sideb/sound_data.asm"
