from uuid import UUID
from django.apps import apps
import base64
from django.core.files.storage import default_storage
from celery import shared_task
import cloudinary.uploader
from loguru import logger


# create a decorator whose main purpose is to turn python files into celery tasks
@shared_task(name="upload_photos_to_cloudinary")
def upload_photos_to_cloudinary(profile_id: UUID, photos: dict) -> None:
    try:
        profile_model = apps.get_model("user_profile", "Profile")
        profile = profile_model.objects.get(id=profile_id)
        for field_name, photo_data in photos.items():
            if photo_data["type"] == "base64":
                image_content = base64.b64decode(photo_data["data"])
                response = cloudinary.uploader.upload(image_content)

            else:  # if the photo is of type file, thus we read the provided path and upload to cloudinary
                with open(photo_data["data"], "rb") as image_file:  # this open the file in binary read mode
                    response = cloudinary.uploader.upload(image_file)
                    default_storage.delete(photo_data["data"])  # delete the original file from the django default storage

            setattr(profile, field_name, response["public_id"])
            setattr(profile, f"{field_name}_url", response["url"])
        profile.save()
        logger.info(
            f"Photo for {profile.user.email}'s uploaded to cloudinary and profile updated successfully"
        )

    except Exception as e:
        logger.exception(
            f"Photo for {profile.user.email}'s could not be uploaded to cloudinary and profile didn't update successfully {str(e)}"
        )

        # cleanup by deleting any left over photo that was left behind during when the error occured
        for photo_data in photos.values():
            if photo_data["type"] == "file" and default_storage.exists(
                photo_data["data"]
            ):
                default_storage.delete(photo_data["data"])
