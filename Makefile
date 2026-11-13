CC     = gcc
CFLAGS = -O2 -Wall -Wextra -Wno-unused-function -Isrc -Ibuild
SRC    = src/main.c src/runtime.c

calc: src/calc.y src/calc.l src/calc.h $(SRC)
	bison -Wall -v -d -o build/calc.tab.c src/calc.y
	flex -o build/lex.yy.c src/calc.l
	$(CC) $(CFLAGS) -o calc $(SRC) build/calc.tab.c build/lex.yy.c -lm

clean:
	rm -f calc build/calc.tab.* build/lex.yy.c build/calc.output
