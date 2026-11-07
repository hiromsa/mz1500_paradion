; ============================================================
; ビデオプリミティブ: V-BLANK 同期 / VRAM 初期化 / セル描画・消去
; (オブジェクトの描画パスは render.asm)
; ============================================================

; ------------------------------------------------------------
; V-BLANK 開始待ち (8255 PC7: 0 = V-BLANK 中)
; 入力: なし
; 出力: V-BLANK 開始までブロック
; 破壊: A, F
; ------------------------------------------------------------
wait_vblank_start:
        ld a,(PPI_PORTC)
        bit 7,a
        jr z,wait_vblank_start          ; まず表示期間まで待つ
WVS1:   ld a,(PPI_PORTC)
        bit 7,a
        jr nz,WVS1                      ; V-BLANK 開始を待つ
        ret

; ------------------------------------------------------------
; V-BLANK 終了待ち
; 入力: なし
; 出力: V-BLANK 終了 (表示期間の先頭) までブロック
; 破壊: A, F
; ------------------------------------------------------------
wait_vblank_end:
        ld a,(PPI_PORTC)
        bit 7,a
        jr z,wait_vblank_end            ; V-BLANK 終了を待つ
        ret

; ------------------------------------------------------------
; VRAM 初期化 (テキスト / PCG コード / 属性クリア + 優先度設定)
; 入力: なし
; 出力: VRAM 全領域クリア, PCG 表示 + PCG 前面, スコア欄初期化
; 破壊: A, B, C, DE, HL, F
; ------------------------------------------------------------
video_init:
        ld hl,VRAM_TEXT                 ; テキスト+PCG コード+属性クリア
        ld de,VRAM_TEXT+1
        ld bc,0FFFh
        ld (hl),0
        ldir
        ld hl,VRAM_ATTR                 ; テキスト属性: 白/黒
        ld de,VRAM_ATTR+1
        ld bc,03FFh
        ld (hl),070h
        ldir
        ld a,03h
        out (PORT_PRIORITY),a           ; PCG 表示 + PCG 前面
        call status_init
        ret

; ------------------------------------------------------------
; スコア欄ラベル + PCG 属性初期化
; 入力: なし
; 出力: 行 23 に SCORE / HI / REST / STAGE ラベルと PCG 属性を設定
; 破壊: A, DE, HL, F
; ------------------------------------------------------------
status_init:
        ld hl,VRAM_TEXT + 23*40 + 0
        ld de,LBL_SCORE
        call print_msg
        ld hl,VRAM_TEXT + 23*40 + 12
        ld de,LBL_HI
        call print_msg
        ld hl,VRAM_TEXT + 23*40 + 21
        ld de,LBL_REST
        call print_msg
        ld hl,VRAM_TEXT + 23*40 + 30
        ld de,LBL_STAGE
        call print_msg
        ; PCG 属性設定 (スコア桁/ハイ/残機/ステージ桁)
        ld hl,0DC00h + 23*40 + 6
        call set_status_attr6
        ld hl,0DC00h + 23*40 + 15
        call set_status_attr6
        ld a,PCGATTR_BANK0
        ld (0DC00h + 23*40 + 26),a      ; ハートアイコン
        ld (0DC00h + 23*40 + 27),a      ; 残機数
        ld (0DC00h + 23*40 + 36),a      ; ステージ数
        ret

; ------------------------------------------------------------
; PCG 属性 6 セル設定 (スコア欄桁用)
; 入力: HL = 設定先 (PCG 属性 VRAM)
; 出力: 6 セルに PCGATTR_BANK0 を書き込み
; 破壊: A, C, F (HL は +6 進む)
; ------------------------------------------------------------
set_status_attr6:
        ld c,6
SSA1:   ld (hl),PCGATTR_BANK0
        inc hl
        dec c
        jr nz,SSA1
        ret

; ------------------------------------------------------------
; 文字列描画 (ディスプレイコード)
; 入力: HL = VRAM 転送先, DE = 文字列 (00h 終端)
; 出力: 00h 直前まで VRAM へ転送
; 破壊: A, DE, HL, F
; ------------------------------------------------------------
print_msg:
        ld a,(de)
        or a
        ret z
        ld (hl),a
        inc hl
        inc de
        jr print_msg

