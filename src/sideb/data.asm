; ============================================================
; データ: ステージテーブル / メッセージ / 各種テーブル
; ============================================================

; ---- フィールド色 (PCG 3bit) ----
; スプライトの透過色 (黒) をこの色へ置換して地形に馴染ませる
; (video.asm sprite_recolor_field)。地面タイルの主色に合わせること
defc FLD_CLR_FOREST = 4   ; 緑 (魔界の森の草原)
defc FLD_CLR_ROCK = 1     ; 青 (岩場の石畳)
defc FLD_CLR_GRAVE = 4    ; 緑 (墓地の草)
defc FLD_CLR_VOLCANO = 2  ; 赤 (火山の焦げ地)
defc FLD_CLR_CASTLE = 1   ; 青 (幻魔城の石畳)

; ---- ステージ定義 (16 バイト / 面) ----
; +0 スクロール間隔 +1 spawn間隔 +2/3 ボス出現フレーム +4 ボスHP
; +5 ボス攻撃間隔 +6/7 マップ行テーブル +8 行数 +9/A BGM +B/C SE射撃
; +D/E SE爆発 +F フィールド色 (スプライト透過色の置換先)
; スクロール間隔 17/14 は旧値 (12/10) の約 70% 速度
STAGE_TABLE:
; --- Stage 1: 魔界の森 ---
        db 17
        db 90
        dw 2700
        db 24
        db 90
        dw MAP_ROWS_S1
        db 22                          ; 11 tile rows x 2 character rows
        dw BGM_FIELD1
        dw SE_SHOT
        dw SE_EXPL
        db FLD_CLR_FOREST
; --- Stage 2: 荒涼たる岩場 ---
        db 17
        db 75
        dw 3000
        db 32
        db 80
        dw MAP_ROWS_S2
        db 22
        dw BGM_ROCK
        dw SE_SHOT
        dw SE_EXPL
        db FLD_CLR_ROCK
; --- Stage 3: 呪われた墓地 ---
        db 14
        db 65
        dw 3300
        db 40
        db 70
        dw MAP_ROWS_S3
        db 22
        dw BGM_FIELD2
        dw SE_SHOT
        dw SE_EXPL
        db FLD_CLR_GRAVE
; --- Stage 4: 灼熱の火山 ---
        db 14
        db 55
        dw 3600
        db 48
        db 60
        dw MAP_ROWS_S4
        db 22
        dw BGM_FIELD2
        dw SE_SHOT
        dw SE_EXPL
        db FLD_CLR_VOLCANO
; --- Stage 5: 幻魔城・最上階 ---
        db 14
        db 48
        dw 3900
        db 56
        db 50
        dw MAP_ROWS_S5
        db 22
        dw BGM_FIELD2
        dw SE_SHOT
        dw SE_EXPL
        db FLD_CLR_CASTLE

defc STAGE_LEN = 16

; ---- ボス PCG 先頭コード表 (stage.asm stage_flow がステージ番号で参照) ----
BOSS_CODE_TBL:
        db SP_BOSS1_0                   ; Stage 1: 大樹の魔物トレント
        db SP_BOSS2_0                   ; Stage 2: ストーンゴーレム
        db SP_BOSS3_0                   ; Stage 3: デスサイズ
        db SP_BOSS4_0                   ; Stage 4: 炎の魔竜ファイアドラゴン
        db SP_BOSS5_0                   ; Stage 5: 幻魔王ダークロード

; ---- スプライト透過色置換対象 (video.asm sprite_recolor_field 参照) ----
;   bank / 開始コード / コード数 — 定義済み PCG の範囲だけを走査する
SPRC_TBL:
        db 1, 000h, 042h                ; bank1: 自機/弾/爆発/アイテム 00h-41h
        db 2, 000h, 034h                ; bank2: 雑魚 6 種 + 宝箱 00h-33h
        db 3, 000h, 031h                ; bank3: ボス1 + ボス5 形態1 00h-30h
        db 3, 040h, 011h                ; bank3: ボス2 40h-50h
        db 3, 080h, 011h                ; bank3: ボス3 80h-90h
        db 3, 0A0h, 011h                ; bank3: ボス5 形態2 A0h-B0h
        db 3, 0C0h, 020h                ; bank3: ボス4 C0h-DFh
        db 0                            ; 終端
