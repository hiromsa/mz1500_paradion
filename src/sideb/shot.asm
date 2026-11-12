; ============================================================
; 弾: 自弾 (地形破壊判定込み) / 敵弾 / 照準弾生成
; ============================================================

; ------------------------------------------------------------
; 自弾更新 (スロット O_SHOTS..+3)
; 入力: なし
; 出力: 各弾 y -4 (y < 6 で消滅), 地形ヒットで消滅 (+30 点)
; 破壊: A, B, IX, F
; ------------------------------------------------------------
shots_update:
        ld ix,O_TBL + O_SHOTS*O_LEN
        ld b,4
SU_L:   ld a,(ix+0)
        or a
        jr z,SU_N
        ld a,(ix+3)
        cp 6
        jr c,SU_KILL
        sub 4
        ld (ix+3),a
        call shot_hit_bg                ; BC/DE/HL/IX 保存 → ループカウンタ不要
        jr c,SU_KILL
        jr SU_N
SU_KILL:
        xor a
        ld (ix+0),a
SU_N:   ld de,O_LEN
        add ix,de
        djnz SU_L
        ret

; ------------------------------------------------------------
; 自弾 × 地形 (破壊ブロック) 判定
; 入力: IX = 自弾スロット
; 出力: ヒット時 CY=1 (16x16タイル全体を消去 + スコア +30)
;       非ヒット時 CY=0
; 破壊: A, F (BC, DE, HL, IX は保存)
; 注意: セルアドレスは VRAM (D400h) 基準, ミラーは VRAM-2000h (B400h 基準)。
;       ★旧実装はミラー変換に E000h を引いており F4xx (EXT ROM ウィンドウ)
;         を読み, 一致時に D4xx+2000h の 16bit ラップでメイン RAM 14xx/1Cxx
;         (ゲームコード領域) に書き込むコード破壊バグがあった。
; ------------------------------------------------------------
shot_hit_bg:
        push bc
        push de
        push hl
        ld a,(ix+3)
        srl a
        srl a
        srl a
        cp 22                           ; row >= 22 (フィールド外) は判定しない
        jr nc,SHB_OUT
        ld c,a                          ; row
        ld a,(ix+2)
        srl a
        srl a                           ; x2 → col (描画側と同じ x2>>2)
        ld b,a                          ; col
        push bc
        call CELLADDR                   ; HL = VRAM セル
        ld de,2000h
        or a
        sbc hl,de                       ; ミラー (VRAM-2000h = B400h 基準)
        ld a,(hl)
        call is_breakable
        jr nc,SHB_NO
        pop bc                          ; B=列, C=行 (16x16 タイルの象限計算)
        ; ミラーアドレスをタイル左上へ丸める
        ld a,(W_TILE_PHASE)
        xor c
        and 1
        jr z,SHB_ROW_ALIGNED
        ld de,40
        or a
        sbc hl,de
SHB_ROW_ALIGNED:
        ld a,b
        and 1
        jr z,SHB_TILE_TOP
        dec hl
SHB_TILE_TOP:
        ; ミラーの2x2コードを空にする
        ld (hl),0
        inc hl
        ld (hl),0
        ld de,39
        add hl,de
        ld (hl),0
        inc hl
        ld (hl),0
        ld de,41
        or a
        sbc hl,de                       ; ミラー左上へ戻る
        ld bc,2000h
        add hl,bc                       ; VRAM セルへ戻る
        ld (hl),0
        inc hl
        ld (hl),0
        ld de,39
        add hl,de
        ld (hl),0
        inc hl
        ld (hl),0
        ld de,41
        or a
        sbc hl,de                       ; VRAM 左上へ戻る
        ld de,0800h
        add hl,de                       ; PCG 属性 (DC00h 基準)
        ld (hl),PCGATTR_BANK0
        inc hl
        ld (hl),PCGATTR_BANK0
        ld de,39
        add hl,de
        ld (hl),PCGATTR_BANK0
        inc hl
        ld (hl),PCGATTR_BANK0
        ld de,030h
        call add_score
        pop hl
        pop de
        pop bc
        scf
        ret
SHB_NO: pop bc
SHB_OUT:
        pop hl
        pop de
        pop bc
        or a                            ; CY = 0
        ret

; ------------------------------------------------------------
; 破壊ブロック判定
; 入力: A = セルコード
; 出力: 破壊可能コードなら CY=1
; 破壊: B, F (A, HL は保存)
; ------------------------------------------------------------
is_breakable:
        push hl                         ; 呼び出し側の HL (ミラーセル) を保護
        ld hl,BRK_TABLE
        ld b,BRK_CNT
IB_L:   cp (hl)
        jr z,IB_YES
        inc hl
        djnz IB_L
        pop hl
        or a
        ret
IB_YES: pop hl
        scf
        ret

