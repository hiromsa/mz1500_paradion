; ============================================================
; 描画パス: オブジェクト / ボス / スコア欄 (V-BLANK 中に呼ぶ)
;  スクロール時: 消去 → 地形シフト → 描画 の順で残像を防ぐ
; ============================================================

; ------------------------------------------------------------
; 全オブジェクト再描画 (メインループから毎フレーム呼ぶ)
; 入力: なし
; 出力: W_SCROLLEDUE = 1 なら消去 → 地形シフト → 描画,
;       それ以外は消去 → 描画, 最後にボスとスコア欄を更新
; 破壊: すべて
; ------------------------------------------------------------
render_objects:
        ld a,(W_SCROLLEDUE)
        or a
        jr z,RO_PLAIN
        xor a
        ld (W_SCROLLEDUE),a
        call RO_ERASE_PASS
        call render_boss_erase
        call do_scroll_shift
        call RO_DRAW_PASS
        call render_boss_draw
        call render_status
        ret
RO_PLAIN:
        call RO_ERASE_PASS
        call render_boss_erase
        call RO_DRAW_PASS
        call render_boss_draw
        call render_status
        ret

; ------------------------------------------------------------
; パス 1: 旧セル消去 (全 20 スロット)
; 入力: なし
; 出力: 描画済みセル (+6/+7) があるスロットを消去し +6/+7 = 0 に
;       (状態に関係なく消すため消滅直後の残像も消える)
; 破壊: A, B, DE, IX, F
; ------------------------------------------------------------
RO_ERASE_PASS:
        ld ix,O_TBL
        ld b,O_SLOTS
RO_E1:
        push bc                         ; ループカウンタ (ヘルパが BC を壊すため)
        ld l,(ix+6)
        ld h,(ix+7)
        ld a,h
        or l
        jr z,RO_E1CLR                   ; 未描画 → 消去不要
        bit 1,(ix+1)
        jr nz,RO_E1X1
        call ERASE2X2
        jr RO_E1CLR
RO_E1X1:
        call ERASE1X1
RO_E1CLR:
        ld (ix+6),0
        ld (ix+7),0
        pop bc
        ld de,O_LEN
        add ix,de
        djnz RO_E1
        ret

; ------------------------------------------------------------
; パス 2: 現位置へ描画 (全 20 スロット)
; 入力: なし
; 出力: 有効スロット (+0 != 0, y < 176) をセルへ描画し,
;       消去用にミラーセルアドレスを +6/+7 へ保存
; 破壊: A, B, C, DE, IX, F
; ------------------------------------------------------------
RO_DRAW_PASS:
        ld ix,O_TBL
        ld b,O_SLOTS
RO_D1:
        ld a,(ix+0)
        or a
        jr z,RO_DSKIP
        ld a,(ix+3)
        cp 176                          ; y >= 176 は画面外
        jr nc,RO_DSKIP
        push bc                         ; ループカウンタ
        ; セルアドレス: B = col, C = row
        ld a,(ix+2)
        srl a
        srl a                           ; x2 → col
        ld b,a
        ld a,(ix+3)
        srl a
        srl a
        srl a
        ld c,a
        push de
        call CELLADDR                   ; HL = セル
        pop de
        ; コード (anim: (t>>3 &1)*4 を加算)
        ld a,(ix+4)
        bit 0,(ix+1)
        jr z,RO_DNAN
        ld a,(ix+5)
        srl a
        srl a
        srl a
        and 1                           ; (t >> 3) & 1
        add a,a
        add a,a                         ; animation frame offset = 0 or 4
        ld e,a
        ld a,(ix+4)                     ; preserve the sprite's base PCG code
        add a,e
RO_DNAN:
        ld b,a                          ; コード
        ld a,(ix+1)
        and 0F8h
        ld c,a                          ; 属性
        ld (ix+6),l                     ; 消去用にミラーセル (VRAM-2000h) を保存
        ld a,h                          ; (ERASE2X2 / ERASE1X1 はミラー基準)
        sub 20h
        ld (ix+7),a
        bit 1,(ix+1)
        jr nz,RO_D1X1
        call DRAW2X2
        pop bc
        jr RO_DSKIP
RO_D1X1:
        call DRAW1X1
        pop bc
RO_DSKIP:
        ld de,O_LEN
        add ix,de
        djnz RO_D1
        ret

; ------------------------------------------------------------
; ボス消去パス (旧セル)
; 入力: なし
; 出力: W_BOSS+6/+7 (描画済みセル) があれば BOSS_ERASE し 0 に戻す
; 破壊: A, B, C, DE, HL, F
; ------------------------------------------------------------
render_boss_erase:
        ld a,(W_BOSS+0)
        or a
        ret z                           ; 非出現
        ld a,(W_BOSS+6)
        ld l,a
        ld a,(W_BOSS+7)
        ld h,a
        ld a,h
        or l
        ret z
        push hl
        call BOSS_ERASE
        pop hl
        xor a
        ld (W_BOSS+6),a
        ld (W_BOSS+7),a
        ret

