; ============================================================
; サウンドドライバ (フレーム駆動 / デュアル PSG 分離運用)
; V-BLANK 同期のメインループから 1 フレームに 1 回 sound_update を呼ぶ。
; BGM = PSG1 (左 F2h) / SE = PSG2 (右 F3h) と専用チップを割り当て,
; SE は BGM を中断・上書きせず両者が独立に同時進行する。
; ============================================================
defc V_BGM_PTR = W_WORKTOP + 000h     ; 2B
defc V_BGM_DUR = W_WORKTOP + 002h
defc V_BGM_ACT = W_WORKTOP + 003h
defc V_BGM_LOOP = W_WORKTOP + 004h     ; 2B
defc V_SE_PTR = W_WORKTOP + 006h     ; 2B
defc V_SE_DUR = W_WORKTOP + 008h     ; 1B 現 SE エントリの残り待ちフレーム
defc V_SE_ACT = W_WORKTOP + 009h
defc PORT_PSG_BGM = PORT_PSG_L       ; BGM 専用 (PSG1・左)
defc PORT_PSG_SE = PORT_PSG_R        ; SE 専用 (PSG2・右)


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
; 両 PSG 消音
; 入力: なし
; 出力: 左右両 PSG の全チャンネルを消音
; 破壊: A, B, C, F
; ------------------------------------------------------------
psg_mute:
        ld c,PORT_PSG_BGM               ; 左 PSG (BGM 側)
        call psg_mute_one
        ld c,PORT_PSG_SE                ; 右 PSG (SE 側) は fall-through で処理

; ------------------------------------------------------------
; 片側 PSG の全チャンネル消音
; 入力: C = 対象 PSG ポート (PORT_PSG_BGM / PORT_PSG_SE)
; 出力: 指定 PSG の音量レジスタ ch0-3 を消音 (SN76489 音量 F = 無音)
; 破壊: A, B, C, F
; ------------------------------------------------------------
psg_mute_one:
        ld b,0                          ; out (c),a のポート上位 8bit を 0 に
        ld a,9Fh                        ; ch0 音量 = 消音
        out (c),a
        ld a,0BFh                       ; ch1 音量 = 消音
        out (c),a
        ld a,0DFh                       ; ch2 音量 = 消音
        out (c),a
        ld a,0FFh                       ; ch3 (ノイズ) 音量 = 消音
        out (c),a
        ret

; ------------------------------------------------------------
; フレームごとのサウンド更新 (メインループから呼ばれる)
; 入力: なし
; 出力: BGM/SE 1 tick 進行, W_TICK +1
; 破壊: A, B, C, HL, F
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
; 出力: BGM を左 PSG へ進行 (dur -1, 0 で次エントリ out, FFh でループ点へ)。
;       SE を右 PSG へ独立進行 (dur 待ち + エントリ out, 00h 終端で消音停止)。
;       BGM と SE は別チップなので互いの音を上書きしない
; 破壊: A, B, C, HL, F
; ------------------------------------------------------------
snd_tick:
        call snd_tick_bgm              ; BGM → 左 PSG
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
        out (PORT_PSG_SE),a            ; SE → 右 PSG (BGM と別チップ)
        djnz SEW1
        ld (V_SE_PTR),hl
        ret
SE_FIN:
        xor a
        ld (V_SE_ACT),a
        ld c,PORT_PSG_SE
        jp psg_mute_one                ; 右 PSG の残音を消して停止
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
        out (PORT_PSG_BGM),a           ; BGM → 左 PSG
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
; SE 開始 (次の sound_update から再生)
; 入力: DE = SE ストリーム先頭アドレス ([dur][バイト数][PSG writes...], 00h 終端)
; 出力: V_SE_PTR = DE, V_SE_DUR = 0, V_SE_ACT = 1, 右 PSG 消音
; 破壊: A, F
; ------------------------------------------------------------
play_se:
        ld (V_SE_PTR),de
        xor a
        ld (V_SE_DUR),a                ; 1 エントリ目を即ロード
        ld a,1
        ld (V_SE_ACT),a
        push bc                        ; 前回 SE の残レジスタを消す (BC は保存)
        ld c,PORT_PSG_SE
        call psg_mute_one
        pop bc
        ret
