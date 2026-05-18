import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from listings.views import MAX_LISTING_PHOTOS


@pytest.mark.django_db
class TestPhotoLimitEnforcement:
    def test_upload_within_limit_succeeds(self, owner_user):
        from tests.factories import ListingFactory
        listing = ListingFactory(owner=owner_user)
        client = APIClient()
        client.force_authenticate(user=owner_user)

        photo = SimpleUploadedFile('test.jpg', b'fake-image-data', content_type='image/jpeg')
        response = client.post(
            f'/api/v1/listings/{listing.id}/media/',
            {'file': photo},
            format='multipart',
        )
        assert response.status_code == 201
        assert response.data['success'] is True
        assert response.data['data']['photo_count'] == 1
        assert response.data['data']['max_photos'] == MAX_LISTING_PHOTOS

    def test_upload_at_limit_is_rejected(self, owner_user):
        from tests.factories import ListingFactory, ListingMediaFactory
        listing = ListingFactory(owner=owner_user)

        for i in range(MAX_LISTING_PHOTOS):
            ListingMediaFactory(listing=listing, display_order=i)

        assert listing.media.count() == MAX_LISTING_PHOTOS

        client = APIClient()
        client.force_authenticate(user=owner_user)

        photo = SimpleUploadedFile('extra.jpg', b'fake-image-data', content_type='image/jpeg')
        response = client.post(
            f'/api/v1/listings/{listing.id}/media/',
            {'file': photo},
            format='multipart',
        )
        assert response.status_code == 400
        assert 'Maximum 10 photos' in response.data['errors']

    def test_max_listing_photos_constant_is_10(self):
        assert MAX_LISTING_PHOTOS == 10
