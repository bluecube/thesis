FILENAME = thesis

GOALS = $(FILENAME).pdf
GOALS += $(FILENAME)-print.pdf

BUILD_DIR = build
IMPL_DIR = $(realpath ../impl)
export IMPL_DIR

GOALS_WITH_PATH = $(addprefix $(BUILD_DIR)/,$(GOALS))

DO_MAKE_DIR = @mkdir -p $(@D)

.PHONY: default
default: pdf
	@echo
	@echo 'Only built target pdf. use `make all` to rebuild everything.'

.PHONY: all
all: $(GOALS_WITH_PATH)

.PHONY: pdf
pdf: $(BUILD_DIR)/$(FILENAME).pdf

.PHONY: print-pdf
print-pdf: $(BUILD_DIR)/$(FILENAME)-print.pdf

$(BUILD_DIR)/%.pdf: %.tex
	$(DO_MAKE_DIR)
	cd $(@D); TEXINPUTS="..:$$TEXINPUTS" pdflatex -file-line-error $(abspath $<)
	cd $(@D); BIBINPUTS="..:$$BIBINPUTS" bibtex8 $(@F:.pdf=.aux)
	cd $(@D); TEXINPUTS="..:$$TEXINPUTS" pdflatex -file-line-error $(abspath $<)

$(BUILD_DIR)/%.html: %.tex hevea/*
	$(MAKE_DIR)
	hevea -v -I . -I hevea/ -o $@ extra.hva $<
	cd $(@D); BIBINPUTS="..:$$BIBINPUTS" bibhva $(@F:.html=.haux)
	hevea -v -I . -I hevea/ -o $@ extra.hva $<

$(BUILD_DIR)/%.pdf.dependencies: %.tex dependencies.py
	$(DO_MAKE_DIR)
	echo -n "$(@:.dependencies=) $@: " > $@
	./dependencies.py --build-dir=$(BUILD_DIR) $< >> $@

$(BUILD_DIR)/%.pdf: %.eps
	$(DO_MAKE_DIR)
	ps2pdf -dEPSCrop $^ $@

$(BUILD_DIR)/%.pdf $(BUILD_DIR)/%.out: %.sh
	$(DO_MAKE_DIR)
	set -e ; set -o pipefail ; $^ $(basename $@).pdf | tee $(basename $@).out

$(BUILD_DIR)/%.pdf_tex $(BUILD_DIR)/%.pdf: %.svg
	$(DO_MAKE_DIR)
	inkscape -f$^ --export-pdf=$(basename $@).pdf --export-latex --export-use-hints

.PHONY: clean
clean:
	rm -r $(BUILD_DIR)/*

include $(addsuffix .dependencies,$(GOALS_WITH_PATH))
