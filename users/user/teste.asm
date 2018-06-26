        @    /0100
INIT    +    L0+2 ; ACC = FF
        -    L0+3 ; ACC = F1
        *    L0+4 ; ACC = E2
        SC   SUB1 ; Teste subrotina
        CN   /2   ; Modo indireto
        MM   L0
        OS   /0   ; Show data
        CN   /0   ; Halt Machine

L0      K    /12
        K    /00

        K    /FF
        K    /0E
        K    2
        K    5

SUB1    $    2
        /    L0+5 ; ACC = FA
        CN   /2   ; Modo indireto
        JP   SUB1

        @    /1200
        K    0

        # INIT
