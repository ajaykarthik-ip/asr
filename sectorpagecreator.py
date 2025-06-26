import json
import shlex
import os
import argparse
from slugify import slugify
from jsonupdator import JSONUpdator
from wpcommandrunner import WPCommandRunner
from wpimagecreator import WPImageCreator
from sectordataloader import load_sector_data
from sectortabcreator import SectorTabCreator
from servicescontentcreator import ServicesContentCreator
from expertsectioncreator import ExpertSectionCreator


class SectorManager:
    def __init__(
        self,
        wp_runner,
        sector_file="redseer-sector-pages.csv",
        wp_host="staging.redseer.com",
        levels=["L1", "L2", "L3"],
        sync_json=False,
    ):
        self.wp_host = wp_host
        self.levels = levels
        self.wp_runner = wp_runner
        self.sync_json = sync_json
        print("📀 Loading sector data from file:", sector_file)
        self.sector_data = load_sector_data(sector_file)
        print("✅ Sector data loaded successfully.")
        self.create_content_directories()
        print("📂 Content directories created successfully.")
        self.image_creator = WPImageCreator(self.wp_runner)
        self.sector_tab_creator = SectorTabCreator(
            self.sector_data, self.image_creator, wp_host
        )
        self.services_content_creator = ServicesContentCreator(
            self.wp_runner, self.image_creator
        )
        self.expert_section_creator = ExpertSectionCreator(
            self.sector_data, self.wp_runner
        )

    def create_content_directories(self):
        # Create a directory structure under data with the following hierarchy:
        # redseer-websidata/
        # ├── L1 sector name
        # │   ├── L2 sector name
        # │       ├── L3 sector name
        print("🛠️ Creating content directories...")
        for sector in self.sector_data:
            directory_path = sector.get_data_directory()
            if directory_path:
                # Check if the directory already exists locally, if not, create it
                try:
                    if os.path.exists(directory_path):
                        print(f"✅ Directory already exists: {directory_path}")
                    else:
                        os.makedirs(directory_path, exist_ok=True)
                        print(f"✅ Created directory: {directory_path}")
                except Exception as e:
                    print(f"❌ Failed to create directory {directory_path}: {e}")
                self.create_text_files(sector.level, directory_path)

    def create_text_files(self, level, directory_path):
        # Create a text file in the directory with the level name
        # and a placeholder for content
        files_to_be_created_by_level = {
            "L1": ["hero-heading.txt", "hero-byline.txt", "expert-names.txt"],
            "L2": [
                "tab-description.txt",
                "hero-heading.txt",
                "second-fold-description.txt",
                "expert-names.txt",
            ],
            "L3": [
                "tab-description.txt",
                "hero-heading.txt",
                "second-fold-description.txt",
                "expert-names.txt",
            ],
        }
        files_to_be_created = files_to_be_created_by_level[level]
        for file in files_to_be_created:
            file_path = os.path.join(directory_path, file)
            if not os.path.exists(file_path):
                print(
                    f"❌ File {file_path} does not exist. In process only mode, skipping creation."
                )
                # Uncomment the following lines to actually create the files
                # print(f"🛠️ Creating file: {file_path}")
                # try:
                #     with open(file_path, "w") as f:
                #         f.write(f"Placeholder content for {file} in {level}\n")
                #         print(f"✅ Created file: {file_path}")
                # except Exception as e:
                #     print(f"❌ Failed to create file {file_path}: {e}")
            else:
                print(f"✅ File already exists: {file_path}")

    def create_sector_pages(self):
        # Load the page templates for each level
        print("📀 Loading template pages for sector levels...")
        page_ids_by_level = {}
        for level in range(1, 4):
            page_id = self.get_page_id_by_slug(f"sector-level-{level}")
            if not page_id:
                raise ValueError(f"Template page for sector level {level} not found.")
            page_ids_by_level[f"L{level}"] = page_id
        print(page_ids_by_level)
        print("✅ Template pages loaded successfully.")
        print("📀 Loading parent page ID for industries...")
        parent_page_id = self.get_page_id_by_slug("industries")
        print("✅ Parent page ID for industries:", parent_page_id)
        print("🛠️ Creating/updating sector pages...")
        for sector in self.sector_data:
            if sector.level not in self.levels:
                continue
            slug = sector["slug"]
            post_id = ""
            template_page_id = page_ids_by_level[sector.level]
            # Check if the page already exists
            existing_page_id = self.get_page_id_by_slug(slug)
            if existing_page_id:
                print(
                    f"📄 Page with slug '{slug}' already exists with ID {existing_page_id}."
                )
                post_id = existing_page_id
            else:
                print(f"🛠️ Creating page for {sector.level} with slug '{slug}'")
                post_title = sector.name
                post_id = self.wp_runner.run_wp_cli(
                    f"wp post create --porcelain --post_type=page --post_title='{post_title}' "
                    f"--post_name='{slug}' --post_parent={parent_page_id} --from-post={template_page_id}"
                )
                if post_id:
                    print(f"✨ Created page with ID {post_id} for slug '{slug}'")
                else:
                    print(f"❌ Failed to create page for slug '{slug}'")
            if post_id:
                # Update the page with the content from the text files
                directory_path = sector.get_data_directory()
                self.update_page_content(
                    template_page_id, post_id, directory_path, sector
                )
        # Flush the Elementor CSS cache to ensure the new pages are styled correctly
        print("🧹 Flushing Elementor CSS cache...")
        self.wp_runner.run_wp_cli("wp elementor flush_css")
        self.wp_runner.run_wp_cli("wp w3-total-cache flush all")

    def update_page_content(self, template_page_id, post_id, directory_path, sector):
        print(f"🔄 Updating content for post ID {post_id} in {directory_path}")
        if sector.level == "L1":
            subsector_list = self.sector_tab_creator.create_tab_content(
                sector, directory_path
            )
            services_list = self.services_content_creator.create_services_content(
                sector
            )
            updates = [
                {
                    "path": "[0].elements.[0].elements.[0].settings.editor",
                    "value": f"<p>{sector.name.upper()}</p>",
                },
                {
                    "path": "[0].elements.[0].elements.[1].settings.editor",
                    "value-file": "hero-heading.txt",
                },
                {
                    "path": "[0].elements.[0].elements.[2].settings.editor",
                    "value-file": "hero-byline.txt",
                },
                {
                    "path": "[0].settings.background_image",
                    "image-file": "hero.jpg",
                    "image-file-name": f"{slugify(sector.name)}-hero-image-optimized.jpg",
                },
                {
                    "path": "[2].elements.[0].settings.title",
                    "value": f"Our {sector.name} Consulting Services",
                },
                {
                    "path": "[4].elements.[0].settings.title",
                    "value": f"Explore {sector.name} Subsectors",
                },
                {
                    "path": "[5].elements.[0].settings.title",
                    "value": f"{sector.name} Sector Experts",
                },
                {
                    "path": "[4].elements.[1].settings.list",
                    "value": subsector_list,
                },
                {
                    "path": "[3].elements.[0].elements.[0].settings.list",
                    "value": services_list,
                },
                {
                    "path": "[5].elements.[1].settings.shortcode",
                    "value": self.expert_section_creator.get_widget_code(sector),
                },
            ]
        elif sector.level == "L2":
            subsector_list = self.sector_tab_creator.create_tab_content(
                sector, directory_path
            )
            services_list = self.services_content_creator.create_services_content(
                sector
            )
            updates = [
                {
                    "path": "$[0].elements[0].elements[0].settings.editor",
                    "value": f"<p>{sector.name.upper()}</p>",
                },
                {
                    "path": "[0].elements.[0].elements.[1].settings.editor",
                    "value-file": "hero-heading.txt",
                },
                {
                    "path": "[0].settings.background_image",
                    "image-file": "hero.jpg",
                    "image-file-name": f"{slugify(sector.name)}-hero-image-optimized.jpg",
                },
                {
                    "path": "[2].elements.[1].settings.editor",
                    "value-file": "second-fold-description.txt",
                },
                {
                    "path": "[2].elements.[0].settings.image",
                    "image-file": "second-fold-descrition.jpg",
                    "image-file-name": f"{slugify(sector.name)}-second-fold-image-optimized.jpg",
                },
                {
                    "path": "[3].elements.[0].settings.editor",
                    "value": f"Explore {sector.name} Subsectors",
                },
                {
                    "path": "[5].elements.[0].settings.title",
                    "value": f"Explore {sector.name} Subsectors",
                },
                {
                    "path": "[5].elements.[1].settings.list",
                    "value": subsector_list,
                },
                {
                    "path": "[4].elements.[0].elements.[0].settings.list",
                    "value": services_list,
                },
                {
                    "path": "[6].elements.[0].elements.[0].settings.title",
                    "value": f"{sector.name} Experts",
                },
                {
                    "path": "[6].elements.[1].settings.shortcode",
                    "value": self.expert_section_creator.get_widget_code(sector),
                },
            ]
        elif sector.level == "L3":
            services_list = self.services_content_creator.create_services_content(
                sector
            )
            updates = [
                {
                    "path": "$[0].elements[0].elements[0].settings.editor",
                    "value": f"<p>{sector.name.upper()}</p>",
                },
                {
                    "path": "[0].elements.[0].elements.[1].settings.editor",
                    "value-file": "hero-heading.txt",
                },
                {
                    "path": "[0].settings.background_image",
                    "image-file": "hero.jpg",
                    "image-file-name": f"{slugify(sector.name)}-hero-image-optimized.jpg",
                },
                {
                    "path": "[2].elements.[1].settings.editor",
                    "value-file": "second-fold-description.txt",
                },
                {
                    "path": "[2].elements.[0].settings.image",
                    "image-file": "second-fold-descrition.jpg",
                    "image-file-name": f"{slugify(sector.name)}-second-fold-image-optimized.jpg",
                },
                {
                    "path": "[5].elements.[0].elements.[0].settings.title",
                    "value": f"<p>{sector.name} Experts</p>",
                },
                {
                    "path": "[4].elements.[0].elements.[0].settings.list",
                    "value": services_list,
                },
                {
                    "path": "[5].elements.[1].settings.shortcode",
                    "value": self.expert_section_creator.get_widget_code(sector),
                },
            ]
        # Get the elementor content for the hero section
        elementor_data = self.wp_runner.run_wp_cli(
            f"wp post meta get {template_page_id} _elementor_data"
        )
        elementor_data = json.loads(elementor_data)

        if not self.sync_json:
            # If sync_json is False, we will update the page content
            # else, we just want to update the JSON files in the directory
            # Update the hero heading and byline for L1
            updator = JSONUpdator(elementor_data)
            for update in updates:
                if "value-file" in update:
                    file_path = os.path.join(directory_path, update["value-file"])
                    with open(file_path, "r") as f:
                        value = f.read().strip()
                elif "image-file" in update:
                    source_image_file = update["image-file"]
                    optimized_image_name = update["image-file-name"]
                    image_id, image_url = self.image_creator.check_and_create_image(
                        os.path.join(directory_path, source_image_file),
                        optimized_image_name,
                        width=1440,
                    )
                    if not image_id:
                        print(
                            f"❌ Failed to create or find image {optimized_image_name}"
                        )
                        continue
                    value = {
                        "url": f"https://{self.wp_host}/wp-content/uploads/{image_url}",
                        "id": image_id,
                        "size": "",
                        "alt": "",
                        "source": "library",
                    }
                else:
                    value = update["value"]
                updator.update_json(update["path"], value)
            if updates:
                self.wp_runner.run_wp_cli(
                    f"wp post meta update {post_id} _elementor_data "
                    + shlex.quote(json.dumps(elementor_data))
                )
        # Save the elementor data to a JSON file in the directory for debugging.
        with open(f"{directory_path}/elementor_data.json", "w") as f:
            json.dump(elementor_data, f, indent=4)

    def get_page_id_by_slug(self, slug):
        command = f"wp post list --post_type=page --format=json --name={slug}"
        output = self.wp_runner.run_wp_cli(command)
        if output:
            pages = json.loads(output)
            if pages:
                return pages[0]["ID"]
        return None


if __name__ == "__main__":
    argparse.ArgumentParser(description="Create and update sector pages on WordPress.")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        type=str,
        default="staging.redseer.com",
        help="WordPress host (default: staging.redseer.com)",
    )
    parser.add_argument(
        "--user",
        type=str,
        default="ubuntu",
        help="SSH user for WordPress (default: ubuntu)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=22,
        help="SSH port for WordPress (default: 22)",
    )
    # Add an argument on the levels to be created L1, L2, L3 - default is L1, L2, L3
    # This should be a list of levels supported, e.g. --level L1,L2
    parser.add_argument(
        "--level",
        type=str,
        default="L1,L2,L3",
        help="Comma-separated list of levels to create (default: L1,L2,L3)",
    )
    parser.add_argument(
        "--sync-json",
        action="store_true",
        help="Do not create the pages, just sync the JSON files (default: False)",
    )
    args = parser.parse_args()
    wp_runner = WPCommandRunner(args.host, args.user, args.port)
    sector_manager = SectorManager(
        wp_runner,
        "redseer-sector-pages.csv",
        args.host,
        levels=[x.strip().upper() for x in args.level.split(",")],
        sync_json=args.sync_json,
    )
    sector_manager.create_sector_pages()
