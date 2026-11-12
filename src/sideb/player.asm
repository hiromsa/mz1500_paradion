; ============================================================
; 自機: 移動 / 発射 / 機体パターン / 被弾
; ============================================================

; ------------------------------------------------------------
; 自機更新 (O_TBL スロット 0)
; 入力: なし (W_KEYS / 各種ワークを参照)
; 出力: 無敵・クールダウン減算, 方向キー移動 (クランプ込み),
;       射撃 (クールダウン 0 時), 移動位相に応じた機体パターン更新
; 破壊: A, B, C, IX, F
; ------------------------------------------------------------
player_update:
        ld ix,O_TBL                     ; スロット 0
        call player_tick_timers
        call player_move
        call player_try_fire
        jp player_set_pattern

; ------------------------------------------------------------
; 無敵 / クールダウンタイマ減算
; 入力: なし (IX 未使用)
; 出力: W_PLRINV > 0 なら -1, W_PLRCD > 0 なら -1
; 破壊: A, F
; ------------------------------------------------------------
player_tick_timers:
        ld a,(W_PLRINV)
        or a
        jr z,PTT_CD
        dec a
        ld (W_PLRINV),a
PTT_CD: ld a,(W_PLRCD)
        or a
        ret z
        dec a
        ld (W_PLRCD),a
        ret

; ------------------------------------------------------------
; 方向キーによる移動 + 画面端クランプ
; 入力: IX = 自機スロット
; 出力: +3 (y) を [0,152], +2 (x2) を [0,144] の範囲で移動
; 破壊: A, B, C, F
; ------------------------------------------------------------
player_move:
        ld a,(W_PLRSPD)
        ld b,a                          ; y 移動量 (px)
        ld c,a
        srl c                           ; x 移動量 (2px 単位)
        ld a,(W_KEYS)
        bit 0,a                         ; 上
        jr z,PM_D1
        ld a,(ix+3)
        sub b
        jr nc,PM_U1
        xor a                           ; 上端クランプ
PM_U1:  ld (ix+3),a
PM_D1:  ld a,(W_KEYS)
        bit 1,a                         ; 下
        jr z,PM_L1
        ld a,(ix+3)
        add a,b
        cp 153
        jr c,PM_D2
        ld a,152                        ; 下端クランプ
PM_D2:  ld (ix+3),a
PM_L1:  ld a,(W_KEYS)
        bit 2,a                         ; 左
        jr z,PM_R1
        ld a,(ix+2)
        sub c
        jr nc,PM_L2
        xor a                           ; 左端クランプ
PM_L2:  ld (ix+2),a
PM_R1:  ld a,(W_KEYS)
        bit 3,a                         ; 右
        jr z,PM_END
        ld a,(ix+2)
        add a,c
        cp 145
        jr c,PM_R2
        ld a,144                        ; 右端クランプ
PM_R2:  ld (ix+2),a
PM_END: ret

; ------------------------------------------------------------
; 射撃キー処理
; 入力: なし (IX 未使用)
; 出力: 射撃キー押下かつ W_PLRCD = 0 なら player_fire 実行
; 破壊: A, B, IX, F (player_fire に従う)
; ------------------------------------------------------------
player_try_fire:
        ld a,(W_KEYS)
        bit 4,a                         ; 射撃
        ret z
        ld a,(W_PLRCD)
        or a
        ret nz                          ; クールダウン中
        jp player_fire

; ------------------------------------------------------------
; 機体パターン更新 (歩行アニメ 2 フレーム x 水平位相 4 相)
; 入力: なし
; 出力: 自機スロット +4 = SP_SHIP0 + 歩行フレーム * 16 + (x2 & 3) * 4
;       歩行フレームは W_TICK の bit4 (16 フレーム周期) で 2 パターン切替
;       → 前進している見た目の歩行アニメになる
; 破壊: A, E, IX, F
; 注意: player_fire は IX を弾スロットへ奪うため、ここで必ず
;       自機スロットを再ロードする (旧実装は奪われた IX のまま
;       書き込むため発射した弾のコードを壊していた)
; ------------------------------------------------------------
player_set_pattern:
        ld ix,O_TBL
        ; 歩行フレーム = (W_TICK >> 4) & 1 → 0 か 16
        ld a,(W_TICK)
        srl a
        srl a
        srl a
        srl a
        and 1
        add a,a
        add a,a
        add a,a
        add a,a                         ; E = フレーム差分 (0 / 16)
        ld e,a
        ; 水平位相 = x2 下位 2bit → 位相 * 4
        ld a,(ix+2)
        and 3
        add a,a
        add a,a                         ; 位相 * 4
        add a,e
        add a,SP_SHIP0
        ld (ix+4),a
        ret

