; ============================================================
; コード部: エントリ / メインループ / 全体初期化
; ============================================================

; ------------------------------------------------------------
; エントリ (← $EA0E がここへジャンプ)
; 入力: なし
; 出力: なし (メインループで無限ループ)
; 破壊: すべて
; ------------------------------------------------------------
START:
        di
        ld sp,STACK_TOP
        out (PORT_ROM_LOW),a            ; 0000h-0FFFh = モニタ ROM (BIOS 用)
        out (PORT_VRAM),a               ; D000h-FFFFh = VRAM & I/O
        call snd_init                   ; 割り込みフック / 8253 / PSG 初期化
        call psg_mute
        call video_init                 ; VRAM クリア / 属性 / 優先度 / スコア欄
        call game_init
        ei
MAIN_LOOP:
        call wait_vblank_start
        call render_objects             ; スクロール + PCG 更新 (V-BLANK 中)
        call wait_vblank_end
        call sound_update               ; BGM/SE とフレームカウンタを 1 回進める
        call game_tick
        jr MAIN_LOOP

; ------------------------------------------------------------
; 全体初期化
; 入力: なし
; 出力: ワークエリア初期化後, A = 1 (Stage 1) で init_stage へ
; 破壊: A, B, C, DE, HL, F
; ------------------------------------------------------------
game_init:
        xor a
        ld (W_TICK),a
        ld hl,0
        ld (W_SCORE),hl                 ; スコア 0 (BCD 3B)
        ld (W_SCORE+2),a
        ld (W_HISCORE),hl
        ld (W_HISCORE+2),a
        ld a,2
        ld (W_LIVES),a                  ; REST = 2
        xor a
        ld (W_PLRTWIN),a
        ld (W_PLRSHIELD),a
        ld (W_PLRINV),a
        ld (W_PLRCD),a
        ld (W_KEYS_PREV),a
        ld (W_RAND),a
        ld (W_RAND+1),a
        ld (W_ITMTIMER),a               ; アイテム名メッセージ非表示
        ld a,1
        ld (W_FRESH),a                  ; 次の init_stage は "GAME START" 表示
        ld a,2
        ld (W_PLRSPD),a
        ; オブジェクトテーブルクリア
        ld hl,O_TBL
        ld de,O_TBL+1
        ld bc,W_WORKTOP-O_TBL-1
        ld (hl),0
        ldir
        ld hl,W_BOSS
        ld de,W_BOSS+1
        ld bc,8
        ld (hl),0
        ldir
        ld a,ST_FIELD
        ld (W_STATE),a
        ld hl,0
        ld (W_MSGTIMER),hl
        ld a,1
        jp init_stage                   ; ★旧実装はフォールスルー (A=1 = Stage 1)
