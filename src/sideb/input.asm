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
        ld a,KEY_STROBE_7               ; ←→↑↓ (bit2 L / bit3 R / bit4 D / bit5 U)
        ld (PPI_PORTA),a
        ld a,(PPI_PORTB)
        cpl
        and 3Ch
        ld b,a
        ld c,0
        bit 5,b
        jr z,RK_N1
        set 0,c                         ; 上
RK_N1:  bit 4,b
        jr z,RK_N2
        set 1,c                         ; 下
RK_N2:  bit 2,b
        jr z,RK_N3
        set 2,c                         ; 左
RK_N3:  bit 3,b
        jr z,RK_N4
        set 3,c                         ; 右
RK_N4:  ld a,KEY_STROBE_6               ; SPACE (bit4)
        ld (PPI_PORTA),a
        ld a,(PPI_PORTB)
        cpl
        and KEYBIT_SPACE
        jr z,RK_N5
        set 4,c
RK_N5:  ld a,KEY_STROBE_0               ; CR (bit0)
        ld (PPI_PORTA),a
        ld a,(PPI_PORTB)
        cpl
        and KEYBIT_CR
        jr z,RK_N6
        set 5,c
RK_N6:  ld a,KEY_STROBE_4               ; C (bit5)
        ld (PPI_PORTA),a
        ld a,(PPI_PORTB)
        cpl
        and KEYBIT_C
        jr z,RK_N7
        set 6,c
RK_N7:  ld a,c
        ld (W_KEYS),a
        ret
