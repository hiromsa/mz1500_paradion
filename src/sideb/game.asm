; ============================================================
; 状態ディスパッチ: W_STATE 別の 1 フレーム更新
; ============================================================

; ------------------------------------------------------------
; メインティック (状態別ディスパッチ)
; 入力: なし
; 出力: W_STATE に応じた更新一式 (下記 GK_xxx を参照)
; 破壊: すべて (状態別ハンドラに従う)
; ------------------------------------------------------------
game_tick:
        call read_keys
        ld a,(W_STATE)
        cp ST_FIELD
        jp z,GK_FIELD
        cp ST_BOSS
        jp z,GK_BOSS
        cp ST_CLEAR
        jp z,GK_CLEAR
        cp ST_DEATH
        jp z,GK_DEATH
        cp ST_GAMEOVER
        jp z,GK_GAMEOVER
        jp GK_ENDING

; ------------------------------------------------------------
; ST_FIELD: 道中 1 フレーム更新
; 入力: なし
; 出力: 自機 / スクロール / 敵スポーン / 弾 / 敵 / 演出 / 当たり判定 /
;       ボス出現判定 / メッセージ
; 破壊: すべて
; ------------------------------------------------------------
GK_FIELD:
        call player_update
        call scroll_logic
        call spawn_update
        call shots_update
        call eshots_update
        call enemies_update
        call pwups_update
        call expls_update
        call collide_field
        call stage_flow
        call msgs_update
        ret

; ------------------------------------------------------------
; ST_BOSS: ボス戦 1 フレーム更新
; 入力: なし
; 出力: 自機 / 弾 / 敵弾 / 敵 / 演出 / ボス / 当たり判定 / メッセージ
; 破壊: すべて
; ------------------------------------------------------------
GK_BOSS:
        call player_update
        call shots_update
        call eshots_update
        call enemies_update
        call pwups_update
        call expls_update
        call boss_update
        call collide_boss
        call msgs_update
        ret

; ------------------------------------------------------------
; ST_CLEAR: クリア演出 → 次ステージ or エンディング
; 入力: なし
; 出力: 残り演出更新, W_MSGTIMER = 0 で:
;       ステージ < 5 → clear_messages + init_stage (次面)
;       ステージ = 5 → clear_messages + ending_init
; 破壊: A, B, C, DE, HL, IX, F
; ------------------------------------------------------------
GK_CLEAR:
        call shots_update
        call expls_update
        call pwups_update
        ld hl,W_MSGTIMER
        call timer_dec
        ret nz
        ld a,(W_STAGE)
        cp 5
        jr nc,GKC_TOEND
        call clear_messages
        ld a,(W_STAGE)
        inc a
        call init_stage
        ret
GKC_TOEND:
        call clear_messages
        jp ending_init

; ------------------------------------------------------------
; ST_DEATH: 死亡演出 → 復帰 or ゲームオーバー
; 入力: なし
; 出力: W_MSGTIMER (死亡待ちタイマを兼ねる) が 0 になったら:
;       残機 > 0 → W_STATE = W_PREVSTATE 復帰, 自機中央再配置,
;                  W_PLRINV = 60, clear_messages
;       残機 = 0 → hiscore 更新 + W_STATE = ST_GAMEOVER + 表示
;       (msgs_update と二重減算しないようここで直接減算する)
; 破壊: A, C, DE, HL, IX, F
; ------------------------------------------------------------
GK_DEATH:
        call expls_update
        call eshots_update
        ld hl,W_MSGTIMER
        call timer_dec
        ret nz
        ; 復帰 or ゲームオーバー
        ld a,(W_LIVES)
        or a
        jr z,GKD_OVER
        ld a,(W_PREVSTATE)
        ld (W_STATE),a
        ; 自機スロット完全再初期化 (+0..+7: 属性/パターン/消去セル含む)
        ld ix,O_TBL
        ld a,1
        ld (ix+0),a
        ld a,PCGATTR_BANK1
        ld (ix+1),a
        ld a,76                         ; x2 = 中央 (px 152)
        ld (ix+2),a
        ld a,140
        ld (ix+3),a
        ld a,SP_SHIP0
        ld (ix+4),a
        xor a
        ld (ix+5),a
        ld (ix+6),a                     ; 描画済みセルなし (消去パス対象外)
        ld (ix+7),a
        ld a,60
        ld (W_PLRINV),a
        call clear_messages
        ret
GKD_OVER:
        call hiscore_check
        ld a,ST_GAMEOVER
        ld (W_STATE),a
        ld hl,MSG_GAMEOVER
        ld c,10
        call show_msg
        ld hl,MSG_CONT
        ld c,12
        call show_msg
        ret

; ------------------------------------------------------------
; ST_GAMEOVER: コンティニュー待ち
; 入力: なし
; 出力: C キー押下で clear_messages + スコア 0 + 残機 2 +
;       init_stage (現ステージの最初から)
; 破壊: A, DE, F (init_stage / 呼出先に従う)
; ------------------------------------------------------------
GK_GAMEOVER:
        call expls_update
        call eshots_update
        ld a,(W_KEYS)
        bit 6,a                         ; C キー → コンティニュー
        ret z
        call clear_messages
        xor a
        ld (W_SCORE),a
        ld (W_SCORE+1),a
        ld (W_SCORE+2),a
        ld a,2
        ld (W_LIVES),a
        ld a,1
        ld (W_STATDIRTY),a
        ld a,(W_STAGE)
        jp init_stage

; ------------------------------------------------------------
; ST_ENDING: エンディング → タイトル復帰待ち
; 入力: なし
; 出力: CR キー押下で clear_messages + game_init (再スタート)
; 破壊: A, F (呼出先に従う)
; ------------------------------------------------------------
GK_ENDING:
        call msgs_update
        ld a,(W_KEYS)
        bit 5,a                         ; CR → タイトル戻り (再スタート)
        ret z
        call clear_messages
        jp game_init
