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
; 入力: HL = 文字列 (0FFh 終端, ディスプレイコード, 00h = 空白), C = 行番号
; 出力: VRAM_TEXT の指定行中央に文字列を描画
; 破壊: A, B, C, DE, HL, F
; ------------------------------------------------------------
show_msg:
        push bc                         ; 行番号退避 (終端で属性 OFF 処理)
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
        cp 0FFh                         ; 終端までの文字数を数える
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
        cp 0FFh                         ; 00h は空白としてそのまま書く
        jr z,SM_E
        ld (hl),a
        inc hl
        inc de
        jr SM_P
SM_E:   pop de
        pop bc                          ; C = 行番号
        jp msg_attr_off                 ; 行の PCG 属性を表示 OFF にして戻る

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
        ; 消した行の PCG 属性を表示 ON (バンク0) へ戻す (行 9-13 = 200 セル連続)
        ld hl,0DC00h + 9*40
        ld de,0DC01h + 9*40
        ld bc,200
        ld (hl),PCGATTR_BANK0
        ldir
        ret

; ------------------------------------------------------------
; メッセージタイマ減算 (0 になったら領域クリア)
; 入力: なし
; 出力: W_MSGTIMER が 0 になったフレームで clear_messages 実行し,
;       再減算防止のため W_MSGTIMER = FFFFh をセット
; 破壊: A, HL, F
; ------------------------------------------------------------
msgs_update:
        ; アイドル (FFFFh) なら何もしない
        ld a,(W_MSGTIMER+1)
        cp 0FFh
        jr nz,MSGU_ACT
        ld a,(W_MSGTIMER)
        cp 0FFh
        ret z
MSGU_ACT:
        ; 表示中は行 9-13 の PCG 属性表示 OFF を毎フレーム再 assert
        ; (スプライトの消去パスが属性を表示 ON に戻し文字を隠すため)
        call msgs_attr_off
        ld hl,W_MSGTIMER
        call timer_dec
        ret nz
        call clear_messages
        ld hl,0FFFFh
        ld (W_MSGTIMER),hl
        ret

; ------------------------------------------------------------
; 行 9-13 (メッセージ領域) の PCG 属性を一括表示 OFF
; 入力: なし / 出力: 0DC00h+9*40 から 200 セルを 00h へ
; 破壊: A, BC, DE, HL, F
; ------------------------------------------------------------
msgs_attr_off:
        ld hl,0DC00h + 9*40
        ld de,0DC01h + 9*40
        ld bc,200
        ld (hl),0
        ldir
        ret
; ------------------------------------------------------------
; アイテム名メッセージ表示 (行 8 中央)
; 入力: HL = 文字列 (0FFh 終端)
; 出力: 行 8 中央に表示 + W_ITMTIMER = ITEMMSG_FRAMES
;       (メインメッセージ領域 行 9-13 とは別行のため重ならない)
; 破壊: A, C, DE, HL, F
; ------------------------------------------------------------
show_item_msg:
        push hl
        ld c,8
        call show_msg
        pop hl
        ld a,ITEMMSG_FRAMES
        ld (W_ITMTIMER),a
        ret

; ------------------------------------------------------------
; アイテム名メッセージタイマ更新 (0 で行 8 を消去)
; 入力: なし
; 出力: W_ITMTIMER > 0 なら -1, 0 到達フレームで行 8 を空白化
; 破壊: A, B, HL, F
; ------------------------------------------------------------
itemmsg_update:
        ld a,(W_ITMTIMER)
        or a
        ret z                           ; 非表示
        push af
        ld c,8
        call msg_attr_off               ; 表示中は行 8 属性 OFF を再 assert
        pop af
        dec a
        ld (W_ITMTIMER),a
        ret nz
        ; 表示時間が尽きた → 行 8 を消去
        ld b,33
        ld hl,VRAM_TEXT + 8*40 + 4
IM_CLR: ld (hl),0
        inc hl
        djnz IM_CLR
        ; 行 8 の PCG 属性を表示 ON へ戻す
        ld hl,0DC00h + 8*40
        ld c,40
IM_A:   ld (hl),PCGATTR_BANK0
        inc hl
        dec c
        jr nz,IM_A
        ret
; ------------------------------------------------------------
; メッセージ行の PCG 属性を表示 OFF (テキストを前面に見せる)
; 入力: C = 行番号
; 出力: 0DC00h + 40*行 から 40 セルの PCG 属性を 00h (表示 OFF) へ
;       (PCG が前面のため, 属性を切らないとテキスト レイヤの
;        メッセージが地形に隠れて見えない。復帰は clear_messages /
;        itemmsg_update が行う)
; 破壊: A, C, DE, HL, F
; ------------------------------------------------------------
msg_attr_off:
        ld l,c
        ld h,0
        add hl,hl                       ; 2r
        push hl
        add hl,hl
        add hl,hl                       ; 8r
        ld e,l
        ld d,h                          ; DE = 8r
        pop hl                          ; 2r
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl                       ; 32r
        add hl,de                       ; 40r
        ld de,0DC00h
        add hl,de                       ; HL = PCG 属性の行先頭
        ld c,40
MAO_L:  ld (hl),0
        inc hl
        dec c
        jr nz,MAO_L
        ret
