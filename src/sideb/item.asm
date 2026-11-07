; ============================================================
; パワーアップ / 宝箱: 落下 / 取得判定 / 効果適用 / 宝箱出現・破壊
; ============================================================

; ------------------------------------------------------------
; パワーアップ更新 (スロット O_PWUPS..+1, 16x16 スプライト)
; 入力: なし
; 出力: 寿命タイマ (+5) 減算, 0 で消滅。宝箱の位置に出現し, スクロールと
;       一緒に地形の上を流れる (y 更新は do_scroll_shift)。
; 破壊: A, B, D, IX, F
; ------------------------------------------------------------
pwups_update:
        ld ix,O_TBL + O_PWUPS*O_LEN
        ld b,2
PUW_L:  ld a,(ix+0)
        or a
        jr z,PUW_N
        ; 寿命タイマ減算 (0 になったら消滅, 出現位置から移動はしない)
        ld a,(ix+5)
        or a
        jr z,PUW_KILL
        dec a
        ld (ix+5),a
        ; 自機との接触 (16x16 同士: |dx| < 8 かつ |dy| < 14)
        ; ※B はループカウンタのため一時値には D を使う
        ld d,(ix+2)
        ld a,(O_TBL+2)
        sub d
        jr nc,PUW_AX
        neg
PUW_AX: cp 8
        jr nc,PUW_N
        ld d,(ix+3)
        ld a,(O_TBL+3)
        sub d
        jr nc,PUW_AY
        neg
PUW_AY: cp 14
        jr nc,PUW_N
        ld a,(ix+4)
        push af                         ; コード退避 (A は下で潰れる)
        xor a
        ld (ix+0),a                     ; 先に消滅させてから適用
        pop af
        call pwup_apply
        jr PUW_KILL
PUW_KILL:
        xor a
        ld (ix+0),a
PUW_N:  ld de,O_LEN
        add ix,de
        djnz PUW_L
        ret

; ------------------------------------------------------------
; パワーアップ効果適用
; 入力: A = パワーアップコード (SP_PW_xxx)
; 出力: コードに応じ W_PLRTWIN / W_PLRSPD / W_PLRSHIELD / W_LIVES を
;       更新 (1UP は上限 6) + アイテム名を画面中央 (行 8) に表示 +
;       SE(パワーアップ) 再生
; 破壊: A, DE, HL, F (B は保存 → ループカウンタに影響しない)
; ------------------------------------------------------------
pwup_apply:
        cp SP_PW_TWIN
        jr nz,PWU_S2
        ld a,1
        ld (W_PLRTWIN),a
        ld hl,MSG_ITWIN                 ; "TWIN SHOT"
        jr PWU_MSG
PWU_S2: cp SP_PW_SPEED
        jr nz,PWU_S3
        ld a,4
        ld (W_PLRSPD),a
        ld hl,MSG_ISPEED                ; "SPEED UP"
        jr PWU_MSG
PWU_S3: cp SP_PW_SHIELD
        jr nz,PWU_S4
        ld a,1
        ld (W_PLRSHIELD),a
        ld hl,MSG_ISHIELD               ; "SHIELD"
        jr PWU_MSG
PWU_S4: cp SP_PW_LIFE
        jr nz,PWU_RET
        ld a,(W_LIVES)
        cp 6
        jr nc,PWU_MSG                   ; 上限 6 → 加算せず表示だけ
        inc a
        ld (W_LIVES),a
        ld a,1
        ld (W_STATDIRTY),a
        ld hl,MSG_ILIFE                 ; "1 UP"
PWU_MSG:
        call show_item_msg
        ld de,SE_PWUP
        jp play_se
PWU_RET:
        ret

; ------------------------------------------------------------
; 宝箱更新 (スロット O_CHEST, 16x16)
; 入力: なし
; 出力: W_CHESTCNT 減算, 0 で空いていれば宝箱を上から出現させる。
;       出現中は敵と同じ速度 (75%) で降下し, y >= 168 で消滅
; 破壊: A, B, DE, IX, F
; ------------------------------------------------------------
chest_update:
        ; 出現タイマ
        ld a,(W_CHESTCNT)
        or a
        jr z,CU_SPAWN
        dec a
        ld (W_CHESTCNT),a
        jr CU_MOVE
