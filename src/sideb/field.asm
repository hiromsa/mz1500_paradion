; ============================================================
; プレイフィールド: マップ行補充 / スクロール要求 / 地形シフト
; ============================================================

; ------------------------------------------------------------
; マップ行 1 行分 (40 バイト) を HL に補充
; 入力: HL = 転送先
; 出力: 40 バイト転送完了, W_MAPROW = 次回インデックス (末尾でラップ)
; 破壊: A, B, C, DE, HL, F
; ------------------------------------------------------------
fill_row:
        push hl                         ; 転送先退避
        ld a,(W_MAPROW)                 ; 今回使うインデックス
        ld e,a
        inc a                           ; 次回インデックスを計算
        ld c,a
        ld a,(W_MAPCNT)
        cp c
        jr nz,FR_SET
        ld c,0                          ; 末尾 → 先頭へラップ
FR_SET: ld a,c
        ld (W_MAPROW),a                 ; 次回インデックス
        ld a,e                          ; 今回インデックス (dec によるアンダーフローなし)
        ld l,a
        ld h,0
        add hl,hl                       ; 2r
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
        ld bc,(W_MAPROWS)
        add hl,bc                       ; ソース
        pop de                          ; 転送先
        ld bc,40
        ldir
        ret

; ------------------------------------------------------------
; スクロール要求タイマ
; 入力: なし
; 出力: W_SCROLLCNT を -1, 0 になったら間隔を再セットし W_SCROLLEDUE = 1
;       (実際のシフトは render_objects が消去パスの後に実行する)
; 破壊: A, F
; ------------------------------------------------------------
scroll_logic:
        ld a,(W_SCROLLCNT)
        dec a
        jr nz,SCL_SET
        ld a,(W_SCROLLINT)
        ld (W_SCROLLCNT),a
        ld a,1
        ld (W_SCROLLEDUE),a
        ret
SCL_SET:
        ld (W_SCROLLCNT),a
        ret

; ------------------------------------------------------------
; 地形 1 行分を下へシフトし, 最上段へ次のマップ行を補充
; 入力: なし
; 出力: VRAM_PCG / MIRROR_TOP のプレイフィールド全体を更新
; 破壊: A, B, C, DE, HL, F
; 注意: 重なりのある下方向シフトのため LDIR ではなく LDDR (後方コピー)
;       を使う。オブジェクト消去パス (RO_ERASE_PASS 等) の後に呼ぶこと
; ------------------------------------------------------------
do_scroll_shift:
        ld hl,VRAM_PCG+FIELD_BYTES-41   ; 最終ソース (最下段の直前バイト)
        ld de,VRAM_PCG+FIELD_BYTES-1    ; 最終転送先 (最下段の最終バイト)
        ld bc,FIELD_BYTES-40
        lddr                            ; 行 r → 行 r+1 (最下段は押し出される)
        ld hl,MIRROR_TOP+FIELD_BYTES-41
        ld de,MIRROR_TOP+FIELD_BYTES-1
        ld bc,FIELD_BYTES-40
        lddr
        ld hl,MIRROR_TOP                ; ミラー最上段へ次の行を補充
        call fill_row
        ld hl,MIRROR_TOP
        ld de,VRAM_PCG
        ld bc,40
        ldir
        ret
