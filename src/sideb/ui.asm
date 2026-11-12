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
; 出力: VRAM_TEXT の指定行中央に文字列を描画し, その行の PCG 属性を
;       整える (文字セルだけ PCG を隠し, 空白セルは地形表示に戻す)
; 破壊: A, B, C, DE, HL, F
; ------------------------------------------------------------
show_msg:
        push bc                         ; 行番号退避 (属性設定で使う)
        push hl                         ; 文字列退避
        call msg_row_offset             ; HL = 40 * 行
        ld bc,VRAM_TEXT
        add hl,bc                       ; HL = 行先頭 (テキスト)
        pop de                          ; DE = 文字列
        push hl                         ; 行先頭退避
        push de                         ; 文字列退避 (カウントで進むため)
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
        pop hl                          ; HL = 行先頭
        add hl,bc                       ; HL = 描画開始セル
SM_P:   ld a,(de)
        cp 0FFh                         ; 00h は空白としてそのまま書く
        jr z,SM_E
        ld (hl),a
        inc hl
        inc de
        jr SM_P
SM_E:   pop bc                          ; C = 行番号
        jp msg_row_setup                ; その行の PCG 属性を整えて戻る

; ------------------------------------------------------------
; 行番号 → セルオフセット
; 入力: C = 行番号
; 出力: HL = 40 * 行番号
; 破壊: DE, HL, F
; ------------------------------------------------------------
msg_row_offset:
        ld l,c
        ld h,0
        add hl,hl                       ; 2r
        add hl,hl
        add hl,hl                       ; 8r
        ld e,l
        ld d,h                          ; DE = 8r
        add hl,hl
        add hl,hl                       ; 32r
        add hl,de                       ; 40r
        ret

; ------------------------------------------------------------
; メッセージ行の PCG 属性セットアップ (表示開始時に 1 回)
; 入力: C = 行番号
; 出力: その行の文字セルだけ PCG 属性を 00h (表示 OFF) にし,
;       空白セルは PCGATTR_BANK0 (地形表示) にする。
;       色属性は一切触らない (テキストは既定色で読めるため)。
; 破壊: A, B, DE, HL, F
; ------------------------------------------------------------
msg_row_setup:
        call msg_row_offset             ; HL = 40 * 行
        push hl
        ld de,VRAM_TEXT
        add hl,de                       ; HL = テキスト行先頭
        pop de                          ; DE = オフセット
        push hl                         ; テキスト行先頭退避
        ld hl,0DC00h
        add hl,de                       ; HL = PCG 属性行先頭
        ex de,hl                        ; DE = PCG 属性, HL = テキスト
        pop hl
        ld b,40
MRS_L:  ld a,(hl)
        or a
        jr z,MRS_S
        xor a
        ld (de),a                       ; 文字セルの裏だけ PCG を消す
        jr MRS_N
MRS_S:  ld a,PCGATTR_BANK0
        ld (de),a                       ; 空白セルは地形をそのまま見せる
MRS_N:  inc hl
        inc de
        djnz MRS_L
        ret

; ------------------------------------------------------------
; メッセージ行の PCG 属性の再 assert (表示中, 毎フレーム用)
; 入力: C = 行番号
; 出力: その行の文字セルだけ PCG 属性を 00h にする。
;       空白セルには触らない (地形表示はスプライト消去パスが維持する)。
;       スプライトの消去パスが文字セルの属性を地形表示へ戻してしまう
;       ため, 表示中は毎フレームこれを呼んで文字を隠れさせない。
; 破壊: A, B, DE, HL, F
; ------------------------------------------------------------
msg_attr_pcg:
        call msg_row_offset             ; HL = 40 * 行
        push hl
        ld de,VRAM_TEXT
        add hl,de                       ; HL = テキスト行先頭
        pop de                          ; DE = オフセット
        push hl
        ld hl,0DC00h
        add hl,de                       ; HL = PCG 属性行先頭
        ex de,hl                        ; DE = PCG 属性, HL = テキスト
        pop hl
        ld b,40
MAP_L:  ld a,(hl)
        or a
        jr z,MAP_N                      ; 空白セルは触らない
        xor a
        ld (de),a                       ; 文字セルの裏だけ PCG を消す
MAP_N:  inc hl
        inc de
        djnz MAP_L
        ret

; ------------------------------------------------------------
; メッセージ領域 (行 9-13) の PCG 属性の再 assert (表示中, 毎フレーム用)
; 入力: なし
; 出力: 行 9-13 のうち文字が入るセルだけ PCG 属性を 00h にする
;       (空白セルには触らない)
; 破壊: A, B, DE, HL, F
; ------------------------------------------------------------
msg_assert_band:
        ld hl,0DC00h + 9*40
        ld de,VRAM_TEXT + 9*40
        ld b,200
