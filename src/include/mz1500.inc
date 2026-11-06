; ============================================================
; 鬲泌｢・ｨ主｣ｫ繝代Λ繝・ぅ繧ｪ繝ｳ - MZ-1500 繝上・繝峨え繧ｧ繧｢螳夂ｾｩ
; ============================================================

; --- 繝｡繝｢繝ｪ繝槭ャ繝・---
defc VRAM_TEXT = 0D000h      ; 繝・く繧ｹ繝医く繝｣繝ｩ繧ｯ繧ｿ繧ｳ繝ｼ繝・(40x25)
defc VRAM_PCG = 0D400h      ; PCG 繧ｭ繝｣繝ｩ繧ｯ繧ｿ繧ｳ繝ｼ繝・
defc VRAM_ATTR = 0D800h      ; 繝・く繧ｹ繝医き繝ｩ繝ｼ繧｢繝医Μ繝薙Η繝ｼ繝・
defc VRAM_PCGATTR = 0DC00h      ; PCG 繧｢繝医Μ繝薙Η繝ｼ繝・(bit3=陦ｨ遉ｺ, bit7-6=繝舌Φ繧ｯ)
defc MMIO_8255 = 0E000h      ; 8255 PPI (繝｡繝｢繝ｪ繝槭ャ繝励ラ I/O)
defc MMIO_8253 = 0E004h      ; 8253 PIT
defc MMIO_STAT = 0E008h      ; bit7: 0=H-BLANK荳ｭ 1=陦ｨ遉ｺ荳ｭ (隱ｭ縺ｿ蜃ｺ縺・
defc WORK_BOTTOM = 0B000h      ; 繧ｲ繝ｼ繝繝ｯ繝ｼ繧ｯ鬆伜沺蜈磯ｭ
defc MIRROR_TOP = 0B400h      ; 繝励Ξ繧､繝輔ぅ繝ｼ繝ｫ繝・PCG 繧ｳ繝ｼ繝峨Α繝ｩ繝ｼ (880B)
defc STACK_TOP = 0BF00h      ; 繧ｹ繧ｿ繝・け鬆らせ

; --- 繝舌Φ繧ｯ蛻・ｊ譖ｿ縺医・繝ｼ繝・(OUT 蜻ｽ莉､) ---
defc PORT_RAM_LOW = 0E0h        ; 0000h-0FFFh 繧・RAM 縺ｸ
defc PORT_RAM_HIGH = 0E1h        ; D000h-FFFFh 繧・RAM 縺ｸ
defc PORT_ROM_LOW = 0E2h        ; 0000h-0FFFh 繧偵Δ繝九ち ROM 縺ｸ
defc PORT_VRAM = 0E3h        ; D000h-FFFFh 繧・VRAM & I/O 縺ｸ
defc PORT_PCG_B = 0E5h        ; PCG 繝｢繝ｼ繝・ON (荳倶ｽ・bit: 1=B 2=R 3=G)
defc PORT_PCG_OFF = 0E6h        ; PCG 繝｢繝ｼ繝・OFF

; --- 繝薙ョ繧ｪ蛻ｶ蠕｡繝昴・繝・(OUT 蜻ｽ莉､) ---
defc PORT_PRIORITY = 0F0h        ; bit0=PCG陦ｨ遉ｺ bit1=PCG蜑埼擇
defc PORT_PALETTE = 0F1h        ; bit6-4=繝代Ξ繝・ヨ逡ｪ蜿ｷ bit2-0=濶ｲ
defc PORT_PSG_L = 0F2h        ; PSG 1 (蟾ｦ)
defc PORT_PSG_R = 0F3h        ; PSG 2 (蜿ｳ)
defc PORT_PSG_LR = 0E9h        ; 荳｡ PSG 蜷梧凾
defc PORT_CHAINLOAD = 0EA0Eh      ; EXT.ROM 谺｡繝輔ぃ繧､繝ｫ繝ｭ繝ｼ繝牙ｮ溯｡・(JP 蜈・

; --- 8255 PPI (LD 蜻ｽ莉､縺ｧ繧｢繧ｯ繧ｻ繧ｹ) ---
defc PPI_PORTA = 0E000h      ; 繧ｭ繝ｼ繝懊・繝峨せ繝医Ο繝ｼ繝門・蜉・(bit0-3)
defc PPI_PORTB = 0E001h      ; 繧ｭ繝ｼ繝槭ヨ繝ｪ繧ｯ繧ｹ蜈･蜉・(謚ｼ荳・bit=0)
defc PPI_PORTC = 0E002h      ; bit7: 0=V-BLANK荳ｭ
defc PPI_CONTROL = 0E003h      ; 蛻ｶ蠕｡繝ｯ繝ｼ繝・/ 繝薙ャ繝医そ繝・ヨ繝ｪ繧ｻ繝・ヨ
defc PPI_MODE_ALLIN = 089h        ; PA=out PB=in PC=in (mode 0)

; --- 8253 PIT (LD 蜻ｽ莉､縺ｧ繧｢繧ｯ繧ｻ繧ｹ) ---
defc PIT_CH0 = 0E004h
defc PIT_CH1 = 0E005h
defc PIT_CH2 = 0E006h
defc PIT_CONTROL = 0E007h
defc PIT_CTRL_CH1_M2 = 074h        ; ch1 mode2 RW16 (襍ｰ譟ｻ邱壹け繝ｭ繝・け)
defc PIT_CTRL_CH2_M0 = 0B0h        ; ch2 mode0 RW16 (INT 繝ｯ繝ｳ繧ｷ繝ｧ繝・ヨ)

; --- BIOS / 繝｢繝九ち ROM 繧ｨ繝ｳ繝医Μ ---
defc BIOS_PNT_VIA_WA = 00DDCh      ; A>=C0h: 繝ｯ繝ｼ繧ｯ繧ｨ繝ｪ繧｢ 1171h 縺ｮ蠎ｧ讓吶∈繧ｫ繝ｼ繧ｽ繝ｫ險ｭ螳・
defc BIOS_MSG = 00015h      ; DE=譁・ｭ怜・(00h邨らｫｯ) 繧定｡ｨ遉ｺ
defc BIOS_KEYFLUSH = 0003Eh      ; 繧ｭ繝ｼ繝舌ャ繝輔ぃ髢｢騾｣蛻晄悄蛹・
defc BIOS_INKEY = 0001Bh      ; 1 譁・ｭ怜・蜉・(謚ｼ縺吶∪縺ｧ蠕・▽, A=繧ｳ繝ｼ繝・
defc BIOS_POINTXY = 01171h      ; PNT 繝ｯ繝ｼ繧ｯ繧ｨ繝ｪ繧｢ (L=X H=Y)

; --- 繧ｭ繝ｼ繝槭ヨ繝ｪ繧ｯ繧ｹ (繧ｹ繝医Ο繝ｼ繝・0-9 x bit0-7, 謚ｼ荳・0) ---
defc KEY_STROBE_0 = 0F0h        ; bit0=CR
defc KEY_STROBE_6 = 0F6h        ; bit4=SPACE
defc KEY_STROBE_7 = 0F7h        ; bit2=蟾ｦ bit3=蜿ｳ bit4=荳・bit5=荳・
defc KEY_STROBE_4 = 0F4h        ; bit5=C (繧ｳ繝ｳ繝・ぅ繝九Η繝ｼ)
defc KEYBIT_CR = 001h
defc KEYBIT_LEFT = 004h
defc KEYBIT_RIGHT = 008h
defc KEYBIT_DOWN = 010h
defc KEYBIT_UP = 020h
defc KEYBIT_SPACE = 010h
defc KEYBIT_C = 020h

; --- PCG 螻樊ｧ蛟､ ---
defc PCGATTR_BANK0 = 008h        ; 繝舌Φ繧ｯ0 陦ｨ遉ｺon
defc PCGATTR_BANK1 = 048h        ; 繝舌Φ繧ｯ1
defc PCGATTR_BANK2 = 088h        ; 繝舌Φ繧ｯ2
defc PCGATTR_BANK3 = 0C8h        ; 繝舌Φ繧ｯ3

; --- 逕ｻ髱｢ ---
defc SCREEN_W = 40
defc SCREEN_H = 25
defc FIELD_ROWS = 22          ; 繝励Ξ繧､繝輔ぅ繝ｼ繝ｫ繝芽｡梧焚 (陦・-21)
defc FIELD_BYTES = 880         ; 22 x 40
defc STATUS_ROW = 23
