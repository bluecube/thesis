FILENAME=thesis

MPFILES = $(wildcard img/*.mp)
EPSFILES = $(wildcard img/*.eps)

TEXFILES = $(wildcard tex/*.tex)
IMAGEFILES = $(MPFILES:.mp=.pdf) $(EPSFILES:.eps=.pdf) \
	$(wildcard tex/*.jpg) $(wildcard tex/*.png)

.PHONY: view
.PHONY: all
.PHONY: clean

RMEVERYTHING = rm -f *.1 *.log *.aux *.out *.pdf *.toc *.bbl *.blg *-blx.bib *.run.xml mperr.tex mptextmp.mp *.mpx *.mpo *-temp.* *-temp-* *.dependencies *.pdf_tex *.spl

all: $(FILENAME).pdf

view: all
	evince $(FILENAME).pdf &

%.pdf: %.tex
	cd $(<D); pdflatex $(<F) -file-line-error
	bibtex8 $(basename $<).aux
	cd $(<D); pdflatex $(<F) -file-line-error

%.dependencies: %.tex
	echo -n "$*.dependencies $*.pdf: " > $@
	./dependencies.pl $(FILENAME).tex >> $@

img/%.pdf: img/%.eps
	ps2pdf -dEPSCrop $^ $@

plots/%.pdf: plots/%.sh
	set -e ; set -o pipefail ; $^ $@ | tee plots/$*.out

img/%.pdf_tex: img/%.svg
	inkscape -f$^ --export-pdf=img/$*.pdf --export-latex --export-use-hints

.INTERMEDIATE: %.1

%.1: %.mp
	cd $(<D); mpost -tex=latex $(<F)

clean:
	$(RMEVERYTHING)
	cd img ; $(RMEVERYTHING)
	cd plots ; $(RMEVERYTHING)

include $(FILENAME).dependencies
