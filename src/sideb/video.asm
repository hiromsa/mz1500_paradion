; ============================================================
; ビデオプリミティブ: V-BLANK 同期 / VRAM 初期化 / セル描画・消去
; (オブジェクトの描画パスは render.asm)
; ============================================================

; ------------------------------------------------------------
; V-BLANK 開始待ち (8255 PC7: 0 = V-BLANK 中)
; 入力: なし
; 出力: V-BLANK 開始までブロック
; 破壊: A, F
; ------------------------------------------------------------
wait_vblank_start:
        ld a,(PPI_PORTC)
        bit 7,a
        jr z,wait_vblank_start          ; まず表示期間まで待つ
WVS1:   ld a,(PPI_PORTC)
        bit 7,a
        jr nz,WVS1                      ; V-BLANK 開始を待つ
        ret

; ------------------------------------------------------------
; V-BLANK 終了待ち
; 入力: なし
; 出力: V-BLANK 終了 (表示期間の先頭) までブロック
; 破壊: A, F
; ------------------------------------------------------------
wait_vblank_end:
        ld a,(PPI_PORTC)
        bit 7,a
        jr z,wait_vblank_end            ; V-BLANK 終了を待つ
        ret

; ------------------------------------------------------------
; VRAM 初期化 (テキスト / PCG コード / 属性クリア + 優先度設定)
; 入力: なし
; 出力: VRAM 全領域クリア, PCG 表示 + PCG 前面, スコア欄初期化
; 破壊: A, B, C, DE, HL, F
; ------------------------------------------------------------
video_init:
        ld hl,VRAM_TEXT                 ; テキスト+PCG コード+属性クリア
        ld de,VRAM_TEXT+1
        ld bc,0FFFh
        ld (hl),0
        ldir
        ld hl,VRAM_ATTR                 ; テキスト属性: 白/黒
        ld de,VRAM_ATTR+1
        ld bc,03FFh
        ld (hl),070h
        ldir
        ld a,03h
        out (PORT_PRIORITY),a           ; PCG 表示 + PCG 前面
        call status_init
        ret

; ------------------------------------------------------------
; スコア欄ラベル + PCG 属性初期化
; 入力: なし
; 出力: 行 23 に SCORE / HI / REST / STAGE ラベルと PCG 属性を設定
; 破壊: A, DE, HL, F
; ------------------------------------------------------------
status_init:
        ld hl,VRAM_TEXT + 23*40 + 0
        ld de,LBL_SCORE
        call print_msg
        ld hl,VRAM_TEXT + 23*40 + 12
        ld de,LBL_HI
        call print_msg
        ld hl,VRAM_TEXT + 23*40 + 21
        ld de,LBL_REST
        call print_msg
        ld hl,VRAM_TEXT + 23*40 + 30
        ld de,LBL_STAGE
        call print_msg
        ; PCG 属性設定 (スコア桁/ハイ/残機/ステージ桁)
        ld hl,0DC00h + 23*40 + 6
        call set_status_attr6
        ld hl,0DC00h + 23*40 + 15
        call set_status_attr6
        ld a,PCGATTR_BANK0
        ld (0DC00h + 23*40 + 26),a      ; ハートアイコン
        ld (0DC00h + 23*40 + 27),a      ; 残機数
        ld (0DC00h + 23*40 + 36),a      ; ステージ数
        ret

; ------------------------------------------------------------
; PCG 属性 6 セル設定 (スコア欄桁用)
; 入力: HL = 設定先 (PCG 属性 VRAM)
; 出力: 6 セルに PCGATTR_BANK0 を書き込み
; 破壊: A, C, F (HL は +6 進む)
; ------------------------------------------------------------
set_status_attr6:
        ld c,6
SSA1:   ld (hl),PCGATTR_BANK0
        inc hl
        dec c
        jr nz,SSA1
        ret

; ------------------------------------------------------------
; 文字列描画 (ディスプレイコード)
; 入力: HL = VRAM 転送先, DE = 文字列 (00h 終端)
; 出力: 00h 直前まで VRAM へ転送
; 破壊: A, DE, HL, F
; ------------------------------------------------------------
print_msg:
        ld a,(de)
        or a
        ret z
        ld (hl),a
        inc hl
        inc de
        jr print_msg

