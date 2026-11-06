; ============================================================
; 当たり判定: 弾×敵 / 敵弾×自機 / 敵×自機 / まとめ
; ============================================================

; ------------------------------------------------------------
; フィールド面の当たり判定まとめ
; 入力: なし
; 出力: 弾×敵, 敵弾×自機, 敵×自機, 1UP 判定を実行
; 破壊: すべて (各判定ルーチンに従う)
; ------------------------------------------------------------
collide_field:
        call shots_vs_enemies
        call eshots_vs_player
        call enemies_vs_player
        call check_1up
        ret

; ------------------------------------------------------------
; ボス戦の当たり判定まとめ
; 入力: なし
; 出力: 弾×ボス, 敵弾×自機, 敵×自機, ボス×自機, 1UP 判定を実行
; 破壊: すべて (各判定ルーチンに従う)
; ------------------------------------------------------------
collide_boss:
        call shots_vs_boss
        call eshots_vs_player
        call enemies_vs_player
        call boss_vs_player
        call check_1up
        ret

; ------------------------------------------------------------
; 自弾 × 敵
; 入力: なし
; 出力: ヒット弾消滅 + kill_enemy (敵消滅/爆発/スコア/ドロップ)
; 破壊: A, B, C, D, E, HL, IX, F
; ------------------------------------------------------------
shots_vs_enemies:
        ld ix,O_TBL + O_SHOTS*O_LEN
        ld b,4
CF_SHOT:
        push bc
        ld a,(ix+0)
        or a
        jr z,CF_NEXTS
        ld hl,O_TBL + O_ENEMIES*O_LEN
        ld c,6
CF_EN:
        ld a,(hl)
        or a
        jr z,CF_ENEXT
        inc hl
        inc hl
        ld d,(hl)                       ; D = 敵 x
        inc hl
        ld e,(hl)                       ; E = 敵 y
        dec hl
        dec hl
        dec hl                          ; HL = 敵先頭
        ld a,(ix+2)
        sub d
        jr nc,CF_A1
        neg
CF_A1:  cp 6
        jr nc,CF_ENEXT
        ld a,(ix+3)
        sub e
        jr nc,CF_A2
        neg
CF_A2:  cp 12
        jr nc,CF_ENEXT
        xor a
        ld (ix+0),a                     ; 弾消滅
        call kill_enemy                 ; HL = 敵先頭 (敵消滅・爆発等)
        jr CF_NEXTS                     ; 命中したのでこの弾の探索終了
CF_ENEXT:
        ld de,O_LEN
        add hl,de
        dec c
        jr nz,CF_EN
CF_NEXTS:
        ld de,O_LEN
        add ix,de
        pop bc
        djnz CF_SHOT
        ret

; ------------------------------------------------------------
; 敵弾 × 自機
; 入力: なし
; 出力: 接触敵弾消滅 + hit_player 実行
; 破壊: A, B, IX, F
; ------------------------------------------------------------
eshots_vs_player:
        ld ix,O_TBL + O_ESHOTS*O_LEN
        ld b,4
EVP_L:  push bc
        push ix
        ld a,(ix+0)
        or a
        jr z,EVP_N
        ld a,(W_PLRINV)
        or a
        jr nz,EVP_N
        ld b,(ix+2)
        ld a,(O_TBL+2)
        sub b
        jr nc,EVP_A1
        neg
EVP_A1: cp 5
        jr nc,EVP_N
        ld b,(ix+3)
        ld a,(O_TBL+3)
        sub b
        jr nc,EVP_A2
        neg
EVP_A2: cp 12
        jr nc,EVP_N
        xor a
        ld (ix+0),a                     ; 弾消滅
        call hit_player
EVP_N:  pop ix
        pop bc
        ld de,O_LEN
        add ix,de
        djnz EVP_L
        ret

; ------------------------------------------------------------
; 敵本体 × 自機
; 入力: なし
; 出力: 接触敵消滅 + 接触位置に爆発 + hit_player 実行
; 破壊: A, B, IX, F
; ------------------------------------------------------------
enemies_vs_player:
        ld ix,O_TBL + O_ENEMIES*O_LEN
        ld b,6
NVP_L:  push bc
        push ix
        ld a,(ix+0)
        or a
        jr z,NVP_N
        ld a,(W_PLRINV)
        or a
        jr nz,NVP_N
        ld b,(ix+2)
        ld a,(O_TBL+2)
        sub b
        jr nc,NVP_A1
        neg
NVP_A1: cp 7
        jr nc,NVP_N
        ld b,(ix+3)
        ld a,(O_TBL+3)
        sub b
        jr nc,NVP_A2
        neg
NVP_A2: cp 14
        jr nc,NVP_N
        xor a
        ld (ix+0),a                     ; 敵も消滅
        ld a,(ix+2)
        ld (W_SCRATCH2),a
        ld a,(ix+3)
        ld (W_SCRATCH2+1),a
        call spawn_expl_scratch
        call hit_player
NVP_N:  pop ix
        pop bc
        ld de,O_LEN
        add ix,de
        djnz NVP_L
        ret
