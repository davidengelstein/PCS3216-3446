        @    /0100
INIT    +    L0+2 ; commentop
        -    L0+3
        *    L0+4
        SC   SUB1
        CN   /2   ; Modo indireto
        MM   L0
        CN   /0   ; Halt Machine

L0      K    /12
        K    /00

        K    /FF
        K    /0E
        K    2
        K    5

SUB1    $    2
        /    L0+5
        CN   /2   ; Modo indireto
        JP   SUB1

        @    /1200
        K    0

        # INIT
