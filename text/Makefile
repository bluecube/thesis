FILENAME = thesis

GOALS = $(FILENAME).pdf
GOALS += $(FILENAME)-print.pdf
GOALS += $(FILENAME).html

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
all: pdf print-pdf html ebook

.PHONY: pdf
pdf: $(BUILD_DIR)/$(FILENAME).pdf

.PHONY: print-pdf
print-pdf: $(BUILD_DIR)/$(FILENAME)-print.pdf

.PHONY: html
html: $(BUILD_DIR)/$(FILENAME).html

.PHONY: ebook
ebook: $(BUILD_DIR)/$(FILENAME).epub $(BUILD_DIR)/$(FILENAME).mobi

$(BUILD_DIR)/%.pdf: %.tex
	$(DO_MAKE_DIR)
	cd $(@D); TEXINPUTS="..:$$TEXINPUTS" pdflatex -file-line-error $(abspath $<)
	cd $(@D); BIBINPUTS="..:$$BIBINPUTS" bibtex8 $(@F:.pdf=.aux)
	cd $(@D); TEXINPUTS="..:$$TEXINPUTS" pdflatex -file-line-error $(abspath $<)

$(BUILD_DIR)/%.html: %.tex hevea/*
	$(DO_MAKE_DIR)
	hevea -v -I . -I hevea/ -o $@ $<
	cd $(@D); BIBINPUTS="..:$$BIBINPUTS" bibhva $(@F:.html=.haux)
	hevea -v -I . -I hevea/ -o $@ $<
	cd $(@D); TEXINPUTS="..:$$TEXINPUTS" imagen -pdf $(abspath $(@:%.html=%))

$(BUILD_DIR)/%.pdf.dependencies: %.tex dependencies.py
	$(DO_MAKE_DIR)
	echo -n "$(@:.dependencies=) $@: " > $@
	./dependencies.py --build-dir=$(BUILD_DIR) $< >> $@

$(BUILD_DIR)/%.html.dependencies: %.tex dependencies.py
	$(DO_MAKE_DIR)
	echo -n "$(@:.dependencies=) $@: " > $@
	./dependencies.py --build-dir=$(BUILD_DIR) $< >> $@

$(BUILD_DIR)/%.epub: $(BUILD_DIR)/%.html
	$(DO_MAKE_DIR)
	ebook-convert $< $@

$(BUILD_DIR)/%.mobi: $(BUILD_DIR)/%.html
	$(DO_MAKE_DIR)
	ebook-convert $< $@

$(BUILD_DIR)/%.pdf: %.eps
	$(DO_MAKE_DIR)
	ps2pdf -dEPSCrop $^ $@

$(BUILD_DIR)/%.pdf $(BUILD_DIR)/%.out: %.sh
	$(DO_MAKE_DIR)
	set -e ; set -o pipefail ; $^ $(basename $@).pdf | tee $(basename $@).out

$(BUILD_DIR)/%.tex $(BUILD_DIR)/%.out: %.sh
	$(DO_MAKE_DIR)
	set -e ; set -o pipefail ; $^ $(basename $@).tex | tee $(basename $@).out

$(BUILD_DIR)/%.pdf_tex $(BUILD_DIR)/%.pdf: %.svg
	$(DO_MAKE_DIR)
	inkscape -f$^ --export-pdf=$(basename $@).pdf --export-latex --export-use-hints

.PHONY: clean
clean:
	rm -r $(BUILD_DIR)/*

include $(addsuffix .dependencies,$(GOALS_WITH_PATH))
