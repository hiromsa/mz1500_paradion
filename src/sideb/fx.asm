; ============================================================
; 演出: 爆発
; ============================================================

; ------------------------------------------------------------
; 爆発更新 (スロット O_EXPLS..+2)
; 入力: なし
; 出力: t +1, t >= 24 で消滅, コード = SP_EXPL0 + (t >> 3) * 4
; 破壊: A, B, IX, F
; ------------------------------------------------------------
expls_update:
        ld ix,O_TBL + O_EXPLS*O_LEN
        ld b,3
EX_L:   ld a,(ix+0)
        or a
        jr z,EX_N
        ld a,(ix+5)
        inc a
        cp 24
        jr nc,EX_KILL
        ld (ix+5),a
        ; code = SP_EXPL0 + (t >> 3) * 4
        srl a
        srl a
        srl a
        add a,a
        add a,a
        add a,SP_EXPL0
        ld (ix+4),a
        jr EX_N
EX_KILL:
        xor a
        ld (ix+0),a
EX_N:   ld de,O_LEN
        add ix,de
        djnz EX_L
        ret

; ------------------------------------------------------------
; 爆発生成
; 入力: W_SCRATCH2 = 座標 (+0 = x2, +1 = y)
; 出力: 空きスロットに爆発 1 個生成 (空きなし時は何もしない)
; 破壊: A, B, DE, IX, F
; ------------------------------------------------------------
spawn_expl_scratch:
        ld a,O_EXPLS
        ld b,3
        call FIND_SLOT
        ret c
        ld a,1
        ld (ix+0),a
        ld a,049h                       ; attr (バンク1 + anim)
        ld (ix+1),a
        ld a,(W_SCRATCH2)
        ld (ix+2),a
        ld a,(W_SCRATCH2+1)
        ld (ix+3),a
        ld a,SP_EXPL0
        ld (ix+4),a
        ld (ix+5),0
        ; +6/+7 (描画済みセル) は消去パスが管理するのでここでは触らない
        ret
