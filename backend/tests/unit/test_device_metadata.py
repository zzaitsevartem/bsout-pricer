import pytest
from pydantic import ValidationError

from src.modules.catalog.model.catalog import Device
from src.modules.catalog.schema.device import DeviceMetadata
from src.modules.catalog.service.device_metadata import merge_metadata

pytestmark = pytest.mark.unit


def record(**changes):
    return DeviceMetadata.model_validate(
        {
            "model_key": "samsung-a54",
            "metadata_source_url": "https://example.org/device",
            "release_year": 2023,
            "model_codes": ["SM-A546B"],
            "images": [
                {
                    "url": "https://example.org/photo.jpg",
                    "source_name": "Manufacturer",
                    "source_url": "https://example.org/device",
                }
            ],
            **changes,
        }
    )


def test_metadata_merge_is_repeatable_and_preserves_known_values():
    device = Device(
        model_key="samsung-a54",
        name="Galaxy A54",
        brand_id=1,
        release_year=2022,
        model_codes=["existing"],
        images=[],
        metadata_source_url="https://trusted.example/device",
    )
    assert merge_metadata(device, record())
    assert device.release_year == 2022
    assert device.metadata_source_url == "https://trusted.example/device"
    assert device.model_codes == ["existing", "SM-A546B"]
    assert len(device.images) == 1
    assert not merge_metadata(device, record())
    assert not merge_metadata(device, record(model_codes=[], release_year=None, images=[]))
    assert len(device.images) == 1


def test_metadata_does_not_replace_existing_photo_or_duplicate_codes():
    device = Device(
        release_year=None,
        model_codes=["sm-a546b"],
        images=[{"url": "https://trusted.example/photo.jpg"}],
        metadata_source_url=None,
    )
    merge_metadata(device, record(model_codes=[" SM-A546B ", ""]))
    assert device.model_codes == ["sm-a546b"]
    assert device.images == [{"url": "https://trusted.example/photo.jpg"}]
    assert device.release_year == 2023


def test_import_requires_image_provenance():
    with pytest.raises(ValidationError):
        record(images=[{"url": "https://example.org/part.jpg"}])
