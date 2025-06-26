import os
from slugify import slugify


QUESTIONS = [
    "Accelerate my digital growth and market share",
    "Solve for Growing Customer Base and Existing Customers\u2019 Retention"
    "Strategy"
    "Grow in new/existing cities and micro-markets",
    "Build a New Product Innovation Strategy",
    "Optimise Existing Product and Market Strategy",
    "Accelerate Key Account Management Strategy Playbook",
    "Unlock profitability at scale",
    "Evaluate new investment and M&amp;A opportunities",
    "Plan for IPO or Exit Strategy",
    "Others",
]


class SectorTabCreator:
    def __init__(self, sector_data, image_creator, wp_host):
        self.sector_data = sector_data
        self.image_creator = image_creator
        self.wp_host = wp_host

    def create_tab_content(self, sector, directory_path):
        subsector_list = []
        level = sector["level"]
        if level not in ["L1", "L2"]:
            raise ValueError(f"Invalid level {level} for sector {sector['sector']}")
        level_name_key = "sector" if level == "L1" else "subsector"
        sublevel_name_key = "subsector" if level == "L1" else "category"
        # Walk through each sub-directory of directory_path
        for subsector in os.listdir(directory_path):
            subsector_path = os.path.join(directory_path, subsector)
            if os.path.isdir(subsector_path):
                tab_description_file_path = os.path.join(
                    subsector_path, "tab-description.txt"
                )
                with open(tab_description_file_path, "r") as f:
                    tab_description = f.read().strip()
                tab_image_path = os.path.join(subsector_path, "tabimage.jpg")
                if os.path.exists(tab_image_path):
                    image_id, image_url = self.image_creator.check_and_create_image(
                        tab_image_path,
                        f"{slugify(sector[level_name_key])}-{slugify(subsector)}-tab-image-optimized.jpg",
                        width=800,
                    )
                    if not image_id:
                        print(
                            f"❌ Failed to create or find image for subsector {subsector}"
                        )
                        continue
                    tab_image = {
                        "url": f"https://{self.wp_host}/wp-content/uploads/{image_url}",
                        "id": image_id,
                        "alt": "",
                        "source": "library",
                    }
                else:
                    raise FileNotFoundError(
                        f"Tab image file not found for subsector {subsector} at {tab_image_path}"
                    )
                # Get the tab link by searching for the subsector in self.sector_data
                subsector_index = self.sector_data.index(
                    next(
                        item
                        for item in self.sector_data
                        if item.get(sublevel_name_key) == subsector
                    )
                )
                subsector_data = self.sector_data[subsector_index]
                if subsector is None:
                    raise ValueError(f"Subsector {subsector} not found in sector data.")
                subsector_url = (
                    f"https://{self.wp_host}/industries/{subsector_data['slug']}/"
                )

                subsector_list.append(
                    {
                        "name": subsector,
                        "_id": "",
                        "description": tab_description,
                        "questions": "\n".join(QUESTIONS),
                        "link": {
                            "url": subsector_url,
                            "is_external": False,
                            "nofollow": False,
                            "custom_attributes": "",
                        },
                        "image": tab_image,
                    }
                )
        return subsector_list