; ------------------------------------------------------------
; セルアドレス計算
; 入力: B = col (0-39), C = row (0-24)
; 出力: HL = VRAM_PCG + row * 40 + col (コード領域アドレス)
; 破壊: DE, HL, F (A, B, C は保存)
; ------------------------------------------------------------
CELLADDR:
        push bc
        ld l,c
        ld h,0
        add hl,hl
        push hl
        add hl,hl
        add hl,hl                       ; 8r
        ld e,l
        ld d,h
        pop hl                          ; 2r
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl                       ; 32r
        add hl,de                       ; 40r
        ld e,b
        ld d,0
        add hl,de
        ld bc,VRAM_PCG
        add hl,bc
        pop bc
        ret

; ------------------------------------------------------------
; 2x2 セル描画 (16x16 ドット)
; 入力: HL = 左上セル (VRAM_PCG 基準), B = 左上コード, C = 属性
; 出力: コード 4 セル + 属性 4 セルを描画
; 破壊: B, DE, HL, F (C は保存)
; ------------------------------------------------------------
DRAW2X2:
        ld (hl),b                       ; TL
        inc b
        inc hl
        ld (hl),b                       ; TR
        push hl
        ld de,39
        add hl,de                       ; BL
        inc b
        ld (hl),b
        inc b
        inc hl
        ld (hl),b                       ; BR
        ; 属性 (DC00 = セル + 800h)
        ld de,0800h
        add hl,de                       ; BR attr
        ld (hl),c
        dec hl
        ld (hl),c                       ; BL attr
        ld de,-40
        add hl,de                       ; TL attr
        ld (hl),c
        inc hl
        ld (hl),c                       ; TR attr
        pop hl
        ret

; ------------------------------------------------------------
; 1x1 セル描画 (8x8 ドット)
; 入力: HL = セル (VRAM_PCG 基準), B = コード, C = 属性
; 出力: コード + 属性を描画
; 破壊: DE, HL, F (B, C は保存)
; ------------------------------------------------------------
DRAW1X1:
        ld (hl),b
        ld de,0800h
        add hl,de
        ld (hl),c
        ret

; ------------------------------------------------------------
; 2x2 セル消去 → 地形コードへ復元
; 入力: HL = 左上ミラーセル (0B400h 基準, 描画時に保存したアドレス)
; 出力: コード 4 セルをミラーから復元, 属性 4 セルを PCGATTR_BANK0 へ
; 破壊: A, B, C, DE, HL, F
; ★注意: 旧実装は BR 値を D に保持したまま `ld de,39` を再ロードし、
;   D が 00h に壊された状態で `ld (hl),d` するため、自機 (2x2) 右下セルに
;   常に 00h (黒) を書き込んでいた (スクロールで黒列として焼き付く)。
;   本実装では BR 値を書き込み時にミラーから直接読み直す。
; ------------------------------------------------------------
ERASE2X2:
        push hl
        ld de,2000h
        add hl,de                       ; VRAM セル
        push hl
        or a
        ld bc,2000h
        sbc hl,bc                       ; ミラーへ戻る
        ld a,(hl)                       ; TL
        inc hl
        ld b,(hl)                       ; TR
        ld de,39
        add hl,de                       ; ミラー BL
        ld c,(hl)                       ; BL
        pop hl                          ; HL = VRAM セル
        ld (hl),a                       ; TL
        inc hl
        ld (hl),b                       ; TR
        ld de,39
        add hl,de                       ; VRAM BL
        ld (hl),c
        inc hl                          ; VRAM BR
        push hl
        ld de,2000h
        or a
        sbc hl,de                       ; ミラー BR
        ld a,(hl)                       ; ★BR 値はここで読む (D レジスタ経由にしない)
        pop hl
        ld (hl),a
        ld de,0800h
        add hl,de                       ; BR attr
        ld (hl),PCGATTR_BANK0
        dec hl
        ld (hl),PCGATTR_BANK0
        ld de,-40
        add hl,de                       ; TL attr
        ld (hl),PCGATTR_BANK0
        inc hl
        ld (hl),PCGATTR_BANK0
        pop hl
        ret

; ------------------------------------------------------------
; 1x1 セル消去 → 地形コードへ復元
; 入力: HL = ミラーセル (0B400h 基準)
; 出力: コードをミラーから復元, 属性を PCGATTR_BANK0 へ
; 破壊: A, DE, HL, F
; ------------------------------------------------------------
ERASE1X1:
        ld de,2000h
        add hl,de                       ; HL = VRAM cell
        push hl
        or a
        ld bc,2000h
        sbc hl,bc                       ; HL = mirror cell
        ld a,(hl)
        pop hl
        ld (hl),a                       ; コード復元
        ld de,0800h                     ; PCG 属性は DC00 基準 = セル + 800h
        add hl,de
        ld (hl),PCGATTR_BANK0
        ret

