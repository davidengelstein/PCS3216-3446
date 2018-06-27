        @   /0030

INIT
LOOP    CN  /2        ; Activate Indirect Mode
        LD  INICIO    ; Indirect load from current address

        IO  /4        ; Put Data, device = 0

        LD  SPACE
        IO  /4        ; Put Space

        LD  INICIO+1  ; Get inicio
        +   ONE       ; Sum 1
        MM  INICIO+1  ; Put it back

        LD  INICIO
        -   FIM
        JZ  END

        JP  LOOP

END     OS  /F        ; End Program

INICIO  $ 2
FIM     $ 2
ONE     K 1
SPACE   K 32
        # INIT
