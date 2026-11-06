; ============================================================
; パワーアップ: 落下 / 取得判定 / 効果適用
; ============================================================

; ------------------------------------------------------------
; パワーアップ更新 (スロット O_PWUPS..+1)
; 入力: なし
; 出力: 落下 y +2 (y >= 176 で消滅), 自機接触で効果適用後消滅
; 破壊: A, B, D, IX, F
; ------------------------------------------------------------
pwups_update:
        ld ix,O_TBL + O_PWUPS*O_LEN
        ld b,2
PUW_L:  ld a,(ix+0)
        or a
        jr z,PUW_N
        ld a,(ix+3)
        add a,2
        cp 176
        jr nc,PUW_KILL
        ld (ix+3),a
        ; 自機との接触 (|dx| < 5 かつ |dy| < 12)
        ; ※B はループカウンタのため一時値には D を使う
        ld d,(ix+2)
        ld a,(O_TBL+2)
        sub d
        jr nc,PUW_AX
        neg
PUW_AX: cp 5
        jr nc,PUW_N
        ld d,(ix+3)
        ld a,(O_TBL+3)
        sub d
        jr nc,PUW_AY
        neg
PUW_AY: cp 12
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
;       更新 (1UP は上限 6) + SE(パワーアップ) 再生
; 破壊: A, DE, F (B は保存 → ループカウンタに影響しない)
; ------------------------------------------------------------
pwup_apply:
        cp SP_PW_TWIN
        jr nz,PWU_S2
        ld a,1
        ld (W_PLRTWIN),a
        jr PWU_SE
PWU_S2: cp SP_PW_SPEED
        jr nz,PWU_S3
        ld a,4
        ld (W_PLRSPD),a
        jr PWU_SE
PWU_S3: cp SP_PW_SHIELD
        jr nz,PWU_S4
        ld a,1
        ld (W_PLRSHIELD),a
        jr PWU_SE
PWU_S4: cp SP_PW_LIFE
        ret nz
        ld a,(W_LIVES)
        cp 6
        jr nc,PWU_SE
        inc a
        ld (W_LIVES),a
        ld a,1
        ld (W_STATDIRTY),a
PWU_SE: ld de,SE_PWUP
        jp play_se