CU_SPAWN:
        ld a,CHEST_SPAWN_INT
        ld (W_CHESTCNT),a
        ld a,O_CHEST
        ld b,1
        call FIND_SLOT
        ret c                           ; 既に宝箱が出ている
        call rand8
        and 1Fh
        add a,a
        add a,a
        add a,8                         ; x2 = (乱数 & 1Fh) * 4 + 8
        ld (ix+2),a
        xor a
        ld (ix+3),a                     ; y = 0
        ld (ix+5),a
        ld a,1
        ld (ix+0),a
        ld a,PCGATTR_BANK2
        ld (ix+1),a                     ; バンク2, アニメなし
        ld a,SP_CHEST
        ld (ix+4),a
        ; +6/+7 (描画済みセル) は消去パスが管理するのでここでは触らない
CU_MOVE:
        ; 宝箱は地形と一緒に動く (地面に置いてあるイメージ)。
        ; y の更新と画面下への取り逃し消滅は do_scroll_shift が行う
        ret

; ------------------------------------------------------------
; 自弾 × 宝箱
; 入力: なし
; 出力: 命中弾消滅 + chest_open (宝箱破壊 → 爆発 + アイテム出現)
; 破壊: A, B, DE, IX, F
; ------------------------------------------------------------
shots_vs_chest:
        ld a,(O_TBL + O_CHEST*O_LEN + 0)
        or a
        ret z                           ; 宝箱未出現
        ld ix,O_TBL + O_SHOTS*O_LEN
        ld b,4
SVC_L:  push bc
        push ix
        ld a,(ix+0)
        or a
        jr z,SVC_N
        ; |dx| < 8 (16x16 宝箱の横幅)
        ld a,(ix+2)
        ld e,a
        ld a,(O_TBL + O_CHEST*O_LEN + 2)
        sub e
        jr nc,SVC_A1
        neg
SVC_A1: cp 8
        jr nc,SVC_N
        ; |dy| < 16 (宝箱の縦幅)
        ld a,(ix+3)
        ld e,a
        ld a,(O_TBL + O_CHEST*O_LEN + 3)
        sub e
        jr nc,SVC_A2
        neg
SVC_A2: cp 16
        jr nc,SVC_N
        xor a
        ld (ix+0),a                     ; 弾消滅
        call chest_open
SVC_N:  pop ix
        pop bc
        ld de,O_LEN
        add ix,de
        djnz SVC_L
        ret

; ------------------------------------------------------------
; 宝箱を開ける (破壊処理)
; 入力: なし
; 出力: 宝箱消滅 + 爆発 + SE + 200 点 + ランダムなパワーアップ出現
; 破壊: A, B, DE, IX, F
; ------------------------------------------------------------
chest_open:
        ld a,(O_TBL + O_CHEST*O_LEN + 2)
        ld (W_SCRATCH2),a               ; 宝箱 x2
        ld a,(O_TBL + O_CHEST*O_LEN + 3)
        ld (W_SCRATCH2+1),a             ; 宝箱 y
        xor a
        ld (O_TBL + O_CHEST*O_LEN + 0),a ; 宝箱消滅
        call spawn_expl_scratch
        ld de,0200h
        call add_score                  ; 宝箱 200 点
        ld de,(W_SEEXPL)
        call play_se
        ; 空きパワーアップスロットへランダムなアイテムを出す
        ld a,O_PWUPS
        ld b,2
        call FIND_SLOT
        ret c
        ld a,1
        ld (ix+0),a
        ld a,PCGATTR_BANK1
        ld (ix+1),a                     ; バンク1, 16x16
        ld a,(W_SCRATCH2)
        ld (ix+2),a
        ld a,(W_SCRATCH2+1)
        ld (ix+3),a
        call rand8
        and 3
        ld hl,PWUP_TBL
        ld e,a
        ld d,0
        add hl,de
        ld a,(hl)
        ld (ix+4),a
        ld a,PWUP_LIFE
        ld (ix+5),a                     ; 寿命タイマ初期化 (約 4 秒)
        ; +6/+7 (描画済みセル) は消去パスが管理するのでここでは触らない
        ret