MAB_L:  ld a,(de)
        or a
        jr z,MAB_N                      ; 空白セルは触らない
        xor a
        ld (hl),a                       ; 文字セルの裏だけ PCG を消す
MAB_N:  inc hl
        inc de
        djnz MAB_L
        ret

; ------------------------------------------------------------
; メッセージ属性の再 assert (全状態共通)
; 入力: なし
; 出力: 表示中のメッセージについて, 文字セルの PCG 属性を 00h に
;       再設定する (メイン帯 行 9-13 + アイテム名 行 8)。
;       スプライトの消去パスが文字セルの属性を地形表示へ戻して
;       しまうため, game_tick の入口で毎フレーム呼ぶ。
;       タイマの減算・消去は行わない (各状態の更新処理が担う)。
; 破壊: A, B, C, DE, HL, F
; ------------------------------------------------------------
msg_assert_all:
        ld a,(W_MSGTIMER+1)
        cp 0FFh
        jr nz,MAA_BAND
        ld a,(W_MSGTIMER)
        cp 0FFh
        jr z,MAA_ITEM
MAA_BAND:
        call msg_assert_band
MAA_ITEM:
        ld a,(W_ITMTIMER)
        or a
        ret z
        ld c,8
        jp msg_attr_pcg

; ------------------------------------------------------------
; メッセージ行の消去 + 地形復元
; 入力: C = 先頭行, B = 行数
; 出力: 対象行のテキストを空白化し, PCG コードをミラー (地形) から
;       復元して PCG 属性を全て PCGATTR_BANK0 に戻す。
;       表示中にスプライト消去等で属性がどう化けていても, 消去時点で
;       必ず地形と一致した既知の状態へ戻す (表示系の不整合を残さない)。
; 破壊: A, B, C, DE, HL, F
; ------------------------------------------------------------
msg_hide_rows:
        ld a,b
        ld (W_SCRATCH+2),a              ; 行数
        call msg_row_offset             ; HL = 40 * 先頭行
        ld (W_SCRATCH),hl               ; オフセット
        ; --- テキスト消去 ---
        ld de,VRAM_TEXT
        add hl,de                       ; HL = テキスト先頭
        ld a,(W_SCRATCH+2)
MHR_TR: ld b,40
MHR_TC: ld (hl),0
        inc hl
        djnz MHR_TC
        dec a
        jr nz,MHR_TR
        ; --- 地形コード復元 (ミラー → VRAM) ---
        ld hl,(W_SCRATCH)
        ld de,VRAM_PCG
        add hl,de                       ; HL = VRAM 書込先
        ex de,hl                        ; DE = VRAM 書込先
        ld hl,(W_SCRATCH)
        ld bc,MIRROR_TOP
        add hl,bc                       ; HL = ミラー読出元
        ld a,(W_SCRATCH+2)
MHR_RR: ld bc,40
        ldir
        dec a
        jr nz,MHR_RR
        ; --- PCG 属性を地形表示へ戻す ---
        ld hl,(W_SCRATCH)
        ld bc,0DC00h
        add hl,bc                       ; HL = PCG 属性先頭
        ld a,(W_SCRATCH+2)
MHR_AR: ld b,40
MHR_AC: ld (hl),PCGATTR_BANK0
        inc hl
        djnz MHR_AC
        dec a
        jr nz,MHR_AR
        ret

; ------------------------------------------------------------
; メッセージ領域クリア (行 9-13)
; 入力: なし
; 出力: 行 9-13 のテキスト消去 + 地形復元 (msg_hide_rows のラッパ)
; 破壊: A, B, C, DE, HL, F
; ------------------------------------------------------------
clear_messages:
        ld c,9
        ld b,5
        jp msg_hide_rows

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
        ; 属性の再 assert は game_tick 入口の msg_assert_all が全状態で担う
        ld hl,W_MSGTIMER
        call timer_dec
        ret nz
        call clear_messages             ; 消去 + 地形復元
        ld hl,0FFFFh
        ld (W_MSGTIMER),hl
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
; 出力: W_ITMTIMER > 0 なら -1, 0 到達フレームで行 8 を消去 + 地形復元
; 破壊: A, B, C, DE, HL, F
; ------------------------------------------------------------
itemmsg_update:
        ld a,(W_ITMTIMER)
        or a
        ret z                           ; 非表示
        dec a
        ld (W_ITMTIMER),a
        ret nz
        ld c,8                          ; 表示時間が尽きた → 行 8 を消去
        ld b,1
        jp msg_hide_rows
