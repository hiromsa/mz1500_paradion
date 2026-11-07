; ============================================================
; 入力: キーマトリクス走査 (8255)
; ============================================================

; ------------------------------------------------------------
; キー走査 → W_KEYS 更新
; 入力: なし
; 出力: W_KEYS = 押下ビットマップ
;       bit0=上 1=下 2=左 3=右 4=射撃(SPACE) 5=CR 6=C
; 破壊: A, B, C, F
; ------------------------------------------------------------
read_keys:
        ; ←→↑↓ の列を選択し、押下行を読む (active-low)
        ld a,KEY_STROBE_7
        ld (PPI_PORTA),a
        nop
        nop
        nop
        nop
        ld a,(PPI_PORTB)
        cpl
        and 3Ch
        ld b,a
        ; 左右は同じbit位置、上下はbit5/4からbit0/1へ詰める
        ld a,b
        and 00Ch
        ld c,a                          ; 左(bit2) / 右(bit3)
        ld a,b
        and KEYBIT_DOWN
        srl a
        srl a
        srl a                           ; 下 bit4 -> W_KEYS bit1
        add a,c
        ld c,a
        ld a,b
        and KEYBIT_UP
        srl a
        srl a
        srl a
        srl a
        srl a                           ; 上 bit5 -> W_KEYS bit0
        add a,c
        ld c,a

        ; SPACE
        ld a,KEY_STROBE_6
        ld (PPI_PORTA),a
        nop
        nop
        nop
        nop
        ld a,(PPI_PORTB)
        cpl
        and KEYBIT_SPACE
        add a,c
        ld c,a

        ; CR
        ld a,KEY_STROBE_0
        ld (PPI_PORTA),a
        nop
        nop
        nop
        nop
        ld a,(PPI_PORTB)
        cpl
        and KEYBIT_CR
        add a,a
        add a,a
        add a,a
        add a,a
        add a,a                           ; CR bit0 -> W_KEYS bit5
        add a,c
        ld c,a

        ; C / continue
        ld a,KEY_STROBE_4
        ld (PPI_PORTA),a
        nop
        nop
        nop
        nop
        ld a,(PPI_PORTB)
        cpl
        and KEYBIT_C
        add a,a                           ; C bit5 -> W_KEYS bit6
        add a,c
        ld (W_KEYS),a
        ret
