import pytest

from fraudlens.privacy import mask_entity, normalize_entity_value, stable_entity_id


def test_phone_entity_ids_are_stable_across_normalized_phone_formats():
    first = stable_entity_id("phone", "+91 98765-43210", "secret-one")
    second = stable_entity_id("phone", "9876543210", "secret-one")

    assert first == second
    assert first.startswith("phone_")
    assert "9876543210" not in first


def test_entity_ids_are_namespaced_and_secret_bound():
    phone_id = stable_entity_id("phone", "9876543210", "secret-one")
    email_id = stable_entity_id("email", "9876543210", "secret-one")

    assert phone_id != email_id
    assert phone_id != stable_entity_id("phone", "9876543210", "secret-two")


def test_domain_and_case_normalization_is_stable():
    assert normalize_entity_value("email", " Alice@Example.COM ") == "alice@example.com"
    assert normalize_entity_value("upi_id", "Payee.Name@OKAXIS") == "payee.name@okaxis"
    assert normalize_entity_value("url", "HTTPS://Example.COM/Path?A=1") == "https://example.com/Path?A=1"
    assert stable_entity_id("url", "HTTPS://Example.COM/Path?A=1", "secret") == stable_entity_id(
        "url", "https://example.com/Path?A=1", "secret"
    )


def test_ipv6_url_normalization_preserves_brackets_and_port():
    assert normalize_entity_value(
        "url", "HTTPS://[2001:DB8::1]:8443/reset#private-fragment"
    ) == "https://[2001:db8::1]:8443/reset"


def test_ipv6_url_mask_returns_the_full_hostname():
    assert mask_entity("url", "https://[2001:db8::1]/reset") == "2001:db8::1"


@pytest.mark.parametrize(
    ("entity_type", "value", "expected"),
    [
        ("phone", "9876543210", "******3210"),
        ("upi_id", "Payee.Name@OKAXIS", "p***@okaxis"),
        ("email", "Alice@Example.COM", "a***@example.com"),
        ("url", "https://login.example.com/reset?token=abc", "login.example.com"),
    ],
)
def test_masks_are_type_specific_and_do_not_return_the_original_value(entity_type, value, expected):
    assert mask_entity(entity_type, value) == expected
    assert mask_entity(entity_type, value) != value


@pytest.mark.parametrize("entity_type, value", [("phone", ""), ("unknown", "value"), ("", "value")])
def test_empty_or_unsupported_entities_are_rejected(entity_type, value):
    with pytest.raises(ValueError):
        stable_entity_id(entity_type, value, "secret")


@pytest.mark.parametrize("value", ["1234", "12345678901", "1234567890"])
def test_phone_entity_id_rejects_invalid_indian_subscriber_numbers(value):
    with pytest.raises(ValueError, match="valid Indian subscriber number"):
        stable_entity_id("phone", value, "secret")


@pytest.mark.parametrize("value", ["1234", "12345678901", "1234567890"])
def test_phone_mask_rejects_values_that_could_be_returned_raw_or_are_invalid(value):
    with pytest.raises(ValueError, match="valid Indian subscriber number"):
        mask_entity("phone", value)
