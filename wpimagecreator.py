from wpcommandrunner import WPCommandRunner
import os
import shlex


class WPImageCreator:
    def __init__(self, wp_command_runner: WPCommandRunner):
        self.wp_runner = wp_command_runner

    def check_and_create_image(self, image_file_path, optimized_image_name, width):
        # Check if the image file exists locally - the image file path may be
        # .png or .jpg. Check for the existance of either of them.
        jpgeg_and_png_file_paths = set(
            [
                image_file_path,
                image_file_path.replace(".jpg", ".png"),
                image_file_path.replace(".png", ".jpg"),
            ]
        )
        image_file_path = None
        for file_path in jpgeg_and_png_file_paths:
            if os.path.exists(file_path):
                image_file_path = file_path
                break
        if not image_file_path:
            print(f"❌ Image file {image_file_path} does not exist locally.")
            return None, None
        # The source image file exists. Check if the optimized image exists locally.
        # Check if the optimized image already exists in the same directory as the original image
        optimized_image_path = os.path.join(
            os.path.dirname(image_file_path), optimized_image_name
        )
        if not os.path.exists(optimized_image_path):
            # The optimized image does not exist. We need to create it. Use convert (ImageMagick)
            print("🛠️ Optimizing image for web...")
            os.system(
                f"convert {shlex.quote(image_file_path)} -resize {width}x -quality 90 {shlex.quote(optimized_image_path)}"
            )
            print(f"🛠️ Optimized image created: {optimized_image_name}")
            if not os.path.exists(optimized_image_path):
                print(
                    f"❌ Failed to create optimized image {optimized_image_name}. Please check the ImageMagick installation."
                )
                return None, None
        # Check if the image file exists in the WordPress media library
        image_id, image_url = self.get_wp_image_id_and_url(optimized_image_name)
        if not image_id:
            print(
                f"❌ Image {optimized_image_name} not found in WordPress media library."
            )
            self.upload_image(optimized_image_path, optimized_image_name)
            image_id, image_url = self.get_wp_image_id_and_url(optimized_image_name)
            if not image_id:
                print(
                    f"❌ Failed to upload image {optimized_image_name} to WordPress media library."
                )
                return None, None
        print(f"✅ Image {optimized_image_name} found with ID {image_id}.")
        return image_id, image_url

    def upload_image(self, image_file_path, image_file_name):
        # Use fabric to get the image file to the server
        print(f"🛠️ Uploading image {image_file_name} to WordPress media library...")
        remote_path = f"/tmp/{image_file_name}"
        self.wp_runner.connection.put(image_file_path, remote_path)
        print(f"🔄 Uploaded {image_file_path} to {remote_path}")
        # Now run the wp media import command to upload the image
        command = f"wp media import {remote_path} --porcelain"
        output = self.wp_runner.run_wp_cli(command)
        if output:
            print(f"✅ Image {image_file_name} uploaded successfully with ID {output}.")
        else:
            print(
                f"❌ Failed to upload image {image_file_name} to WordPress media library."
            )
        return output

    def get_wp_image_id_and_url(self, image_file_name):
        # Get the URL of an image uploaded to the WordPress media library
        command = f"""echo "select post_id, meta_value from wppj_postmeta where meta_key='_wp_attached_file' and meta_value like '%{image_file_name}';" | wp db cli"""
        output = self.wp_runner.run_wp_cli(command).strip()
        if output:
            image_id, image_url = output.split("\n")[-1].strip().split()
            return image_id, image_url
        return None, None
