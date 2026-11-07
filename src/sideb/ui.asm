; ============================================================
; UI: スコア加算 / 1UP / ハイスコア / メッセージ表示
; ============================================================

; ------------------------------------------------------------
; BCD スコア加算
; 入力: DE = 加算値 (BCD 2 バイト, 第 3 バイトへ桁上がり)
; 出力: W_SCORE += DE, W_STATDIRTY = 1
; 破壊: A, DE, HL, F
; ------------------------------------------------------------
add_score:
        ld hl,W_SCORE
        ld a,(hl)
        add a,e
        daa
        ld (hl),a
        inc hl
        ld a,(hl)
        adc a,d
        daa
        ld (hl),a
        inc hl
        ld a,(hl)
        adc a,0
        daa
        ld (hl),a
        ld a,1
        ld (W_STATDIRTY),a
        ret

; ------------------------------------------------------------
; 10000 点ごとの 1UP チェック
; 入力: なし
; 出力: スコア万位バイトの更新ごとに W_LIVES +1 (上限 6) + W_STATDIRTY = 1
; 破壊: A, B, F
; ------------------------------------------------------------
check_1up:
        ld a,(W_SCORE+2)                ; 万位バイト
        ld b,a
        ld a,(W_UPMARK)
        cp b
        ret nc                          ; 未到達
        ld a,b
        ld (W_UPMARK),a
        ld a,(W_LIVES)
        cp 6
        ret nc
        inc a
        ld (W_LIVES),a
        ld a,1
        ld (W_STATDIRTY),a
        ret

; ------------------------------------------------------------
; ハイスコア更新判定
; 入力: なし
; 出力: W_SCORE > W_HISCORE なら W_HISCORE を更新 + W_STATDIRTY = 1
; 破壊: A, B, DE, HL, F
; ------------------------------------------------------------
hiscore_check:
        ld hl,W_SCORE+2
        ld de,W_HISCORE+2
        ld b,3
HC1:    ld a,(de)
        cp (hl)
        jr c,HC_NEW                     ; hi < score → 更新
        ret nz                          ; hi > score → 終了
        dec hl                          ; 上位バイトから下位へ
        dec de
        djnz HC1
        ret
HC_NEW:
        ld hl,W_SCORE
        ld de,W_HISCORE
        ld bc,3
        ldir
        ld a,1
        ld (W_STATDIRTY),a
        ret

; ------------------------------------------------------------
; メッセージ表示 (行中央寄せ)
; 入力: HL = 文字列 (00h 終端, ディスプレイコード), C = 行番号
; 出力: VRAM_TEXT の指定行中央に文字列を描画
; 破壊: A, B, C, DE, HL, F
; ------------------------------------------------------------
show_msg:
        ld e,l
        ld d,h                          ; DE = 文字列
        push de
        ld l,c                          ; 行
        ld h,0
        add hl,hl                       ; 2r
        push hl
        add hl,hl
        add hl,hl                       ; 8r
        ld b,h
        ld c,l                          ; BC = 8r (LD B,L/LD C,H は HL のバイトスワップになるため)
        pop hl                          ; 2r
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl                       ; 32r
        add hl,bc                       ; 40r
        ld bc,VRAM_TEXT
        add hl,bc                       ; HL = 行先頭
        push de
        ld b,0
SM_CNT: ld a,(de)
        or a
        jr z,SM_CN
        inc b
        inc de
        jr SM_CNT
SM_CN:  pop de                          ; DE = 文字列
        ld a,40
        sub b
        srl a
        ld c,a                          ; 中央寄せ列
        ld b,0
        add hl,bc
SM_P:   ld a,(de)
        or a
        jr z,SM_E
        ld (hl),a
        inc hl
        inc de
        jr SM_P
SM_E:   pop de
        ret

; ------------------------------------------------------------
; メッセージ領域クリア (行 9-13, 列 4-36)
; 入力: なし
; 出力: メッセージ領域を空白 (00h) 化
; 破壊: B, C, DE, HL, F
; ------------------------------------------------------------
clear_messages:
        ld b,5
        ld hl,VRAM_TEXT + 9*40 + 4
CM1:    push bc
        push hl
        ld c,33
CM2:    ld (hl),0
        inc hl
        dec c
        jr nz,CM2
        pop hl
        ld de,40
        add hl,de
        pop bc
        djnz CM1
        ret

; ------------------------------------------------------------
; メッセージタイマ減算 (0 になったら領域クリア)
; 入力: なし
; 出力: W_MSGTIMER が 0 になったフレームで clear_messages 実行し,
;       再減算防止のため W_MSGTIMER = FFFFh をセット
; 破壊: A, HL, F
; ------------------------------------------------------------
msgs_update:
        ld hl,W_MSGTIMER
        call timer_dec
        ret nz
        call clear_messages
        ld hl,0FFFFh
        ld (W_MSGTIMER),hl
        ret
