; ============================================================
; ボス: 更新 / 攻撃 / 撃破 / 自弾・自機との判定
; ============================================================

; ------------------------------------------------------------
; ボス更新 (W_BOSS 8 バイト構造)
; 入力: なし
; 出力: W_BOSSMODE に応じた移動と攻撃
;       (0 = 進入 / 1 = 戦闘 / 2 = 形態2)
; 破壊: A, B, C, DE, HL, IX, F
; ------------------------------------------------------------
boss_update:
        ld a,(W_BOSSMODE)
        or a
        jr z,boss_move_enter
        dec a
        jr z,boss_move_fight
        ; 形態2: 往復速度アップ (t を 2 ずつ進めてから攻撃処理へ)
        ld a,(W_BOSS+5)
        add a,2
        ld (W_BOSS+5),a
        ; ↓ fall through → boss_fire

; ------------------------------------------------------------
; ボス攻撃タイマ → 照準弾 1 発 (ボス中央下)
; 入力: なし
; 出力: W_BOSSFIRE -1, 0 で攻撃間隔を再セットし敵弾生成
; 破壊: A, B, DE, IX, F
; ------------------------------------------------------------
boss_fire:
        ld a,(W_BOSSFIRE)
        or a
        jr z,BF_SHOT
        dec a
        ld (W_BOSSFIRE),a
        ret
BF_SHOT:
        ld a,(W_BOSSFIREINT)
        ld (W_BOSSFIRE),a
        ; 照準弾 (ボス中央下)
        ld a,O_ESHOTS
        ld b,4
        call FIND_SLOT
        ret c
        ld a,1
        ld (ix+0),a
        ld a,04Ah
        ld (ix+1),a
        ld a,(W_BOSS+2)
        add a,6                         ; x2 = ボス中央
        ld (ix+2),a
        ld a,(W_BOSS+3)
        add a,28                        ; y = ボス下端
        ld (ix+3),a
        ld a,SP_ESHOT
        ld (ix+4),a
        ld (ix+5),0
        ; +6/+7 (描画済みセル) は消去パスが管理するのでここでは触らない
        ret

; ------------------------------------------------------------
; ボス進入: 降下 y +2, t +1 → t >= 28 で戦闘モードへ
; 入力: なし
; 出力: W_BOSS+3 (y) / +5 (t) 更新, 条件成立で W_BOSSMODE = 1
; 破壊: A, F
; ------------------------------------------------------------
boss_move_enter:
        ld a,(W_BOSS+3)
        add a,2
        ld (W_BOSS+3),a
        ld a,(W_BOSS+5)
        inc a
        ld (W_BOSS+5),a
        cp 28
        ret c
        ld a,1
        ld (W_BOSSMODE),a
        ret

; ------------------------------------------------------------
; ボス戦闘: 水平往復 + 形態2判定 + 攻撃
; 入力: なし
; 出力: W_BOSS+2 = 76 + SINE16[(t>>3)&15] / +5 = t+1,
;       面 5 で HP 半減時に形態2移行 (パターン差し替え + 攻撃間隔 -15),
;       boss_fire による攻撃
; 破壊: A, B, C, DE, HL, IX, F
; ------------------------------------------------------------
boss_move_fight:
        ld a,(W_BOSS+5)
        inc a
        ld (W_BOSS+5),a
        ; 水平往復: x2 = 76 + SINE16[(t>>3)&15]
        ld a,(W_BOSS+5)
        srl a
        srl a
        srl a
        and 0Fh
        ld c,a
        ld b,0
        ld hl,SINE16
        add hl,bc
        ld a,(hl)
        ld b,a                          ; B = ±22 (2px 単位)
        ld a,76
        add a,b
        ld (W_BOSS+2),a
        ; ステージ 5: HP 半分で形態2
        ld a,(W_STAGE)
        cp 5
        jr nz,BMF_FIRE
        ld a,(W_BOSSMODE)
        cp 1
        jr nz,BMF_FIRE
        ld hl,(W_STAGETBL)
        ld bc,4
        add hl,bc
        ld a,(hl)                       ; +4 = ボス HP
        srl a                           ; 半分
        ld b,a
        ld a,(W_BOSSHP)
        sub b
        jr nc,BMF_FIRE
        ld a,2
        ld (W_BOSSMODE),a
        ld a,SP_BOSS5B_0                ; ボス 5 形態 2 の PCG 先頭
        ld (W_BOSS+4),a
        ld a,(W_BOSSFIREINT)
        sub 15
        ld (W_BOSSFIREINT),a
