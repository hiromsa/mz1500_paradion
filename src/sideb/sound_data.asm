; ============================================================
; BGM / SE データ (PSG ストリーム: E9h = 両チャンネル同時)
; BGM エントリ: [継続tick][バイト数][PSGバイト列...] / FFh=終端(ループ)
; SE  エントリ: [バイト数][PSGバイト列...] を 1tick 毎に 1 個消費 / 00h=終端
; 音符の周波数: n = 111860 / f(Hz)  (3.579545MHz / 32 / n)
; ============================================================

; ---- 道中 BGM 1 (Am / 6 tick = 0.1 秒 / 音符) ----
BGM_FIELD1:
        db 6, 6, 8Eh,0Fh,90h, 0CCh,1Fh,90h      ; A4 + A3
        db 6, 6, 86h,0Dh,90h, 0CCh,1Fh,90h      ; C5 + A3
        db 6, 6, 8Ah,0Ah,90h, 0CCh,1Fh,90h      ; E5 + A3
        db 6, 6, 8Fh,07h,90h, 0CCh,1Fh,90h      ; A5 + A3
        db 6, 6, 8Fh,08h,90h, 0CFh,27h,90h      ; G5 + F3
        db 6, 6, 8Ah,0Ah,90h, 0CFh,27h,90h      ; E5 + F3
        db 6, 6, 86h,0Dh,90h, 0CFh,27h,90h      ; C5 + F3
        db 6, 6, 8Ah,0Ah,90h, 0CFh,27h,90h      ; E5 + F3
        db 6, 6, 80h,0Ah,90h, 0CBh,23h,90h      ; F5 + G3
        db 6, 6, 8Fh,07h,90h, 0CBh,23h,90h      ; A5 + G3
        db 6, 6, 8Fh,08h,90h, 0CBh,23h,90h      ; G5 + G3
        db 6, 6, 8Ah,0Ah,90h, 0CBh,23h,90h      ; E5 + G3
        db 6, 6, 8Fh,0Bh,90h, 0C6h,2Ah,90h      ; D5 + E3
        db 6, 6, 8Ah,0Ah,90h, 0C6h,2Ah,90h      ; E5 + E3
        db 6, 6, 86h,0Dh,90h, 0C6h,2Ah,90h      ; C5 + E3
        db 6, 6, 8Eh,0Fh,90h, 0C6h,2Ah,90h      ; A4 + E3
        db 0FFh

; ---- 道中 BGM 2 (Dm / 5 tick) ----
BGM_FIELD2:
        db 5, 6, 8Ch,17h,90h, 0C9h,2Fh,90h      ; D4 + D3
        db 5, 6, 80h,14h,90h, 0C9h,2Fh,90h      ; F4 + D3
        db 5, 6, 8Eh,0Fh,90h, 0C9h,2Fh,90h      ; A4 + D3
        db 5, 6, 8Dh,11h,90h, 0C9h,2Fh,90h      ; G4 + D3
        db 5, 6, 8Bh,1Ah,90h, 0C6h,35h,90h      ; C4 + C3
        db 5, 6, 83h,15h,90h, 0C6h,35h,90h      ; E4 + C3
        db 5, 6, 8Dh,11h,90h, 0CCh,1Fh,90h      ; G4 + A3
        db 5, 6, 8Ch,17h,90h, 0CCh,1Fh,90h      ; D4 + A3
        db 0FFh

; ---- ボス戦 BGM ----
BGM_BOSS:
        db 4, 6, 83h,15h,90h, 0C6h,2Ah,90h      ; E4 + E3
        db 4, 6, 8Dh,11h,90h, 0C6h,2Ah,90h      ; G4 + E3
        db 4, 6, 83h,15h,90h, 0C6h,2Ah,90h      ; E4 + E3
        db 4, 6, 8Dh,11h,90h, 0CFh,27h,90h      ; G4 + F3
        db 4, 6, 80h,14h,90h, 0CFh,27h,90h      ; F4 + F3
        db 4, 6, 8Ch,17h,90h, 0C9h,2Fh,90h      ; D4 + D3
        db 4, 6, 80h,14h,90h, 0C9h,2Fh,90h      ; F4 + D3
        db 4, 6, 8Ch,17h,90h, 0C6h,2Ah,90h      ; D4 + E3
        db 0FFh

; ---- ステージクリア / エンディング ファンファーレ ----
BGM_CLEAR:
        db 5, 6, 86h,0Dh,90h, 0C6h,35h,90h      ; C5 + C3
        db 5, 6, 8Ah,0Ah,90h, 0C6h,35h,90h      ; E5 + C3
        db 5, 6, 8Fh,08h,90h, 0CBh,23h,90h      ; G5 + G3
        db 5, 6, 8Bh,06h,90h, 0CBh,23h,90h      ; C6 + G3
        db 30, 4, 9Fh, 0CBh,23h,90h             ; メロディ休み, ベース保持
        db 0FFh
BGM_END:        dw BGM_CLEAR

; ---- SE ----
; 射撃 (ピッチダウン)
SE_SHOT:
        db 3, 8Eh,0Fh,90h
        db 3, 8Ch,12h,90h
        db 3, 8Fh,18h,90h
        db 2, 91h,9Fh
        db 1, 9Fh
        db 0
; 爆発 (ノイズ)
SE_EXPL:
        db 2, 0E7h,90h
        db 2, 0E7h,94h
        db 2, 0E5h,98h
        db 2, 0E4h,9Ch
        db 1, 0FFh
        db 0
; パワーアップ (アルペジオ)
SE_PWUP:
        db 3, 8Bh,06h,90h
        db 3, 87h,08h,90h
        db 3, 87h,04h,90h
        db 3, 83h,03h,90h
        db 1, 9Fh
        db 0
