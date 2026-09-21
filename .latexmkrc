$pdf_mode = 1;
$bibtex_use = 2;
$out_dir = 'build';
$pdflatex = 'pdflatex -interaction=nonstopmode -halt-on-error -file-line-error %O %S';
@default_files = ('supplement.tex');
$success_cmd = 'cp build/supplement.pdf supplement.pdf';