BMF_FIRE:
        jp boss_fire

; ------------------------------------------------------------
; 自弾 × ボス
; 入力: なし
; 出力: ヒット弾消滅, W_BOSSHP -1, HP 0 で boss_die 実行
; 破壊: A, B, DE, IX, F
; ------------------------------------------------------------
shots_vs_boss:
        ld ix,O_TBL + O_SHOTS*O_LEN
        ld b,4
SB_L:   push bc
        push ix
        ld a,(ix+0)
        or a
        jr z,SB_N
        ld a,(W_BOSS+0)
        or a
        jr z,SB_N
        ld a,(W_BOSS+2)
        ld e,a
        ld a,(ix+2)
        sub e
        jr nc,SB_A1
        neg
SB_A1:  cp 14
        jr nc,SB_N
        ld a,(W_BOSS+3)
        ld e,a
        ld a,(ix+3)
        sub e
        jr nc,SB_A2
        neg
SB_A2:  cp 30
        jr nc,SB_N
        xor a
        ld (ix+0),a                     ; 弾消滅
        ld a,(W_BOSSHP)
        or a
        jr z,SB_N
        dec a
        ld (W_BOSSHP),a
        jr nz,SB_N
        call boss_die
SB_N:   pop ix
        pop bc
        ld de,O_LEN
        add ix,de
        djnz SB_L
        ret

; ------------------------------------------------------------
; ボス本体 × 自機
; 入力: なし
; 出力: 接触時 hit_player 実行
; 破壊: A, E, F (hit_player 内の死亡処理に従う)
; ------------------------------------------------------------
boss_vs_player:
        ld a,(W_BOSS+0)
        or a
        ret z                           ; 非出現
        ld a,(W_PLRINV)
        or a
        ret nz                          ; 無敵中
        ld a,(W_BOSS+2)
        ld e,a
        ld a,(O_TBL+2)
        sub e
        jr nc,BVP_A1
        neg
BVP_A1: cp 11
        ret nc
        ld a,(W_BOSS+3)
        ld e,a
        ld a,(O_TBL+3)
        sub e
        jr nc,BVP_A2
        neg
BVP_A2: cp 24
        ret nc
        jp hit_player

; ------------------------------------------------------------
; ボス撃破: 消去 + 3 連爆発 + 5000 点 + ST_CLEAR 遷移
; 入力: なし
; 出力: ボス描画セル消去, W_BOSS クリア, 中央/左/右に爆発生成,
;       スコア加算, SE + クリア BGM, "STAGE CLEAR" 表示,
;       W_STATE = ST_CLEAR
; 破壊: A, B, C, DE, HL, IX, F
; ------------------------------------------------------------
boss_die:
        ; ボス座標を爆発生成用に退避
        ld a,(W_BOSS+2)
        ld (W_SCRATCH2),a
        ld a,(W_BOSS+3)
        ld (W_SCRATCH2+1),a
        ; 描画済みセルがあれば消去
        ld a,(W_BOSS+6)
        ld l,a
        ld a,(W_BOSS+7)
        ld h,a
        ld a,h
        or l                            ; ★旧実装は or h のみ (HL = 0 判定が不正)
        jr z,BD_NE
        push hl
        call BOSS_ERASE
        pop hl
BD_NE:  xor a
        ld (W_BOSS+6),a
        ld (W_BOSS+7),a
        ld (W_BOSS+0),a
        call spawn_expl_scratch         ; 中央
        ld a,(W_SCRATCH2)
        sub 10
        ld (W_SCRATCH2),a
        call spawn_expl_scratch         ; 左
        ld a,(W_SCRATCH2)
        add a,20
        ld (W_SCRATCH2),a
        call spawn_expl_scratch         ; 右
        ld de,05000h
        call add_score
        ld de,(W_SEEXPL)
        call play_se
        ld de,BGM_CLEAR
        call play_bgm
        ld hl,240
        ld (W_MSGTIMER),hl
        ld a,ST_CLEAR
        ld (W_STATE),a
        call clear_messages
        ld hl,MSG_CLEAR
        ld c,11
        jp show_msg
