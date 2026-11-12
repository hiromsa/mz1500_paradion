; ============================================================
; ステージ進行: ステージ初期化 / ボス出現判定 / エンディング
; ============================================================

; ------------------------------------------------------------
; ステージ初期化
; 入力: A = ステージ番号 (1-5)
; 出力: W_STATE = ST_FIELD を設定してからステージテーブル内容をワークへ展開,
;       フィールド構築, 自機配置, "STAGE n" バナー表示, W_STATDIRTY = 1,
;       BGM 開始
;       (★旧実装は W_STATE を更新しないため, ST_CLEAR / ST_GAMEOVER から
;         呼ばれた際に状態が戻らず init_stage を毎フレーム再実行し,
;         自機が中央固定・敵もボスも出ない状態に陥っていた)
; 破壊: A, B, C, DE, HL, IX, F
; ------------------------------------------------------------
init_stage:
        ld (W_STAGE),a
        ld a,ST_FIELD
        ld (W_STATE),a                    ; GK_CLEAR / GK_GAMEOVER からの復帰
        ld a,(W_STAGE)
        dec a
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl                       ; x16 (STAGE_LEN)
        ld de,STAGE_TABLE
        add hl,de
        ld (W_STAGETBL),hl
        ld a,(hl)                       ; +0: スクロール間隔
        ld (W_SCROLLINT),a
        ld (W_SCROLLCNT),a
        inc hl
        ld a,(hl)                       ; +1: 敵 spawn 間隔
        ld (W_SPAWNINT),a
        ld (W_SPAWNCNT),a
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)                       ; +2/3: ボス出現フレーム
        ld (W_PLAYTIMER),de
        inc hl
        ld a,(hl)                       ; +4: ボスHP
        ld (W_BOSSHP),a
        inc hl
        ld a,(hl)                       ; +5: ボス攻撃間隔
        ld (W_BOSSFIREINT),a
        ld (W_BOSSFIRE),a
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)                       ; +6/7: マップ行テーブル
        ld (W_MAPROWS),de
        inc hl
        ld a,(hl)                       ; +8: 行数
        ld (W_MAPCNT),a
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)                       ; +9/A: BGM
        push de
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)                       ; +B/C: SE(射撃)
        ld (W_SESHOT),de
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)                       ; +D/E: SE(爆発)
        ld (W_SEEXPL),de
        inc hl
        ld a,(hl)                       ; +F: フィールド色 (スプライト黒の置換色)
        ld (W_FIELDCOL),a               ; メッセージ背景色としても使用
        push af                         ; sprite_recolor_field まで退避
        ld a,(W_MAPCNT)
        dec a
        ld (W_MAPROW),a                 ; 補充開始は末尾行 (fill_row は逆順に遡る)
        ; 雑魚の同時出現上限 = ステージ + 1, 宝箱タイマ初期化
        ld a,(W_STAGE)
        inc a
        ld (W_SPAWNMAX),a
        ld a,CHEST_FIRST_DELAY
        ld (W_CHESTCNT),a
        xor a                           ; ↓ BOSSMODE=0 用に A を戻す
        ld (W_BOSSMODE),a
        ld hl,W_BOSS
        ld de,W_BOSS+1
        ld bc,7
        ld (hl),0
        ldir
        ; 前ステージの敵/弾/アイテム/爆発と描画セル参照を持ち越さない
        ld hl,O_TBL
        ld de,O_TBL+1
        ld bc,O_SLOTS*O_LEN-1
        ld (hl),0
        ldir
        xor a
        ld (W_SCROLLEDUE),a              ; 古いスクロール要求も破棄
        ld (W_TILE_PHASE),a               ; 新しいマップは16x16タイル境界から開始
        ; プレイフィールド構築 (最下行から上へ補充: fill_row の逆順と揃え,
        ; 画面は従来通り 行 0 が最上段の初期配置になる)
        ld hl,MIRROR_TOP+(FIELD_ROWS-1)*40
        ld b,FIELD_ROWS
