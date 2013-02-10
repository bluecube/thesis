FILENAME = thesis

GOALS = $(FILENAME).pdf
GOALS += $(FILENAME)-print.pdf

MPFILES = $(wildcard img/*.mp)
EPSFILES = $(wildcard img/*.eps)

TEXFILES = $(wildcard tex/*.tex)
IMAGEFILES = $(MPFILES:.mp=.pdf) $(EPSFILES:.eps=.pdf) \
	$(wildcard tex/*.jpg) $(wildcard tex/*.png)

.PHONY: view
.PHONY: all
.PHONY: clean

RMEVERYTHING = rm -f *.1 *.log *.aux *.out *.pdf *.toc *.bbl *.blg *-blx.bib *.run.xml mperr.tex mptextmp.mp *.mpx *.mpo *-temp.* *-temp-* *.dependencies *.pdf_tex *.spl
BUILD_DIR = build

GOALS_WITH_PATH = $(addprefix $(BUILD_DIR)/,$(GOALS))
MAKE_DIR = @mkdir -p $(@D)

all: $(GOALS_WITH_PATH)

$(BUILD_DIR)/%.pdf: %.tex
	$(MAKE_DIR)
	cd $(@D); TEXINPUTS="..:$$TEXINPUTS" pdflatex -file-line-error $(abspath $<)
	cd $(@D); BIBINPUTS="..:$$BIBINPUTS" bibtex8 $(@F:.pdf=.aux)
	cd $(@D); TEXINPUTS="..:$$TEXINPUTS" pdflatex -file-line-error $(abspath $<)

$(BUILD_DIR)/%.html: %.tex hevea/*
	$(MAKE_DIR)
	hevea -v -I . -I hevea/ -o $@ extra.hva $<
	cd $(@D); BIBINPUTS="..:$$BIBINPUTS" bibhva $(@F:.html=.haux)
	hevea -v -I . -I hevea/ -o $@ extra.hva $<

$(BUILD_DIR)/%.pdf.dependencies: %.tex dependencies.py
	$(MAKE_DIR)
	echo -n "$(@:.dependencies=) $@: " > $@
	./dependencies.py --build-dir=$(BUILD_DIR) $< >> $@

$(BUILD_DIR)/%.pdf: %.eps
	$(MAKE_DIR)
	ps2pdf -dEPSCrop $^ $@

$(BUILD_DIR)/%.pdf: %.sh
	$(MAKE_DIR)
	set -e ; set -o pipefail ; $^ $@ | tee $(@:.pdf=.out)

$(BUILD_DIR)/%.pdf_tex $(BUILD_DIR)/%.pdf: %.svg
	$(MAKE_DIR)
	inkscape -f$^ --export-pdf=$(basename $@).pdf --export-latex --export-use-hints

.PHONY: clean
clean:
	rm -r $(BUILD_DIR)/*

include $(addsuffix .dependencies,$(GOALS_WITH_PATH))
