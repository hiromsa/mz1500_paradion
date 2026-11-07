; ============================================================
; 敵: 更新 / 種別移動 / スポーン / 撃破
; ============================================================

; ------------------------------------------------------------
; 敵更新 (スロット O_ENEMIES..+5)
; 入力: なし
; 出力: 種別に応じた移動と消滅
;       (1/3 = ガーゴイル / 2/4 = ウィスプ, 3/4 はアイテム持ち)
; 破壊: A, B, IX, F
; ------------------------------------------------------------
enemies_update:
        ld ix,O_TBL + O_ENEMIES*O_LEN
        ld b,6
NU_L:   ld a,(ix+0)
        or a
        jr z,NU_N
        inc (ix+5)                      ; t++
        cp 1                            ; 種別 1 = ガーゴイル
        jr z,EN_GARG
        cp 3                            ; 種別 3 = アイテム持ちガーゴイル
        jr z,EN_GARG
        call enemy_move_wisp            ; 種別 2 = ウィスプ
        jr NU_N
EN_GARG:
        call enemy_move_gargoyle
NU_N:   ld de,O_LEN
        add ix,de
        djnz NU_L
        ret

; ------------------------------------------------------------
; ウィスプ (種別 2/4) 移動: 直進降下, t = 48 で照準弾 1 発
; 入力: IX = 敵スロット
; 出力: y +1px/frame (y >= 168 で消滅), t=48 で照準弾
; 破壊: A, B, F
; ------------------------------------------------------------
enemy_move_wisp:
        ld a,(ix+3)
        inc a                           ; 敵はスクロールと独立して一定速度
        cp 168                          ; 2x2 の下段が行 21 を超える前に消滅
        jr nc,EMW_KILL
        ld (ix+3),a
        ld a,(ix+5)
        cp 48
        ret nz
        jp spawn_eshot_at               ; BC/DE/HL/IX 保存 → ループに影響なし
EMW_KILL:
        xor a
        ld (ix+0),a
        ret

; ------------------------------------------------------------
; ガーゴイル (種別 1/3) 移動: 降下 + 16t ごとに水平方向反転
; 入力: IX = 敵スロット
; 出力: y +1px/frame (y >= 168 で消滅), x 往復
; 破壊: A, F
; ------------------------------------------------------------
enemy_move_gargoyle:
        ld a,(ix+3)
        inc a                           ; 敵はスクロールと独立して一定速度
        cp 168
        jr nc,EMG_KILL
        ld (ix+3),a
        ld a,(ix+5)
        and 0Fh                         ; 16 タイク毎に方向反転 (attr bit2)
        jr nz,EMG_DX
        ld a,(ix+1)
        xor 04h
        ld (ix+1),a
EMG_DX: bit 2,(ix+1)
        jr z,EMG_L
        ld a,(ix+2)
        inc a
        cp 153
        jr c,EMG_SET
        ld a,(ix+1)                     ; 右端 (x2=152) → 反転 (x2 は据え置き)
        xor 04h
        ld (ix+1),a
        ret
EMG_SET:
        ld (ix+2),a
        ret
EMG_L:  ld a,(ix+2)
        or a
        jr nz,EMG_DEC
        ld a,(ix+1)                     ; 左端 (x2=0) → 反転 (x2 は据え置き)
        xor 04h
        ld (ix+1),a
        ret
EMG_DEC:
        dec a
        ld (ix+2),a
        ret
EMG_KILL:
        xor a
        ld (ix+0),a
        ret

; ------------------------------------------------------------
; 敵スポーンタイマ
; 入力: なし
; 出力: W_SPAWNCNT -1, 0 で間隔リセット + 空き敵スロットへ 1 体生成
;       (x2 = (乱数 & 1Fh) * 4 + 8, y = 0, ガーゴイル/ウィスプ 半々)
; 破壊: A, B, C, DE, IX, F
; ------------------------------------------------------------
spawn_update:
        ld a,(W_SPAWNCNT)
        or a
        jr z,SPW_SPAWN
        dec a
        ld (W_SPAWNCNT),a
        ret
SPW_SPAWN:
        ld a,(W_SPAWNINT)
        ld (W_SPAWNCNT),a
        ld a,O_ENEMIES
        ld b,6
        call FIND_SLOT
        ret c
        call rand8
        ld c,a
        ; x2 = (乱数 & 1Fh) * 4 + 8
        and 1Fh
        add a,a
        add a,a
        add a,8
        ld (ix+2),a
        xor a
        ld (ix+3),a                     ; y = 0
        ; 1/8 をアイテム持ちとして出現させる (乱数下位3bit = 0)
        ld d,0
        ld a,c
        and 7
        jr nz,SPW_TYPE
        ld d,2                          ; 種別に +2 → carrier (3/4)
SPW_TYPE:
        ld a,c
        rrca
        and 1
        jr z,SPW_WISP
        ; ガーゴイル
        ld a,1
        add a,d
        ld (ix+0),a
        ld a,089h                       ; attr (バンク2 + anim)
        ld (ix+1),a
        ld a,d
        add a,a
        add a,a
        add a,a                         ; carrier pattern is +16
        ld e,a
        ld a,SP_GARG0
        add a,e
        jr SPW_SET
SPW_WISP:
        ld a,2
        add a,d
        ld (ix+0),a
        ld a,089h
        ld (ix+1),a
        ld a,d
        add a,a
        add a,a
        add a,a
        ld e,a
        ld a,SP_WISP0
        add a,e
SPW_SET:
        ld (ix+4),a
        ld (ix+5),0
        ; +6/+7 (描画済みセル) は消去パスが管理するのでここでは触らない
        ret

; ------------------------------------------------------------
; 敵撃破処理
; 入力: HL = 敵スロット先頭
; 出力: 敵消滅 + 敵位置に爆発生成 + 100 点加算
;       アイテム持ち敵 (種別3/4) のみパワーアップをドロップ
; 破壊: A, B, DE, HL, F (IX は保存)
; ------------------------------------------------------------
kill_enemy:
        push ix
        ld a,(hl)                       ; carrier flag before clearing state
        cp 3
        jr z,KE_CARRIER
        cp 4
        jr z,KE_CARRIER
        xor a                           ; ordinary enemy does not drop an item
        jr KE_FLAG
KE_CARRIER:
        ld a,1                           ; carrier guarantees its marked item drop
KE_FLAG:
        push af
        xor a
        ld (hl),a                       ; 敵消滅
        push hl
        inc hl
        inc hl
        ld a,(hl)
        ld (W_SCRATCH2),a               ; 敵 x2
        inc hl
        ld a,(hl)
        ld (W_SCRATCH2+1),a             ; 敵 y
        pop hl
        call spawn_expl_scratch
        ld de,0100h
        call add_score
        pop af
        or a
        jr z,KE_RET
        ; アイテム持ちを倒したときだけ必ずドロップ
        ld a,O_PWUPS
        ld b,2
        call FIND_SLOT
        jr c,KE_RET
        ld a,1
        ld (ix+0),a
        ld a,04Ah
        ld (ix+1),a
        ld a,(W_SCRATCH2)
        ld (ix+2),a
        ld a,(W_SCRATCH2+1)
        ld (ix+3),a
        ld a,r
        and 3
        ld hl,PWUP_TBL
        ld e,a
        ld d,0
        add hl,de
        ld a,(hl)
        ld (ix+4),a
        ld (ix+5),0
        ; +6/+7 (描画済みセル) は消去パスが管理するのでここでは触らない
KE_RET: pop ix
        ret
