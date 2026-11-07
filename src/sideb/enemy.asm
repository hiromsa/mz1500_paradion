; ============================================================
; 敵: 更新 / 種別移動 / スポーン / 撃破
; ============================================================

; ------------------------------------------------------------
; 敵更新 (スロット O_ENEMIES..+5)
; 入力: なし
; 出力: 種別に応じた移動と消滅
;       (種別 1-6: 奇数 = ガーゴイル型 / 偶数 = ウィスプ型)
;       ステージ N では種別 1..N+1 が出現する (spawn_update)
; 破壊: A, B, IX, F
; ------------------------------------------------------------
enemies_update:
        ld ix,O_TBL + O_ENEMIES*O_LEN
        ld b,6
NU_L:   ld a,(ix+0)
        or a
        jr z,NU_N
        inc (ix+5)                      ; t++
        bit 0,a                         ; 種別 bit0 = 移動パターン選択
        jr z,NU_WISP
        call enemy_move_gargoyle        ; 奇数種 = ガーゴイル型
        jr NU_N
NU_WISP:
        call enemy_move_wisp            ; 偶数種 = ウィスプ型
NU_N:   ld de,O_LEN
        add ix,de
        djnz NU_L
        ret

; ------------------------------------------------------------
; ウィスプ型 (種別 2/4/6) 移動: 直進降下, t = 48 で照準弾 1 発
; 入力: IX = 敵スロット
; 出力: y +1px/移動フレーム (y >= 168 で消滅), t=48 で照準弾
;       4 フレームに 1 回は移動をスキップ (全体速度を約 75% に落とす)
; 破壊: A, B, F
; ------------------------------------------------------------
enemy_move_wisp:
        ld a,(ix+5)
        and 3
        cp 3
        ret z                           ; 移動スキップフレーム (速度 75%)
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
; ガーゴイル型 (種別 1/3/5) 移動: 降下 + 16t ごとに水平方向反転
; 入力: IX = 敵スロット
; 出力: y +1px/移動フレーム (y >= 168 で消滅), x 往復
;       4 フレームに 1 回は移動をスキップ (全体速度を約 75% に落とす)
; 破壊: A, F
; ------------------------------------------------------------
enemy_move_gargoyle:
        ld a,(ix+5)
        and 3
        cp 3
        ret z                           ; 移動スキップフレーム (速度 75%)
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
;       生存数が W_SPAWNMAX (= ステージ + 1) 未満のときのみ出現
;       種別 = 1..ステージ+1 から乱数選択 (新しい雑魚が面毎に追加される)
;       x2 = (乱数 & 1Fh) * 4 + 8, y = 0
;       (アイテム持ち敵は廃止 — アイテムは宝箱から出る item.asm)
; 破壊: A, B, C, D, E, IX, F
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
        ; 生存敵数を数え, 上限に達していれば何もしない
        ld hl,O_TBL + O_ENEMIES*O_LEN
        ld b,6
        ld c,0
SPW_CNT:
        ld a,(hl)
        or a
        jr z,SPW_CNTN
        inc c
SPW_CNTN:
        ld de,O_LEN
        add hl,de
        djnz SPW_CNT
        ld a,(W_SPAWNMAX)
        cp c
        ret c                           ; 生存数 >= 上限 → 出現しない
        ld a,O_ENEMIES
        ld b,6
        call FIND_SLOT
        ret c
        ; 種別 = 1..(ステージ+1) を乱数で選ぶ (mod で範囲に丸める)
        ld a,(W_STAGE)
        inc a
        ld e,a                          ; E = 種別数 (2..6)
        call rand8
        and 7
        ld d,a
SPW_MOD:
        ld a,d
        sub e
        jr c,SPW_TOK                    ; d < e になった
        ld d,a
        jr SPW_MOD
SPW_TOK:
        inc d                           ; D = 種別 1..e
        call rand8
        and 1Fh
        add a,a
        add a,a
        add a,8                         ; x2 = (乱数 & 1Fh) * 4 + 8
        ld (ix+2),a
        xor a
        ld (ix+3),a                     ; y = 0
        ld a,089h                       ; attr (バンク2 + anim)
        ld (ix+1),a
        ; パターン = SP_GARG0 + (種別-1) * 8 (全種が等間隔の PCG 割当)
        ld a,d
        dec a
        add a,a
        add a,a
        add a,a
        add a,SP_GARG0
        ld (ix+4),a
        ld a,d
        ld (ix+0),a                     ; 種別 (bit0 = 移動パターン)
        ld (ix+5),0
        ; +6/+7 (描画済みセル) は消去パスが管理するのでここでは触らない
        ret

; ------------------------------------------------------------
; 敵撃破処理
; 入力: HL = 敵スロット先頭
; 出力: 敵消滅 + 敵位置に爆発生成 + 100 点加算
;       (アイテムは落とさない。宝箱を撃って入手する — item.asm)
; 破壊: A, DE, HL, F (IX は保存)
; ------------------------------------------------------------
kill_enemy:
        push ix
        push hl
        inc hl
        inc hl
        ld a,(hl)
        ld (W_SCRATCH2),a               ; 敵 x2
        inc hl
        ld a,(hl)
        ld (W_SCRATCH2+1),a             ; 敵 y
        pop hl
        xor a
        ld (hl),a                       ; 敵消滅
        call spawn_expl_scratch
        ld de,0100h
        call add_score
        pop ix
        ret