; ------------------------------------------------------------
; セルアドレス計算
; 入力: B = col (0-39), C = row (0-24)
; 出力: HL = VRAM_PCG + row * 40 + col (コード領域アドレス)
; 破壊: DE, HL, F (A, B, C は保存)
; ------------------------------------------------------------
CELLADDR:
        push bc
        ld l,c
        ld h,0
        add hl,hl
        push hl
        add hl,hl
        add hl,hl                       ; 8r
        ld e,l
        ld d,h
        pop hl                          ; 2r
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl                       ; 32r
        add hl,de                       ; 40r
        ld e,b
        ld d,0
        add hl,de
        ld bc,VRAM_PCG
        add hl,bc
        pop bc
        ret

; ------------------------------------------------------------
; 2x2 セル描画 (16x16 ドット)
; 入力: HL = 左上セル (VRAM_PCG 基準), B = 左上コード, C = 属性
; 出力: コード 4 セル + 属性 4 セルを描画
; 破壊: B, DE, HL, F (C は保存)
; ------------------------------------------------------------
DRAW2X2:
        ld (hl),b                       ; TL
        inc b
        inc hl
        ld (hl),b                       ; TR
        push hl
        ld de,39
        add hl,de                       ; BL
        inc b
        ld (hl),b
        inc b
        inc hl
        ld (hl),b                       ; BR
        ; 属性 (DC00 = セル + 800h)
        ld de,0800h
        add hl,de                       ; BR attr
        ld (hl),c
        dec hl
        ld (hl),c                       ; BL attr
        ld de,-40
        add hl,de                       ; TL attr
        ld (hl),c
        inc hl
        ld (hl),c                       ; TR attr
        pop hl
        ret

; ------------------------------------------------------------
; 1x1 セル描画 (8x8 ドット)
; 入力: HL = セル (VRAM_PCG 基準), B = コード, C = 属性
; 出力: コード + 属性を描画
; 破壊: DE, HL, F (B, C は保存)
; ------------------------------------------------------------
DRAW1X1:
        ld (hl),b
        ld de,0800h
        add hl,de
        ld (hl),c
        ret

; ------------------------------------------------------------
; 2x2 セル消去 → 地形コードへ復元
; 入力: HL = 左上ミラーセル (0B400h 基準, 描画時に保存したアドレス)
; 出力: コード 4 セルをミラーから復元, 属性 4 セルを PCGATTR_BANK0 へ
; 破壊: A, B, C, DE, HL, F
; ★注意: 旧実装は BR 値を D に保持したまま `ld de,39` を再ロードし、
;   D が 00h に壊された状態で `ld (hl),d` するため、自機 (2x2) 右下セルに
;   常に 00h (黒) を書き込んでいた (スクロールで黒列として焼き付く)。
;   本実装では BR 値を書き込み時にミラーから直接読み直す。
; ------------------------------------------------------------
ERASE2X2:
        push hl
        ld de,2000h
        add hl,de                       ; VRAM セル
        push hl
        or a
        ld bc,2000h
        sbc hl,bc                       ; ミラーへ戻る
        ld a,(hl)                       ; TL
        inc hl
        ld b,(hl)                       ; TR
        ld de,39
        add hl,de                       ; ミラー BL
        ld c,(hl)                       ; BL
        pop hl                          ; HL = VRAM セル
        ld (hl),a                       ; TL
        inc hl
        ld (hl),b                       ; TR
        ld de,39
        add hl,de                       ; VRAM BL
        ld (hl),c
        inc hl                          ; VRAM BR
        push hl
        ld de,2000h
        or a
        sbc hl,de                       ; ミラー BR
        ld a,(hl)                       ; ★BR 値はここで読む (D レジスタ経由にしない)
        pop hl
        ld (hl),a
        ld de,0800h
        add hl,de                       ; BR attr
        ld (hl),PCGATTR_BANK0
        dec hl
        ld (hl),PCGATTR_BANK0
        ld de,-40
        add hl,de                       ; TL attr
        ld (hl),PCGATTR_BANK0
        inc hl
        ld (hl),PCGATTR_BANK0
        pop hl
        ret

; ------------------------------------------------------------
; 1x1 セル消去 → 地形コードへ復元
; 入力: HL = ミラーセル (0B400h 基準)
; 出力: コードをミラーから復元, 属性を PCGATTR_BANK0 へ
; 破壊: A, DE, HL, F
; ------------------------------------------------------------
ERASE1X1:
        ld de,2000h
        add hl,de                       ; HL = VRAM cell
        push hl
        or a
        ld bc,2000h
        sbc hl,bc                       ; HL = mirror cell
        ld a,(hl)
        pop hl
        ld (hl),a                       ; コード復元
        ld de,0800h                     ; PCG 属性は DC00 基準 = セル + 800h
        add hl,de
        ld (hl),PCGATTR_BANK0
        ret

