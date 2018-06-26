; n_quadrado.asm
        @   /0100
INIC    LD  UM     ; Inicializa as variaveis
        MM  CONT   ; com o valor 1
        MM  IMPAR
        MM  N+1

LOOP    LD  CONT   ; Carrega o contador e verifica
        -   N      ; se ja e igual N
        JZ  FORA   ; Se sim, encerra
        LD  CONT   ; Pega o contador
        +   UM     ; Soma 1
        MM  CONT   ; Devolve
        LD  IMPAR  ; Coloca o proximo numero impar
        +   DOIS
        MM  IMPAR
        +   N+1    ; E soma no resultado
        MM  N+1
        JP  LOOP

FORA    LD  N+1    ; Resultado esta em N+1
        OS  /0     ; Mostra o resultado
        CN  /0     ; Halt Machine

        @ /0200    ; Area de Dados
UM      K   01
DOIS    K   02
IMPAR   K   0
N       K   4
        K   0
CONT    K   0

        # INIC
