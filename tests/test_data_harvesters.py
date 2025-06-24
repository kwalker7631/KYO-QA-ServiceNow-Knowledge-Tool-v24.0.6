from data_harvesters import harvest_subject


def test_harvest_subject_simple():
    text = "Subject: Printer fails to start when power is pressed."
    assert "Printer fails to start" in harvest_subject(text)


def test_harvest_subject_no_text():
    assert harvest_subject("Short") == "No subject found."
