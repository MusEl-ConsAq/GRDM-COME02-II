PDF  = tesina.pdf
SRC  = $(wildcard docs/sezioni/*.md) $(wildcard docs/*.bib) metadata.yaml styles/config.yml

.PHONY: pdf open clean
pdf: $(PDF)

$(PDF): $(SRC)
	@command -v pandoc-crossref >/dev/null || { echo "manca pandoc-crossref: brew install pandoc-crossref"; exit 1; }
	python3 .github/scripts/build-tesina.py
	python3 .github/scripts/tmpTeXFont.py
	pandoc --defaults styles/defaults.yml README.md -o $@
	git checkout -- README.md

open: $(PDF)
	open $(PDF)

clean:
	rm -f $(PDF) bibliography.yaml styles/config_fonts.tex