; ------------------------------------------------------------
; 自弾発射
; 入力: なし
; 出力: W_PLRCD = 8, 空き弾スロットへ自弾 1 発
;       (ツイン時は左斜めの 2 発目も生成), SE(射撃) 再生
;       発射位置は 0 未満にならないようクランプする (負ラップ防止)
; 破壊: A, B, C, IX, F
; 注意: ★旧実装は自機 y < 8 で y-8 が 248 にラップし, 描画されない
;         「幽霊弾」が画面外の VRAM/ミラー判定を 60 フレーム続けていた
; ------------------------------------------------------------
player_fire:
        ld a,8
        ld (W_PLRCD),a
        ld a,O_SHOTS
        ld b,4
        call FIND_SLOT
        ret c
        ld a,(O_TBL+2)
        add a,2                         ; x2: 自機中心
        ld c,a
        ld a,(O_TBL+3)
        sub 8                           ; y: 自機上端
        jr nc,PF_Y1
        xor a                           ; y < 8 → 0 にクランプ
PF_Y1:  ld b,a
        ld a,c
        call init_shot_slot
        ; ツインショット (2 発目)
        ld a,(W_PLRTWIN)
        or a
        jr z,PF_SE                      ; SE はツインの有無にかかわらず再生
        ld a,O_SHOTS
        ld b,4
        call FIND_SLOT
        ret c
        ld a,(O_TBL+2)
        sub 4                           ; x2: 左斜め
        jr nc,PF_X2
        xor a                           ; x2 < 4 → 0 にクランプ
PF_X2:  ld c,a
        ld a,(O_TBL+3)
        sub 4
        jr nc,PF_Y2
        xor a
PF_Y2:  ld b,a
        ld a,c
        call init_shot_slot
PF_SE:
        ld de,(W_SESHOT)
        jp play_se

; ------------------------------------------------------------
; 弾スロット共通初期化
; 入力: IX = 弾スロット (FIND_SLOT 成功後), A = x2, B = y
; 出力: +0 = 1 (有効), +1 = 04Ah (バンク1 + 1x1), +2 = x2, +3 = y,
;       +4 = SP_SHOT, +5 = 0
;       (+6/+7 は消去パス管理のため触らない)
; 破壊: A, F (B は保存)
; ------------------------------------------------------------
init_shot_slot:
        push bc
        ld (ix+2),a
        ld (ix+3),b
        ld a,1
        ld (ix+0),a
        ld a,04Ah
        ld (ix+1),a
        ld a,SP_SHOT
        ld (ix+4),a
        xor a
        ld (ix+5),a
        pop bc
        ret

; ------------------------------------------------------------
; 被弾処理
; 入力: なし
; 出力: シールド保持時 → シールド解除 + PLRINV_SHIELD 無敵
;       それ以外 → 死亡処理 (自機消滅, パワーアップ全喪失, 爆発 + SE,
;       W_PREVSTATE 退避, W_STATE = ST_DEATH, 残機 -1, W_STATDIRTY = 1,
;       死亡待ちタイマ 120f, ハイスコア判定)
; 破壊: A, DE, HL, IX, F
; ------------------------------------------------------------
hit_player:
        ld a,(W_PLRINV)
        or a
        ret nz                          ; 無敵中は無効
        ld a,(W_PLRSHIELD)
        or a
        jr z,HP_DIE
        xor a
        ld (W_PLRSHIELD),a
        ld a,PLRINV_SHIELD
        ld (W_PLRINV),a
        ret
HP_DIE:
        ld ix,O_TBL
        ld a,(ix+2)
        ld (W_SCRATCH2),a
        ld a,(ix+3)
        ld (W_SCRATCH2+1),a
        xor a
        ld (ix+0),a                     ; 自機消滅
        ld (W_PLRTWIN),a                ; パワーアップ全喪失 (設計書 5 章)
        ld a,2
        ld (W_PLRSPD),a
        call spawn_expl_scratch
        ld de,(W_SEEXPL)
        call play_se
        ld a,(W_STATE)
        ld (W_PREVSTATE),a
        ld a,ST_DEATH
        ld (W_STATE),a
        ld a,(W_LIVES)
        dec a
        ld (W_LIVES),a
        ld a,1
        ld (W_STATDIRTY),a
        ld hl,120
        ld (W_WAITTIMER),hl             ; 死亡待ちは専用タイマで数える
        ld (W_MSGTIMER),hl              ; 表示側の目安 (描画スキップ判定) として同値も置く
        jp hiscore_check