; ------------------------------------------------------------
; 2x2 セル属性のみ消去 (コード復元なし)
; 入力: HL = 右下セル (VRAM_PCG 基準)
; 出力: 属性 4 セルを PCGATTR_BANK0 へ
; 破壊: DE, HL, F
; ------------------------------------------------------------
ERASEATTR2X2:
        ; HL=BRセル: 属性4セルをバンク0へ戻す
        ld de,0800h
        add hl,de
        ld (hl),PCGATTR_BANK0
        dec hl
        ld (hl),PCGATTR_BANK0
        ld bc,-40
        add hl,bc
        ld (hl),PCGATTR_BANK0
        inc hl
        ld (hl),PCGATTR_BANK0
        ret
; ------------------------------------------------------------
; スプライト PCG 復元 + 透過合成 (統合処理)
; 入力: なし (面の地面タイルは W_STAGE から GRND_TBL で引く)
; 出力: SPRC_TBL の各範囲 (バンク 1-3) を初期データ (SPRC_SRC, pcggen 生成)
;       から PCG-RAM へ転送しつつ, 透過 (3 プレーン全 0) のピクセルへ
;       その面の地面タイル模様を下地として合成する (ピクセル単位)。
;       平坦なフィールド色で塗る旧方式と違い, 地面の上では下地が
;       地形模様そのものになるためスプライト周囲に四角い継ぎ目が
;       出ない。終了時に D000h-EFFFh を VRAM & I/O へ戻す。
;       復元するのは前の面で合成した絵が残り, 次の面で透過として
;       検出できなくなるバグへの対策
; 破壊: A, B, C, D, E, HL, IX, IY, F (呼び出し側 HL は push/pop で保護)
; 注意: OUT E5h 選択中は VRAM/MMIO (E002 の V-BLANK 読み含む) が見えない
;       ため, init_stage の VRAM 転送完了直後 (描画/メッセージの前) に
;       1 回だけ呼ぶこと (ステージ切替時の一瞬の静止になる)
; ------------------------------------------------------------
sprite_recolor_field:
        push hl                         ; 呼び出し側の HL を保護
; 下地に使う地面タイル (左上コード) を面番号から取得
        ld a,(W_STAGE)
        dec a
        ld hl,GRND_TBL
        ld e,a
        ld d,0
        add hl,de
        ld a,(hl)
        ld (W_RFGRND),a                 ; 面の地面タイル左上コード
        ld hl,SPRC_TBL
        ld (W_RFTBL),hl                 ; 置換対象テーブルポインタ (HL は置換で使う)
        ld hl,SPRC_SRC
        ld (W_RFDP),hl                  ; 復元データの src カーソル (SPRC_TBL 並順)
SRF_BANK:
        ld hl,(W_RFTBL)
        ld a,(hl)
        or a
        jp z,SRF_DONE                   ; 終端 (bank = 0)
        inc hl
        ld e,(hl)                       ; E = 開始コード
        inc hl
        ld b,(hl)                       ; B = コード数
        inc hl
        ld (W_RFTBL),hl                 ; テーブルポインタ次エントリへ
; src base = SPRC_SRC カーソル + start × 24
        ld hl,(W_RFDP)
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a                          ; HL = 復元データ base
        push hl                         ; base を退避
        ld a,e                          ; A = start
        ld e,a
        ld d,0
        ld h,d
        ld l,e                          ; HL = start
        add hl,hl                       ; × 2
        add hl,hl                       ; × 4
        add hl,hl                       ; × 8
        push hl                         ; start × 8 を退避
        add hl,hl                       ; × 16
        pop de                          ; DE = start × 8
        add hl,de                       ; HL = start × 24
        pop de                          ; DE = base
        add hl,de                       ; HL = src = base + start × 24
        ld (W_RFSRC),hl                 ; 転送用 src ポインタ (SRF_COPY8 が進める)
        ld hl,(W_RFDP)
        inc hl
        inc hl
        ld (W_RFDP),hl                  ; SPRC_SRC カーソル次エントリへ
; PCG 窓アドレス = D000h + bank × 800h + start × 8
        ld hl,(W_RFTBL)
        dec hl
        dec hl
        dec hl
        ld a,(hl)                       ; A = bank
        inc hl
        ld e,(hl)                       ; E = 開始コード (pop de で失われるため再取得)
        ld c,e                          ; C = 現在処理中のコード (下地の象限判定用)
        add a,a
        add a,a
        add a,a                         ; bank × 8
        ld h,a
        ld l,0                          ; HL = bank × 800h
        ld d,0
        sla e
        rl d
        sla e
        rl d
        sla e
        rl d                            ; DE = start × 8
        add hl,de
        ld de,0D000h
        add hl,de                       ; HL = PCG ウィンドウ上の開始アドレス
        push hl
        pop ix                           ; IX = 走査位置
