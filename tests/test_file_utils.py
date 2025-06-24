import file_utils


def test_is_pdf():

    assert file_utils.is_pdf("sample.PDF")
    assert not file_utils.is_pdf("sample.txt")


def test_is_zip():

    assert file_utils.is_zip("archive.zip")

    assert not file_utils.is_zip("archive.pdf")


def test_is_excel():
    assert file_utils.is_excel("report.xlsx")
    assert file_utils.is_excel("report.xlsm")
    assert not file_utils.is_excel("report.docx")