; ------------------------------------------------------------
; ボス描画パス (4x4 セル)
; 入力: なし
; 出力: W_BOSS+6/+7 にミラー基準セルを記録し BOSS_DRAW で描画
;       (W_BOSS+0 = 0 または y >= 176 のとき何もしない)
; 破壊: A, B, C, D, E, HL, F
; ------------------------------------------------------------
render_boss_draw:
        ld a,(W_BOSS+0)
        or a
        ret z                           ; 非出現
        ld a,(W_BOSS+3)
        cp 176
        ret nc
        ; セル
        ld a,(W_BOSS+2)
        srl a
        srl a                           ; x2 → col
        ld b,a
        ld a,(W_BOSS+3)
        srl a
        srl a
        srl a
        ld c,a
        call CELLADDR
        ld a,l
        ld (W_BOSS+6),a
        ld a,h
        sub 20h                         ; BOSS_ERASE はミラー基準 (VRAM-2000h)
        ld (W_BOSS+7),a
        ; フレーム先頭コード: base + frame*16
        ld a,(W_BOSS+5)
        srl a
        srl a
        srl a
        srl a
        and 1
        jr z,RBD_F0
        ld a,16
RBD_F0: ld e,a
        ld a,(W_BOSS+4)
        add a,e
        ld d,a                          ; D = フレーム先頭コード
        jp BOSS_DRAW

; ------------------------------------------------------------
; ボス本体 4x4 セル描画
; 入力: HL = VRAM 左上セル, D = フレーム先頭コード
; 出力: 4x4 セルにコード (行頭 + 0..3) と属性 (バンク3) を描画
; 破壊: A, B, D, E, HL, F
; ------------------------------------------------------------
BOSS_DRAW:
        ld b,4                          ; 4 行
RBD_ROW:
        push bc
        push hl
        ld a,4
        sub b                           ; 行インデックス 0-3
        add a,a
        add a,a                         ; row*4
        add a,d
        ld e,a                          ; E = この行の先頭コード
        ld (hl),e
        inc e
        inc hl
        ld (hl),e
        inc e
        inc hl
        ld (hl),e
        inc e
        inc hl
        ld (hl),e
        ; 属性 4 セル
        ld de,0800h
        add hl,de
        ld a,PCGATTR_BANK3
        ld (hl),a
        dec hl
        ld (hl),a
        dec hl
        ld (hl),a
        dec hl
        ld (hl),a
        pop hl
        pop bc
        ld de,40
        add hl,de                       ; 次の行
        dec b
        jr nz,RBD_ROW
        ret

; ------------------------------------------------------------
; ボス消去 (4x4 セルを地形コードへ復元)
; 入力: HL = 左上ミラーセル (0B400h 基準)
; 出力: コード 4x4 をミラーから復元, 属性 4x4 を PCGATTR_BANK0 へ
; 破壊: A, B, C, D, E, HL, F
; ------------------------------------------------------------
BOSS_ERASE:
        ld b,4
BE_ROW:
        push bc
        push hl
        ld de,2000h
        add hl,de                       ; VRAM
        push hl
        or a
        ld bc,2000h
        sbc hl,bc                       ; ミラー
        ld a,(hl)
        inc hl
        ld b,(hl)
        inc hl
        ld c,(hl)
        inc hl
        ld d,(hl)
        pop hl
        ld (hl),a
        inc hl
        ld (hl),b
        inc hl
        ld (hl),c
        inc hl
        ld (hl),d
        ; 属性復元
        ld de,0800h
        add hl,de
        ld a,PCGATTR_BANK0
        ld (hl),a
        dec hl
        ld (hl),a
        dec hl
        ld (hl),a
        dec hl
        ld (hl),a
        pop hl
        pop bc
        ld de,40
        add hl,de
        dec b
        jr nz,BE_ROW
        ret

; ------------------------------------------------------------
; スコア欄描画 (W_STATDIRTY = 1 のときのみ)
; 入力: なし
; 出力: スコア / ハイスコア / 残機 / ステージを描画し W_STATDIRTY = 0
; 破壊: A, B, C, DE, HL, F
; ------------------------------------------------------------
render_status:
        ld a,(W_STATDIRTY)
        or a
        ret z
        xor a
        ld (W_STATDIRTY),a
        ; SCORE 6 桁 (col 6-11)
        ld de,W_SCORE+2                 ; 最上位バイト
        ld hl,VRAM_PCG + 23*40 + 6
        call draw_bcd6
        ld de,W_HISCORE+2
        ld hl,VRAM_PCG + 23*40 + 15
        call draw_bcd6
        ; 残機 (heart col26, 数値 col27)
        ld a,T_HEART
        ld (VRAM_PCG + 23*40 + 26),a
        ld a,(W_LIVES)
        and 0Fh
        add a,T_DIGIT0
        ld (VRAM_PCG + 23*40 + 27),a
        ; ステージ数 (col36)
        ld a,(W_STAGE)
        add a,T_DIGIT0
        ld (VRAM_PCG + 23*40 + 36),a
        ret

; ------------------------------------------------------------
; BCD 3 バイト → 数字タイル 6 桁
; 入力: DE = 最上位バイトのアドレス (下位へ 3 バイト), HL = VRAM 転送先
; 出力: 6 桁分の数字タイルを描画
; 破壊: A, B, C, DE, HL, F
; ------------------------------------------------------------
draw_bcd6:
        ld b,3                          ; 3 バイト
DB6_B:
        ld a,(de)
        push bc
        ld c,a
        and 0F0h
        rrca
        rrca
        rrca
        rrca
        add a,T_DIGIT0
        ld (hl),a
        inc hl
        ld a,c
        and 0Fh
        add a,T_DIGIT0
        ld (hl),a
        inc hl
        pop bc
        dec de
        djnz DB6_B
        ret