; ------------------------------------------------------------
; 敵弾更新 (スロット O_ESHOTS..+3)
; 入力: なし
; 出力: y += 弾速 (面 3 以降 3, 未満 2), x 方向 (attr bit2 = 右, bit4 = 2 倍速, 端で停止),
;       y >= 171 で消滅
; 破壊: A, B, IX, F
; ------------------------------------------------------------
eshots_update:
        ld ix,O_TBL + O_ESHOTS*O_LEN
        ld b,4
EU_L:   ld a,(ix+0)
        or a
        jr z,EU_N
        ld a,(W_STAGE)
        cp 3
        jr nc,EU_SP3
        ld a,2
        jr EU_ADDY
EU_SP3: ld a,3
EU_ADDY:
        add a,(ix+3)
        cp 171
        jr nc,EU_KILL
        ld (ix+3),a
        ; x 方向 (attr bit2 = 右 / bit3 = 2 倍速, x2 単位)
        bit 4,(ix+1)
        jr nz,EU_F2                     ; bit4 = 1 → 照準弾は 2px/移動で飛ぶ
        bit 2,(ix+1)
        jr z,EU_L2
        ld a,(ix+2)
        inc a
        cp 153
        jr c,EU_SX
        ld a,152
        jr EU_SX
EU_L2:  ld a,(ix+2)
        or a
        jr z,EU_SX                      ; 左端 (x2=0) で停止
        dec a
        jr EU_SX
EU_F2:  bit 2,(ix+1)
        jr z,EU_F2L
        ld a,(ix+2)
        add a,2                         ; 右 2px
        cp 153
        jr c,EU_SX
        ld a,152
        jr EU_SX
EU_F2L: ld a,(ix+2)
        sub 2                           ; 左 2px
        jr nc,EU_SX
        xor a
EU_SX:  ld (ix+2),a
        inc (ix+5)
        jr EU_N
EU_KILL:
        xor a
        ld (ix+0),a
EU_N:   ld de,O_LEN
        add ix,de
        djnz EU_L
        ret

; ------------------------------------------------------------
; 敵の位置から照準弾生成
; 入力: IX = 発射元敵スロット
; 出力: 空き敵弾スロットがあれば敵直下 (y +12) に生成。
;       自機との x 差から方向 (attr bit2) と 2 倍速 (attr bit4) を設定
; 破壊: A, F (BC, DE, HL, IX は保存)
; ------------------------------------------------------------
spawn_eshot_at:
        push bc
        push de
        push hl
        push ix                         ; FIND_SLOT が IX を壊すため退避
        ld a,O_ESHOTS
        ld b,4
        call FIND_SLOT
        jr c,SESH_R
        push ix
        pop de                          ; DE = 新弾スロット
        pop hl                          ; HL = 発射元敵スロット
        push hl
        ld a,(hl)
        inc hl
        inc hl                          ; +2 = x
        ld c,(hl)                       ; 敵 x2
        inc hl                          ; +3 = y
        ld b,(hl)                       ; 敵 y
        push bc
        ld a,1                          ; state
        ld (de),a
        inc de
        ; 照準: dx = 弾 x2 - 自機 x2 (sign) → 方向 bit2 / 2 倍速 bit4
        ld a,(O_TBL+2)
        ld h,a
        ld a,c                          ; A = 弾 x2 (発射位置)
        sub h                           ; A = 弾 - 自機 (mod 256)
        jr c,SESH_NG                    ; 弾が自機より左 → 自機へ右進
        ; 弾が自機より右 → 自機へ左進 (bit2 = 0)
        cp 10
        jr nc,SESH_LF                   ; |dx| >= 10 → 2 倍速
        ld c,04Ah                       ; 左, 通常 (バンク1 + 1x1, 方向bit2=0, 通常速)
        jr SESH_DA
SESH_LF:ld c,05Ah                       ; 左, 2 倍速 (bit4)
        jr SESH_DA
SESH_NG:neg
        cp 10
        jr nc,SESH_RT                   ; |dx| >= 10 → 2 倍速
        ld c,04Eh                       ; 右, 通常 (bit2)
        jr SESH_DA
SESH_RT:ld c,05Eh                       ; 右, 2 倍速 (bit2 + bit4)
SESH_DA:ld a,c
        ld (de),a
        inc de
        pop bc
        ld a,c                          ; x = 敵 x
        ld (de),a
        inc de
        ld a,b
        add a,12                        ; y = 敵 y + 12
        ld (de),a
        inc de
        ld a,SP_ESHOT
        ld (de),a
        inc de
        xor a
        ld (de),a                       ; t = 0
        ; +6/+7 (描画済みセル) は消去パスが管理するのでここでは触らない
SESH_R: pop ix
        pop hl
        pop de
        pop bc
        ret
