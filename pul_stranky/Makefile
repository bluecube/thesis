TEXINPUTS = .:/$(HOME)/development/tex/style_test:
export TEXINPUTS

TEXFILES = $(shell find . -name "*.tex" -type f)

RMEVERYTHING = rm -f *.1 *.log *.aux *.out *.pdf *.toc mperr.tex mptextmp.mp *.mpx *.mpo *-temp.* *-temp-* *.dependencies

.PHONY: all
all: $(TEXFILES:.tex=.pdf)

%.pdf: %.tex
	cd $(<D); pdflatex $(<F)
	cd $(<D); pdflatex $(<F)

%.dependencies: %.tex
	echo -n "$*.pdf: " > $@
	./dependencies.pl $^ | sed -r 's/^|\s+/ $(<D)\//g' >> $@

%.1: %.mp
	cd $(<D); mpost -tex=latex $(<F)
	-rm $(<D)/mpxerr.tex

clean:
	-$(RMEVERYTHING)
	-cd img ; $(RMEVERYTHING)

include $(TEXFILES:.tex=.dependencies)