; ------------------------------------------------------------
; 2x2 セル属性のみ消去 (コード復元なし)
; 入力: HL = 右下セル (VRAM_PCG 基準)
; 出力: 属性 4 セルを PCGATTR_BANK0 へ
; 破壊: DE, HL, F
; ------------------------------------------------------------
ERASEATTR2X2:
        ; HL=BRセル: 属性4セルをバンク0へ戻す
        ld de,0800h
        add hl,de
        ld (hl),PCGATTR_BANK0
        dec hl
        ld (hl),PCGATTR_BANK0
        ld bc,-40
        add hl,bc
        ld (hl),PCGATTR_BANK0
        inc hl
        ld (hl),PCGATTR_BANK0
        ret
; ------------------------------------------------------------
; スプライト PCG の透過色 (黒) をフィールド色へ一括置換
; 入力: A = フィールド色 (PCG 3bit, STAGE_TABLE +F)
; 出力: SPRC_TBL の各範囲 (バンク 1-3) について 3 プレーン全 0 の
;       ピクセルを A 色へ書換え, 終了時に D000h-EFFFh を VRAM & I/O へ戻す
; 破壊: A, B, D, E, IX, F (C, HL は保存)
; 注意: OUT E5h 選択中は VRAM/MMIO (E002 の V-BLANK 読み含む) が
;       見えないため, init_stage の
;       VRAM 転送完了直後 (描画 / メッセージの前) に 1 回だけ呼ぶこと
;       (約 0.5 秒かかるためステージ切替時の一瞬の静止になる)
; ------------------------------------------------------------
sprite_recolor_field:
        ld c,a                          ; C = フィールド色
        ld hl,SPRC_TBL
SRF_BANK:
        ld a,(hl)
        or a
        jr z,SRF_DONE                   ; 終端 (bank = 0)
        push hl                         ; テーブル位置退避
        inc hl
        ld e,(hl)                       ; 開始コード
        inc hl
        ld b,(hl)                       ; コード数
        add a,a
        add a,a
        add a,a                         ; bank * 8
        ld h,a
        ld l,0                          ; HL = bank * 800h
        ld d,0                          ; DE = 開始コード
        sla e
        rl d
        sla e
        rl d
        sla e
        rl d                            ; DE = 開始コード * 8
        add hl,de
        ld de,0D000h
        add hl,de                       ; HL = PCG ウィンドウ上の開始アドレス
        push hl
        pop ix                          ; IX = 走査位置
        pop hl                          ; テーブル位置 (bank バイト) へ戻す
        inc hl
        inc hl
        inc hl                          ; 次のエントリ (bank) へ
SRF_CODE:
        push bc
        ld d,8                          ; 1 文字 = 8 行
SRF_ROW:
        ld a,001h
        out (PORT_PCG_B),a              ; B プレーン選択
        ld e,(ix+0)
        ld a,002h
        out (PORT_PCG_B),a              ; R プレーン選択
        ld a,(ix+0)
        or e                            ; B|R
        ld e,a
        ld a,003h
        out (PORT_PCG_B),a              ; G プレーン選択
        ld a,(ix+0)
        or e                            ; B|R|G
        jr nz,SRF_NROW                  ; 黒でなければ次の行へ
        ; 3 プレーン全 0 (黒) → フィールド色の立っているプレーンだけ FFh
        bit 0,c
        jr z,SRF_W1
        ld a,001h
        out (PORT_PCG_B),a
        ld (ix+0),0FFh
SRF_W1: bit 1,c
        jr z,SRF_W2
        ld a,002h
        out (PORT_PCG_B),a
        ld (ix+0),0FFh
SRF_W2: bit 2,c
        jr z,SRF_NROW
        ld a,003h
        out (PORT_PCG_B),a
        ld (ix+0),0FFh
SRF_NROW:
        inc ix
        dec d
        jr nz,SRF_ROW
        pop bc
        dec b
        jr nz,SRF_CODE
        jr SRF_BANK
SRF_DONE:
        out (PORT_PCG_OFF),a            ; PCG モード解除 (E6h)
        out (PORT_VRAM),a               ; D000h-EFFFh を VRAM & I/O へ戻す
        ret
