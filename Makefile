PDF  = de_mattia_COME02-II-26_10_2026.pdf
SRC  = $(wildcard docs/sezioni/*.md) $(wildcard docs/*.bib) metadata.yaml styles/config.yml

.PHONY: pdf open clean slides-serve
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

# Slide dell'esame (reveal.js). Server locale: notes.html legge index.html via
# fetch, che da file:// non funziona. Sul telefono: http://<ip-del-mac>:8000/notes.html
slides-serve:
	@echo "Slide su http://localhost:8000  (S = note del relatore, Ctrl+C per chiudere)"
	python3 -m http.server -d slides 8000
