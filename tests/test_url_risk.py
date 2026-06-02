from fraudlens.url_risk import analyze_url


def test_detects_shortened_url():
    signals = analyze_url("https://bit.ly/fakekyc")
    assert any(signal.name == "shortened_url" for signal in signals)


def test_detects_non_https_and_keyword():
    signals = analyze_url("http://bank-kyc-verify.example/login")
    names = {signal.name for signal in signals}
    assert "non_https_url" in names
    assert "suspicious_url_keyword" in names


def test_detects_ip_address_url():
    signals = analyze_url("http://192.168.0.5/login")
    assert any(signal.name == "ip_address_url" for signal in signals)

