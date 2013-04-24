FILENAME = slides

GOAL = $(FILENAME).pdf

BUILD_DIR = build
IMPL_DIR = $(realpath ../impl)
export IMPL_DIR

GOALS_WITH_PATH = $(addprefix $(BUILD_DIR)/,$(GOALS))

DO_MAKE_DIR = @mkdir -p $(@D)

.PHONY: all
all: $(BUILD_DIR)/$(GOAL)

$(BUILD_DIR)/%.pdf: %.tex
	$(DO_MAKE_DIR)
	cd $(@D); TEXINPUTS="..:$$TEXINPUTS" pdflatex -file-line-error $(abspath $<)
	cd $(@D); TEXINPUTS="..:$$TEXINPUTS" pdflatex -file-line-error $(abspath $<)

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

$(BUILD_DIR)/%.tex $(BUILD_DIR)/%.out: %.sh
	$(DO_MAKE_DIR)
	set -e ; set -o pipefail ; $^ $(basename $@).tex | tee $(basename $@).out

$(BUILD_DIR)/%.pdf_tex $(BUILD_DIR)/%.pdf: %.svg
	$(DO_MAKE_DIR)
	inkscape -f$^ --export-pdf=$(basename $@).pdf --export-latex --export-use-hints

.PHONY: clean
clean:
	rm -r $(BUILD_DIR)/*

include $(BUILD_DIR)/$(GOAL).dependencies
