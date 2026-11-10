; ============================================================
; サウンドドライバ (フレーム駆動 / デュアル PSG)
; V-BLANK 同期のメインループから 1 フレームに 1 回 sound_update を呼ぶ。
; ============================================================
defc V_BGM_PTR = W_WORKTOP + 000h     ; 2B
defc V_BGM_DUR = W_WORKTOP + 002h
defc V_BGM_ACT = W_WORKTOP + 003h
defc V_BGM_LOOP = W_WORKTOP + 004h     ; 2B
defc V_SE_PTR = W_WORKTOP + 006h     ; 2B
defc V_SE_DUR = W_WORKTOP + 008h     ; 1B 現 SE エントリの残り待ちフレーム
defc V_SE_ACT = W_WORKTOP + 009h


; ---- 初期化 ----
; ------------------------------------------------------------
; サウンド初期化 (8255 / PSG ゲート)
; 入力: なし
; 出力: PC2 タイマー割り込みゲート OFF, PC0 サウンドゲート ON,
;       BGM/SE 停止状態
; 破壊: A, HL, F (di は呼び出し側に任せる)
; ------------------------------------------------------------
snd_init:
        di
        ld a,08Bh                       ; 8255 mode 0: PA=out PB=in PC=in
        ld (PPI_CONTROL),a              ; (Port C bit7 = V-BLANK readback)
        ld a,004h                       ; BSR: ensure PC2 timer interrupt gate is closed
        ld (PPI_CONTROL),a
        ld a,001h                       ; BSR: PC0 sound gate on
        ld (PPI_CONTROL),a
        xor a
        ld (V_BGM_ACT),a
        ld (V_SE_ACT),a
        ld (V_SE_DUR),a
        ld (V_BGM_DUR),a
        ret

; ------------------------------------------------------------
; PSG 全チャンネル消音
; 入力: なし
; 出力: 両 PSG のボリュームを 0 に設定
; 破壊: A, F
; ------------------------------------------------------------
psg_mute:
        ld a,9Fh
        out (PORT_PSG_LR),a
        ld a,0BFh
        out (PORT_PSG_LR),a
        ld a,0DFh
        out (PORT_PSG_LR),a
        ld a,0FFh
        out (PORT_PSG_LR),a
        ret

; ------------------------------------------------------------
; フレームごとのサウンド更新 (メインループから呼ばれる)
; 入力: なし
; 出力: BGM/SE 1 tick 進行, W_TICK +1
; 破壊: A, B, HL, F
; ------------------------------------------------------------
sound_update:
        call snd_tick
        ld a,(W_TICK)
        inc a
        ld (W_TICK),a
        ret

; ---- BGM/SE 1 タイク進行 ----
; ------------------------------------------------------------
; サウンドシーケンサ 1 tick 進行
; 入力: なし
; 出力: SE 有効時は SE ストリームを進行 (dur 待ち + エントリ再生,
;       00h 終端で停止), それに加えて BGM 進行 (dur -1, 0 で次エントリ,
;       FFh でループ点へ)
; 破壊: A, B, HL, F
; ------------------------------------------------------------
snd_tick:
        call snd_tick_bgm              ; BGM を先に out (SE が後から上書き)
snd_tick_se:
        ld a,(V_SE_ACT)
        or a
        ret z
        ld a,(V_SE_DUR)
        or a
        jr z,SE_LOAD                   ; dur 切れ → 次エントリ
        dec a
        ld (V_SE_DUR),a
        ret
SE_LOAD:
        ld hl,(V_SE_PTR)
        ld a,(hl)
        or a
        jr z,SE_FIN                    ; 00h = ストリーム終端
        ld (V_SE_DUR),a                ; エントリ先頭 = dur (待ちフレーム)
        inc hl
        ld b,(hl)                      ; 次バイト = PSG 書き込みバイト数
        inc hl
SEW1:   ld a,(hl)
        inc hl
        out (PORT_PSG_LR),a
        djnz SEW1
        ld (V_SE_PTR),hl
        ret
SE_FIN:
        xor a
        ld (V_SE_ACT),a
        ret
snd_tick_bgm:
        ld a,(V_BGM_ACT)
        or a
        ret z
        ld a,(V_BGM_DUR)
        or a
        jr z,BGM_LOAD
        dec a
        ld (V_BGM_DUR),a
        ret
BGM_LOAD:
        ld hl,(V_BGM_PTR)
        ld a,(hl)
        cp 0FFh
        jr z,BGM_REW
        ld (V_BGM_DUR),a
        inc hl
        ld b,(hl)
        inc hl
BGW1:   ld a,(hl)
        inc hl
        out (PORT_PSG_LR),a
        djnz BGW1
        ld (V_BGM_PTR),hl
        ret
BGM_REW:
        ld hl,(V_BGM_LOOP)
        ld (V_BGM_PTR),hl
        xor a
        ld (V_BGM_DUR),a
        ret

; ------------------------------------------------------------
; BGM 開始
; 入力: DE = BGM ストリーム先頭アドレス
; 出力: V_BGM_PTR / V_BGM_LOOP = DE, BGM 再生開始
; 破壊: A, F
; ------------------------------------------------------------
play_bgm:
        ld (V_BGM_PTR),de
        ld (V_BGM_LOOP),de
        xor a
        ld (V_BGM_DUR),a
        ld a,1
        ld (V_BGM_ACT),a
        ret

; ------------------------------------------------------------
; BGM 停止 + PSG 消音
; 入力: なし
; 出力: BGM 停止, 両 PSG 消音
; 破壊: A, F
; ------------------------------------------------------------
stop_bgm:
        xor a
        ld (V_BGM_ACT),a
        jp psg_mute

; ------------------------------------------------------------
; SE 開始 (次の sound_update から再生)
; 入力: DE = SE ストリーム先頭アドレス ([dur][バイト数][PSG writes...], 00h 終端)
; 出力: V_SE_PTR = DE, V_SE_DUR = 0, V_SE_ACT = 1
; 破壊: A, F
; ------------------------------------------------------------
play_se:
        ld (V_SE_PTR),de
        xor a
        ld (V_SE_DUR),a                ; 1 エントリ目を即ロード
        ld a,1
        ld (V_SE_ACT),a
        ret