IS_PF:
        push bc
        push hl
        call fill_row                   ; HL に 40 バイト補充
        pop hl
        ld bc,40
        or a
        sbc hl,bc                       ; 1 行上へ
        pop bc
        djnz IS_PF
        ld hl,MIRROR_TOP
        ld de,VRAM_PCG
        ld bc,FIELD_BYTES
        ldir
        ld hl,0DC00h                    ; PCG 属性 rows0-21 = バンク0 表示on
        ld de,0DC01h
        ld bc,FIELD_BYTES-1
        ld (hl),PCGATTR_BANK0
        ldir
        ; スプライトの透過色 (黒) をこの面のフィールド色へ一括置換
        ; (OUT E5h で PCG ウィンドウへ切替るため VRAM アクセスの前に実施)
        pop af
        call sprite_recolor_field
        ; 自機初期配置 (スロット 0)
        ld ix,O_TBL
        ld a,1
        ld (ix+0),a
        ld a,PCGATTR_BANK1
        ld (ix+1),a
        ld a,76
        ld (ix+2),a                     ; x2 = 中央 (px 152)
        ld a,140
        ld (ix+3),a                     ; y
        ld a,SP_SHIP0
        ld (ix+4),a
        ld (ix+5),0
        ld (ix+6),0
        ld (ix+7),0
        ld a,1
        ld (W_STATDIRTY),a
        ; 開始メッセージ: ゲーム起動直後は "GAME START", それ以外は "STAGE n"
        ld a,(W_FRESH)
        or a
        jr z,IS_STGMSG
        xor a
        ld (W_FRESH),a
        ld hl,MSG_START
        jr IS_MSG
IS_STGMSG:
        ld a,(W_STAGE)
        dec a
        ld hl,STAGE_MSGS
        ld e,a
        ld d,0
        add hl,de
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ex de,hl
IS_MSG:
        ld c,10
        call show_msg
        ld hl,180
        ld (W_MSGTIMER),hl
        pop de
        jp play_bgm                     ; BGM 開始して戻る

; ------------------------------------------------------------
; 道中進行: プレイタイマ減算 → ボス出現
; 入力: なし
; 出力: W_PLAYTIMER が 0 になったら W_BOSS 初期化 + W_BOSSMODE = 0 +
;       W_STATE = ST_BOSS + ボス BGM 開始
;       (同フレームで hit_player が ST_DEATH に遷移させていた場合は
;        何もしない。★旧実装は ST_DEATH を ST_BOSS で上書きし,
;        自機の消えたままのボス戦を開始することがあった)
; 破壊: A, DE, HL, F
; ------------------------------------------------------------
stage_flow:
        ld hl,W_PLAYTIMER
        call timer_dec
        ret nz
        ld a,ST_BOSS
        ld (W_STATE),a
        xor a
        ld (W_BOSSMODE),a
        ld a,1
        ld (W_BOSS+0),a
        ld a,0C9h                       ; バンク3 + anim
        ld (W_BOSS+1),a
        ld a,76                         ; x2 = 中央
        ld (W_BOSS+2),a
        xor a
        ld (W_BOSS+3),a                 ; y=0 (上から降下)
        ; ステージ毎のボス PCG 先頭コード (BOSS_CODE_TBL) を設定
        ld a,(W_STAGE)
        dec a
        ld hl,BOSS_CODE_TBL
        ld e,a
        ld d,0
        add hl,de
        ld a,(hl)
        ld (W_BOSS+4),a
        xor a
        ld (W_BOSS+5),a
        ld (W_BOSS+6),a
        ld (W_BOSS+7),a
        ld de,BGM_BOSS
        jp play_bgm

; ------------------------------------------------------------
; エンディング初期化
; 入力: なし
; 出力: ハイスコア更新判定, プレイフィールド消去, エンディング表示,
;       W_STATE = ST_ENDING, BGM 開始
; 破壊: A, B, C, DE, HL, F
; ------------------------------------------------------------
ending_init:
        call hiscore_check
        ld a,ST_ENDING
        ld (W_STATE),a
        call clear_messages
        ; プレイフィールドを消す
        ld hl,MIRROR_TOP
        ld de,MIRROR_TOP+1
        ld bc,FIELD_BYTES-1
        ld (hl),0
        ldir
        ld hl,VRAM_PCG
        ld de,VRAM_PCG+1
        ld bc,FIELD_BYTES-1
        ld (hl),0
        ldir
        ld hl,MSG_END1
        ld c,8
        call show_msg
        ld hl,MSG_END2
        ld c,10
        call show_msg
        ld hl,MSG_END3
        ld c,12
        call show_msg
        ld hl,MSG_END4
        ld c,16
        call show_msg
        ld de,BGM_CLEAR                 ; エンディングはクリアファンファーレ
        jp play_bgm                     ; (BGM_END は dw ポインタでありストリームではない)
