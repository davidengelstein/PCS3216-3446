        @ /0100
LABEL   +    L0+2 ; commentop
        -    L0+3
        *    L0+4
        CN   /2 ; Modo indireto
        MM   L0

L0      K    /12
        K    /00

        K    /FF
        K    /0E
        K    2
        @    /1200
        K    0
        # LABEL
