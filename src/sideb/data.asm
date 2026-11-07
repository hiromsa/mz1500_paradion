; ============================================================
; データ: ステージテーブル / メッセージ / BGM / SE
; ============================================================

; ---- ステージ定義 (16 バイト / 面) ----
; +0 scroll間隔 +1 spawn間隔 +2/3 ボス出現フレーム +4 ボスHP
; +5 ボス攻撃間隔 +6/7 マップ行テーブル +8 行数 +9/A BGM +B/C SE射撃 +D/E SE爆発 +F 地形
STAGE_TABLE:
; --- Stage 1: 魔界の森 ---
        db 12
        db 90
        dw 2700
        db 24
        db 90
        dw MAP_ROWS_S1
        db 22                          ; 11 tile rows x 2 character rows
        dw BGM_FIELD1
        dw SE_SHOT
        dw SE_EXPL
        db T_S1_GRASS
; --- Stage 2: 荒涼たる岩場 ---
        db 12
        db 75
        dw 3000
        db 32
        db 80
        dw MAP_ROWS_S2
        db 22
        dw BGM_ROCK
        dw SE_SHOT
        dw SE_EXPL
        db T_S2_GROUND
; --- Stage 3: 呪われた墓地 ---
        db 10
        db 65
        dw 3300
        db 40
        db 70
        dw MAP_ROWS_S3
        db 22
        dw BGM_FIELD2
        dw SE_SHOT
        dw SE_EXPL
        db T_S3_GROUND
; --- Stage 4: 灼熱の火山 ---
        db 10
        db 55
        dw 3600
        db 48
        db 60
        dw MAP_ROWS_S4
        db 22
        dw BGM_FIELD2
        dw SE_SHOT
        dw SE_EXPL
        db T_S4_GROUND
; --- Stage 5: 幻魔城・最上階 ---
        db 10
        db 48
        dw 3900
        db 56
        db 50
        dw MAP_ROWS_S5
        db 22
        dw BGM_FIELD2
        dw SE_SHOT
        dw SE_EXPL
        db T_S5_FLOOR

defc STAGE_LEN = 16

; ---- 各種テーブル ----
PWUP_TBL:       db SP_PW_TWIN, SP_PW_SPEED, SP_PW_SHIELD, SP_PW_LIFE
; 16x16 destructible terrain tile codes (all four 8x8 quadrants per tile)
BRK_TABLE:      db 094h,095h,096h,097h, 0ACh,0ADh,0AEh,0AFh
                db 0C4h,0C5h,0C6h,0C7h, 0DCh,0DDh,0DEh,0DFh
                db 0F4h,0F5h,0F6h,0F7h
defc BRK_CNT = 20
SINE16:         db 0,6,11,16,19,21,22,22,22,21,19,16,11,6,0,0
STAGE_MSGS:     dw MSG_STG1, MSG_STG2, MSG_STG3, MSG_STG4, MSG_STG5

; ---- メッセージ (MZ ディスプレイコード: A=01h..Z=1Ah, 空白=00h, 数字=20h+) ----
LBL_SCORE:
        db 13h,03h,0Fh,12h,05h,00h
LBL_HI:
        db 08h,09h,00h
LBL_REST:
        db 12h,05h,13h,14h,00h
LBL_STAGE:
        db 13h,14h,01h,07h,05h,00h
MSG_STG1:
        db 13h,14h,01h,07h,05h,00h,21h,00h
MSG_STG2:
        db 13h,14h,01h,07h,05h,00h,22h,00h
MSG_STG3:
        db 13h,14h,01h,07h,05h,00h,23h,00h
MSG_STG4:
        db 13h,14h,01h,07h,05h,00h,24h,00h
MSG_STG5:
        db 13h,14h,01h,07h,05h,00h,25h,00h
MSG_GAMEOVER:
        db 07h,01h,0Dh,05h,00h,0Fh,16h,05h,12h,00h
MSG_CONT:
        db 10h,12h,05h,13h,13h,00h,03h,00h,0Bh,05h,19h,00h,14h,0Fh,00h,03h,0Fh,0Eh,14h,09h,0Eh,15h,05h,00h
MSG_CLEAR:
        db 13h,14h,01h,07h,05h,00h,03h,0Ch,05h,01h,12h,00h
MSG_END1:
        db 14h,08h,05h,00h,04h,05h,0Dh,0Fh,0Eh,00h,0Bh,09h,0Eh,07h,00h,09h,13h,00h,04h,05h,06h,05h,01h,14h,05h,04h,00h
MSG_END2:
        db 14h,08h,05h,00h,0Fh,12h,02h,00h,0Fh,06h,00h,0Ch,09h,07h,08h,14h,00h,09h,13h,00h,02h,01h,03h,0Bh,00h
MSG_END3:
        db 10h,05h,01h,03h,05h,00h,12h,05h,14h,15h,12h,0Eh,13h,00h,14h,0Fh,00h,14h,08h,05h,00h,0Bh,09h,0Eh,07h,04h,0Fh,0Dh,00h
MSG_END4:
        db 14h,08h,01h,0Eh,0Bh,00h,19h,0Fh,15h,00h,06h,0Fh,12h,00h,10h,0Ch,01h,19h,09h,0Eh,07h,00h
