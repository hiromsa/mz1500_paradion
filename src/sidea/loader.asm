; ============================================================
; 魔境騎士パラディオン - Side A ブートローダ
; (IPL が本ファイルを 2000h にロードし 2000h から実行する)
;
;  1. PCG パターン 24KB を OUT E5h (B/R/G プレーン) 経由で PCG-RAM へ転送
;  2. VRAM モードへ復帰しタイトルと B 面交換メッセージを表示
;  3. キー入力を待ち EXT.ROM の $EA0E (次ファイルロード+実行) へジャンプ
;     → ユーザが B 面へ差し替えて CR を押すとゲーム本体が起動する
; ============================================================
        include "include/mz1500.inc"
        include "include/pcgmap.inc"

        org 2000h

ENTRY:
        di
        ld sp,0BFF0h
        out (PORT_ROM_LOW),a        ; 0000h-0FFFh = モニタ ROM (BIOS 呼び出し用)

        ; ---- PCG データ転送 (チャンクテーブル駆動) ----
        ld hl,PCG_TABLE
PCG_LOOP:
        ld a,(hl)
        or a
        jr z,PCG_DONE               ; 00h = 終端
        out (PORT_PCG_B),a          ; プレーン選択 (1=B 2=R 3=G)
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl                      ; DE = 転送元 (2000h+)
        ld c,(hl)
        inc hl
        ld b,(hl)
        inc hl                      ; BC = 転送先 (D000h/D800h/E000h/E800h)
        push hl                     ; テーブルポインタ退避
        ex de,hl                    ; HL = src
        ld e,c
        ld d,b                      ; DE = dst
        ld bc,0800h                 ; 2KB
        ldir
        pop hl
        jr PCG_LOOP
PCG_DONE:
        out (PORT_PCG_OFF),a        ; PCG バンク解除

        ; ---- VRAM モードへ復帰 + 画面初期化 ----
        out (PORT_VRAM),a           ; D000h-FFFFh = VRAM & I/O
        ld hl,0D000h                ; テキスト+PCG コード+属性をクリア
        ld de,0D001h
        ld bc,0FFFh
        ld (hl),0
        ldir
        ld hl,0D800h                ; テキスト属性: 白文字/黒背景
        ld de,0D801h
        ld bc,03FFh
        ld (hl),070h
        ldir
        ld a,03h
        out (PORT_PRIORITY),a       ; PCG 表示 + PCG 前面

        ; ---- タイトル / メッセージ表示 (MZ ディスプレイコード) ----
        ld hl,0D000h + 6*40 + 9
        ld de,MSG_TITLE
        call PRINT_MSG
        ld hl,0D000h + 13*40 + 9
        ld de,MSG_INSERT_B
        call PRINT_MSG
        ld hl,0D000h + 15*40 + 12
        ld de,MSG_CR
        call PRINT_MSG

        call BIOS_KEYFLUSH
KEYWAIT:
        call BIOS_INKEY             ; キー入力待ち
        or a
        jr z,KEYWAIT
        jp PORT_CHAINLOAD           ; EXT.ROM $EA0E: B面をロードして実行

; ---- HL=VRAM アドレス, DE=文字列(00h終端, MZディスプレイコード) ----
PRINT_MSG:
        ld a,(de)
        or a
        ret z
        ld (hl),a
        inc hl
        inc de
        jr PRINT_MSG

; ---- MZ ディスプレイコード (A=01h..Z=1Ah, 空白=00h) ----
MSG_TITLE:      dm 0Dh,01h,0Bh,19h,0Fh,15h,00h,0Bh,09h,13h,08h,09h,00h
                dm 10h,01h,12h,01h,04h,09h,0Fh,0Eh,00h
MSG_INSERT_B:   dm 10h,0Ch,05h,01h,13h,05h,00h,09h,0Eh,13h,05h,12h,14h,00h
                dm 13h,09h,04h,05h,00h,02h,00h
MSG_CR:         dm 01h,0Eh,04h,00h,10h,12h,05h,13h,13h,00h,03h,12h,00h
                dm 0Bh,05h,19h,00h

        align 8
PCG_TABLE:
        include "sidea/pcg_data.asm"
