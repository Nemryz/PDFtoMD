
from pdfmd.quality_metrics import measure_text_quality, quality_score


class TestMeasureTextQuality:

    def test_empty_text(self):
        report = measure_text_quality("")
        assert report.words == 0
        assert report.broken_sentences == 0
        assert report.broken_connectors == 0
        assert report.duplicate_lines == 0
        assert report.noise_patterns == 0
        assert report.headers_detected == 0
        assert report.tables_detected == 0
        assert report.lists_detected == 0

    def test_simple_paragraph(self):
        text = "Esto es un parrafo simple con varias palabras.\n"
        report = measure_text_quality(text)
        assert report.words == 8
        assert report.broken_sentences == 0

    def test_words_count(self):
        text = "uno dos tres cuatro cinco\n"
        report = measure_text_quality(text)
        assert report.words == 5

    def test_broken_sentences(self):
        # Line ends in lowercase vowel without punctuation, next line has content
        text = "Esta oracion termina en e\nY esta es la siguiente linea\n"
        report = measure_text_quality(text)
        assert report.broken_sentences >= 1

    def test_broken_sentences_no_break_at_period(self):
        text = "Termina con punto.\nSiguiente linea.\n"
        report = measure_text_quality(text)
        assert report.broken_sentences == 0

    def test_broken_sentences_no_break_at_end(self):
        # The last line has no next line, so it is not a break.
        text = "Ultima linea sin punto\n"
        report = measure_text_quality(text)
        assert report.broken_sentences == 0

    def test_broken_connectors(self):
        # Connector word alone on a line (split across lines)
        text = "El documento fue firmado\nde\nel director el dia de hoy\n"
        report = measure_text_quality(text)
        assert report.broken_connectors >= 1

    def test_broken_connectors_common_words(self):
        connectors = ["de", "la", "el", "en", "que", "por", "con", "para", "del", "un"]
        for conn in connectors:
            text = f"Linea anterior\n{conn}\nSiguiente linea\n"
            report = measure_text_quality(text)
            assert report.broken_connectors >= 1, f"Connector '{conn}' not detected"

    def test_duplicate_lines(self):
        text = "Linea repetida\nLinea repetida\nOtra linea\n"
        report = measure_text_quality(text)
        assert report.duplicate_lines == 1

    def test_no_duplicates_when_different(self):
        text = "Linea uno\nLinea dos\nLinea tres\n"
        report = measure_text_quality(text)
        assert report.duplicate_lines == 0

    def test_headers_detected(self):
        text = "# Titulo Principal\n## Subtitulo\n### Nivel 3\nTexto normal\n"
        report = measure_text_quality(text)
        assert report.headers_detected == 3

    def test_no_headers_in_normal_text(self):
        text = "No hay headers aqui\nSolo texto normal\n"
        report = measure_text_quality(text)
        assert report.headers_detected == 0

    def test_tables_detected(self):
        text = "| Col1 | Col2 |\n|------|------|\n| a    | b    |\n"
        report = measure_text_quality(text)
        assert report.tables_detected == 3

    def test_lists_detected_bullets(self):
        text = "- Item uno\n* Item dos\n• Item tres\n"
        report = measure_text_quality(text)
        assert report.lists_detected == 3

    def test_lists_detected_numbered(self):
        text = "1. Primero\n2. Segundo\n3. Tercero\n"
        report = measure_text_quality(text)
        assert report.lists_detected == 3

    def test_noise_patterns_single_char_lines(self):
        text = "Texto normal\nA\nOtra linea\n"
        report = measure_text_quality(text)
        assert report.noise_patterns >= 1

    def test_noise_patterns_garbage_chars(self):
        text = "Linea normal\n~~~\nOtra linea\n"
        report = measure_text_quality(text)
        assert report.noise_patterns >= 1

    def test_avg_line_length(self):
        text = "abc\ndefg\n"
        report = measure_text_quality(text)
        assert report.avg_line_length == 3.5  # (3 + 4) / 2

    def test_avg_line_length_skips_empty(self):
        text = "abc\n\n\ndefg\n"
        report = measure_text_quality(text)
        assert report.avg_line_length == 3.5  # (3 + 4) / 2


class TestQualityScore:

    def test_empty_report(self):
        report = measure_text_quality("")
        score = quality_score(report)
        assert score == 100.0  # No issues = perfect score

    def test_perfect_text(self):
        text = "# Titulo\n\nParrafo perfecto con puntuacion.\n\n- Item\n"
        report = measure_text_quality(text)
        score = quality_score(report)
        assert 80 <= score <= 100

    def test_broken_sentences_reduce_score(self):
        good = "Linea correcta.\nOtra linea.\n"
        bad = "Termina en vocal\nSiguiente linea\n" * 5
        score_good = quality_score(measure_text_quality(good))
        score_bad = quality_score(measure_text_quality(bad))
        assert score_bad < score_good

    def test_score_range_0_to_100(self):
        # Worst case: lots of issues
        bad_text = ("x\n" + "termina en vocal\nSiguiente\n") * 20
        report = measure_text_quality(bad_text)
        score = quality_score(report)
        assert 0 <= score <= 100

    def test_score_is_float(self):
        report = measure_text_quality("Test text.\n")
        score = quality_score(report)
        assert isinstance(score, float)


class TestQualityReport:

    def test_dataclass_fields(self):
        report = measure_text_quality("Test.\n")
        assert hasattr(report, "words")
        assert hasattr(report, "broken_sentences")
        assert hasattr(report, "broken_connectors")
        assert hasattr(report, "duplicate_lines")
        assert hasattr(report, "noise_patterns")
        assert hasattr(report, "headers_detected")
        assert hasattr(report, "tables_detected")
        assert hasattr(report, "lists_detected")
        assert hasattr(report, "avg_line_length")

    def test_to_dict(self):
        report = measure_text_quality("Test.\n")
        d = report.to_dict()
        assert isinstance(d, dict)
        assert "words" in d
        assert "broken_sentences" in d