SRF_CODE:
        push bc                         ; B (残り文字数) と C (現在コード) を退避
; --- 復元転送: 初期データ 24 バイト (B/R/G × 8 行) を PCG へ ---
        ld a,001h
        out (PORT_PCG_B),a              ; B プレーン選択
        call SRF_COPY8
        ld a,002h
        out (PORT_PCG_B),a              ; R プレーン選択
        call SRF_COPY8
        ld a,003h
        out (PORT_PCG_B),a              ; G プレーン選択
        call SRF_COPY8
; 下地ポインタ IY = 地面タイルの当該象限 (コード下位 2 ビット) の先頭
        ld a,c
        and 3                           ; 象限 (0=左上, 1=右上, 2=左下, 3=右下)
        ld e,a
        ld a,(W_RFGRND)
        add a,e                         ; 地面サブキャラのコード
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl                       ; x8 (1 文字 = 8 バイト)
        ld de,0D000h
        add hl,de                       ; バンク 0 の窓アドレス
        push hl
        pop iy                          ; IY = 下地走査位置 (行ごとに IX と同期)
        ld d,8                          ; D = 行カウンタ (1 文字 = 8 行)
SRF_ROW:
        ; 3 プレーンを読み, 黒 (3 プレーン全 0) のピクセルビットを求める
        ld a,001h
        out (PORT_PCG_B),a              ; B プレーン選択
        ld l,(ix+0)                     ; L = B プレーン
        ld a,002h
        out (PORT_PCG_B),a              ; R プレーン選択
        ld h,(ix+0)                     ; H = R プレーン
        ld a,003h
        out (PORT_PCG_B),a              ; G プレーン選択
        ld e,(ix+0)                     ; E = G プレーン
        ld a,l
        or h
        or e
        cpl
        ld h,a                          ; H = 透過ピクセルマスク (R 値は下で再読)
        ; B プレーン: B | (下地 B & 透過マスク)
        ld a,001h
        out (PORT_PCG_B),a              ; B プレーン選択 (下地も同じ窓で読める)
        ld a,(iy+0)                     ; 下地 B
        and h
        or l
        push af                         ; 新 B 値を退避
        ; R プレーン: R | (下地 R & 透過マスク)
        ld a,002h
        out (PORT_PCG_B),a
        ld l,(ix+0)                     ; R 値を再読
        ld a,(iy+0)                     ; 下地 R
        and h
        or l
        push af                         ; 新 R 値を退避
        ; G プレーン: G | (下地 G & 透過マスク) → その場で書換
        ld a,003h
        out (PORT_PCG_B),a
        ld l,(ix+0)                     ; G 値を再読
        ld a,(iy+0)                     ; 下地 G
        and h
        or l
        ld (ix+0),a                     ; G プレーン書換
        ; R プレーン書換
        ld a,002h
        out (PORT_PCG_B),a
        pop af
        ld (ix+0),a
        ; B プレーン書換
        ld a,001h
        out (PORT_PCG_B),a
        pop af
        ld (ix+0),a
SRF_NROW:
        inc ix
        inc iy                          ; 下地も次の行へ
        dec d
        jr nz,SRF_ROW
        pop bc
        inc c                           ; 次のコードへ (下地の象限も進む)
        dec b
        jp nz,SRF_CODE                  ; (合成処理で距離が伸びたため JP)
        jp SRF_BANK
SRF_DONE:
        out (PORT_PCG_OFF),a            ; PCG モード解除 (E6h)
        out (PORT_VRAM),a
        pop hl                          ; 呼び出し側の HL 復帰
        ret
SRF_COPY8:
        ld hl,(W_RFSRC)                 ; 転送元 (HL は直前の処理で窓アドレスになっている)
        ld a,(hl)
        ld (ix+0),a
        inc hl
        ld a,(hl)
        ld (ix+1),a
        inc hl
        ld a,(hl)
        ld (ix+2),a
        inc hl
        ld a,(hl)
        ld (ix+3),a
        inc hl
        ld a,(hl)
        ld (ix+4),a
        inc hl
        ld a,(hl)
        ld (ix+5),a
        inc hl
        ld a,(hl)
        ld (ix+6),a
        inc hl
        ld a,(hl)
        ld (ix+7),a
        inc hl
        ld (W_RFSRC),hl
        ret