; --- 復元データ (pcg_restore.asm) の src 先頭 (SPRC_TBL エントリ順に対応) ---
SPRC_SRC:
        dw RF_SEG_B1                    ; bank1: 自機/弾/爆発/アイテム
        dw RF_SEG_B2                    ; bank2: 雑魚 6 種 + 宝箱
        dw RF_SEG_B3                    ; bank3: ボス1 + ボス5 形態1
        dw RF_SEG_B3                    ; bank3: ボス2
        dw RF_SEG_B3                    ; bank3: ボス3
        dw RF_SEG_B3                    ; bank3: ボス5 形態2
        dw RF_SEG_B3                    ; bank3: ボス4

; ---- 各種テーブル ----
PWUP_TBL:       db SP_PW_TWIN, SP_PW_SPEED, SP_PW_SHIELD, SP_PW_LIFE
; 16x16 destructible terrain tile codes (all four 8x8 quadrants per tile)
BRK_TABLE:      db 094h,095h,096h,097h, 0ACh,0ADh,0AEh,0AFh
                db 0C4h,0C5h,0C6h,0C7h, 0DCh,0DDh,0DEh,0DFh
                db 0F4h,0F5h,0F6h,0F7h
defc BRK_CNT = 20
; 破壊したタイルの跡地に敷く地面タイル (面順, 左上コード)
GRND_TBL:       db T_S1_GRASS, T_S2_GROUND, T_S3_GROUND, T_S4_GROUND, T_S5_FLOOR
SINE16:         db 0,6,11,16,19,21,22,22,22,21,19,16,11,6,0,0
STAGE_MSGS:     dw MSG_STG1, MSG_STG2, MSG_STG3, MSG_STG4, MSG_STG5

; ---- メッセージ (MZ ディスプレイコード) ----
; A=01h..Z=1Ah, 空白=00h, 数字=20h+n, 終端=0FFh (show_msg の仕様)
; ※スコア欄ラベル (LBL_xxx) は print_msg 用のため 00h 終端のまま
LBL_SCORE:
        db 13h,03h,0Fh,12h,05h,00h
LBL_HI:
        db 08h,09h,00h
LBL_REST:
        db 12h,05h,13h,14h,00h
LBL_STAGE:
        db 13h,14h,01h,07h,05h,00h
MSG_START:
        db 07h,01h,0Dh,05h,00h,13h,14h,01h,12h,14h,0FFh
MSG_READY:
        db 12h,05h,01h,04h,19h,0FFh
MSG_STG1:
        db 13h,14h,01h,07h,05h,00h,21h,0FFh
MSG_STG2:
        db 13h,14h,01h,07h,05h,00h,22h,0FFh
MSG_STG3:
        db 13h,14h,01h,07h,05h,00h,23h,0FFh
MSG_STG4:
        db 13h,14h,01h,07h,05h,00h,24h,0FFh
MSG_STG5:
        db 13h,14h,01h,07h,05h,00h,25h,0FFh
MSG_GAMEOVER:
        db 07h,01h,0Dh,05h,00h,0Fh,16h,05h,12h,0FFh
MSG_CONT:
        db 10h,15h,13h,08h,00h,03h,00h,0Bh,05h,19h,0FFh
MSG_CLEAR:
        db 13h,14h,01h,07h,05h,00h,03h,0Ch,05h,01h,12h,0FFh
MSG_ITWIN:
        db 14h,17h,09h,0Eh,00h,13h,08h,0Fh,14h,0FFh
MSG_ISPEED:
        db 13h,10h,05h,05h,04h,00h,15h,10h,0FFh
MSG_ISHIELD:
        db 13h,08h,09h,05h,0Ch,04h,0FFh
MSG_ILIFE:
        db 21h,00h,15h,10h,0FFh
MSG_END1:
        db 14h,08h,05h,00h,04h,05h,0Dh,0Fh,0Eh,00h,0Bh,09h,0Eh,07h,00h,09h,13h,00h,04h,05h,06h,05h,01h,14h,05h,04h,0FFh
MSG_END2:
        db 14h,08h,05h,00h,0Fh,12h,02h,00h,0Fh,06h,00h,0Ch,09h,07h,08h,14h,00h,09h,13h,00h,02h,01h,03h,0Bh,0FFh
MSG_END3:
        db 10h,05h,01h,03h,05h,00h,12h,05h,14h,15h,12h,0Eh,13h,00h,14h,0Fh,00h,14h,08h,05h,00h,0Bh,09h,0Eh,07h,04h,0Fh,0Dh,0FFh
MSG_END4:
        db 14h,08h,01h,0Eh,0Bh,00h,19h,0Fh,15h,00h,06h,0Fh,12h,00h,10h,0Ch,01h,19h,09h,0Eh,07h,0FFh
