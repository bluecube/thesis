FILENAME=thesis

MPFILES = $(wildcard img/*.mp)
EPSFILES = $(wildcard img/*.eps)

TEXFILES = $(wildcard tex/*.tex)
IMAGEFILES = $(MPFILES:.mp=.pdf) $(EPSFILES:.eps=.pdf) \
	$(wildcard tex/*.jpg) $(wildcard tex/*.png)

.PHONY: view
.PHONY: all
.PHONY: clean

RMEVERYTHING = rm -f *.1 *.log *.aux *.out *.pdf *.toc mperr.tex mptextmp.mp *.mpx *.mpo *-temp.* *-temp-* *.dependencies

all: $(FILENAME).pdf

view: all
	evince $(FILENAME).pdf &

%.pdf: %.tex
	cd $(<D); pdflatex $(<F)
	cd $(<D); pdflatex $(<F)

%.dependencies: %.tex
	echo -n "$*.pdf: " > $@
	./dependencies.pl $^ >> $@

%.pdf: %.eps
	ps2pdf -dEPSCrop $^ $@

.INTERMEDIATE: %.1

%.1: %.mp
	cd $(<D); mpost -tex=latex $(<F)

clean:
	$(RMEVERYTHING)
	cd img ; $(RMEVERYTHING)

include $(FILENAME).dependencies
