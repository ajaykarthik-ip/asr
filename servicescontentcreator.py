import os
from slugify import slugify

SERVICES = [
    {"name": "Growth Strategy", "id": "growth-strategy"},
    {"name": "Performance Tracking with Benchmarks TM", "id": "performance-tracking"},
    {"name": "Transaction Advisory", "id": "transaction-advisory"},
    {"name": "Operations and Cost Excellence", "id": "operations-cost"},
    {
        "name": "Digital Channel Growth and Monetisation Strategy",
        "id": "digital-monetisation",
    },
    {"name": "Consumer Value Unlock", "id": "consumer-value"},
    {"name": "Inorganic Growth Support", "id": "inorganic-growth"},
    {"name": "New Market Entry", "id": "new-market"},
    {"name": "Product and Content Strategy", "id": "product-content"},
    {"name": "Growth in Existing Markets", "id": "growth-existing"},
    {
        "name": "Operational Excellence and Profitability",
        "id": "operational-excellence",
    },
    {
        "name": "Growth Acceleration and Business Model Validations",
        "id": "growth-acceleration",
    },
]

SERVICES_MAPPING_BY_SECTOR = {
    "Consumer": [
        "growth-strategy",
        "new-market",
        "growth-existing",
        "operational-excellence",
        "transaction-advisory",
        "performance-tracking",
    ],
    "B2B": [
        "growth-accelaration",
        "new-market",
        "consumer-value",
        "operational-excellence",
        "inorganic-growth",
        "transaction-advisory",
        "performance-tracking",
    ],
    "Fintech": [
        "growth-strategy",
        "consumer-value",
        "operational-excellence",
        "transaction-advisory",
    ],
    "Investors": ["growth-accelaration", "transaction-advisory"],
    # TODO: Investment Themes Assessment - not in design
    ## L2 content for Consumer
    "Retail & Leisure": [
        "digital-monetisation",
        "new-market",
        "growth-existing",
        "operational-excellence",
        "transaction-advisory",
        "performance-tracking",
    ],
    "Consumer Goods": [
        "growth-strategy",
        "new-market",
        "consumer-value",
        "inorganic-growth",
        "transaction-advisory",
        "performance-tracking",
    ],
    "TMT": [
        "growth-strategy",
        "new-market",
        "consumer-value",
        "product-content",
        "transaction-advisory",
        "performance-tracking",
    ],
    # L2 content for Fintech
    "BFSI": [
        "growth-strategy",
        "consumer-value",
        "operational-excellence",
        "transaction-advisory",
    ],
    # L2 content for B2B
    "SaaS and Enterprise Tech": [
        "new-market",
        "consumer-value",
        "transaction-advisory",
    ],
    "Manufacturing and Supply Chain": [
        "growth-strategy",
        "new-market",
        "consumer-value",
        "operational-excellence",
        "transaction-advisory",
        "performance-tracking",
    ],
    "Automotive and Mobility": [
        "growth-acceleration",
        "new-market",
        "operational-excellence",
        "inorganic-growth",
        "transaction-advisory",
        "performance-tracking",
    ],
}


class ServicesContentCreator:
    def __init__(self, wp_command_runner, image_creator):
        self.services = SERVICES
        self.wp_runner = wp_command_runner
        self.image_creator = image_creator
        self.create_content_directories()
        self.create_and_load_services_content()

    def create_content_directories(self):
        base_path = "redseer-sector-data/services"
        for service in self.services:
            service_name = service["name"]
            directory_path = f"{base_path}/{service_name}"
            # Check if the directory already exists
            if os.path.exists(directory_path):
                print(f"Directory already exists: {directory_path}")
            else:
                try:
                    os.makedirs(directory_path, exist_ok=True)
                    print(f"Created directory: {directory_path}")
                except Exception as e:
                    print(f"Error creating directory {directory_path}: {e}")
            # Create content placeholder file if it doesn't exist
            content_file_path = f"{directory_path}/description.txt"
            if not os.path.exists(content_file_path):
                try:
                    with open(content_file_path, "w") as content_file:
                        content_file.write(f"Content for {service_name} service.")
                    print(f"Created content file: {content_file_path}")
                except Exception as e:
                    print(f"Error creating content file {content_file_path}: {e}")

    def create_and_load_services_content(self):
        for service in self.services:
            service_name = service["name"]
            service_id = service["id"]
            # Read service content from the description file
            description_file_path = (
                f"redseer-sector-data/services/{service_name}/description.txt"
            )
            if os.path.exists(description_file_path):
                with open(description_file_path, "r") as file:
                    service["content"] = file.read().strip()
                    print(f"Loaded content for {service_name}.")
            else:
                print(
                    f"No description.txt found for {service_name}. Creating new content."
                )
                # Create a placeholder content if it doesn't exist
                service["content"] = f"Placeholder content for {service_name}."
            # Check if we have the image ID and URL for the service stored in the service dictionary
            # Load these to the dictionary if they exist
            id_url_file = f"redseer-sector-data/services/{service_name}/id_url.txt"
            if os.path.exists(id_url_file):
                with open(id_url_file, "r") as file:
                    lines = file.readlines()
                    if len(lines) >= 2:
                        service["image_id"] = lines[0].strip()
                        service["image_url"] = lines[1].strip()
                        print(f"Loaded image ID and URL for {service_name}.")
                        continue
                    else:
                        print(f"Invalid id_url.txt format for {service_name}.")
            print(f"No id_url.txt found for {service_name}. Creating new image.")
            # Check if the image for the service exists locally
            image_file_paths = [
                f"redseer-sector-data/services/{service_name}/image.jpg",
                f"redseer-sector-data/services/{service_name}/image.png",
            ]
            image_file_path = None
            for path in image_file_paths:
                if os.path.exists(path):
                    image_file_path = path
                    break
            if not image_file_path:
                print(f"Image file for {service_name} does not exist locally.")
                continue
            # Check if the image file exists on WordPress
            optimized_image_name = f"service-widget-{slugify(service_id)}-optimized.jpg"
            image_id, image_url = self.image_creator.check_and_create_image(
                image_file_path, optimized_image_name, width=400
            )
            if image_id is None or image_url is None:
                print(f"Failed to create or find image for {service_name}.")
                continue
            # Store the image ID and URL in the service dictionary
            with open(id_url_file, "w") as file:
                file.write(f"{image_id}\n{image_url}\n")
            service["image_id"] = image_id
            service["image_url"] = image_url
            print(
                f"Image for {service_name} created with ID {image_id} and URL {image_url}."
            )

    def create_services_content(self, sector):
        # Check the level of the sector
        # For L3, check if sector["category"] exists. If not,
        # check if sector["subsector"] exists. Default to sector["sector"] if neither exists.
        # For L2, use sector["subsector"] if it exists, otherwise use sector["sector"].
        # For L1, use sector["sector"] directly.
        if sector["level"] == "L3":
            services = SERVICES_MAPPING_BY_SECTOR.get(
                sector["category"],
                SERVICES_MAPPING_BY_SECTOR.get(
                    sector["subsector"],
                    SERVICES_MAPPING_BY_SECTOR.get(sector["sector"], []),
                ),
            )
        elif sector["level"] == "L2":
            services = SERVICES_MAPPING_BY_SECTOR.get(
                sector["subsector"],
                SERVICES_MAPPING_BY_SECTOR.get(sector["sector"], []),
            )
        elif sector["level"] == "L1":
            services = SERVICES_MAPPING_BY_SECTOR.get(sector["sector"], [])
        services_content = []
        for service in services:
            service_data = next((s for s in self.services if s["id"] == service), None)
            if service_data:
                # Sample content structure
                # {
                #     "name": "Performance Tracking with benchmarks TM",
                #     "_id": "96c7648",
                #     "description": "Our proprietary Benchmarks portal \nhelps with detailed insights and strategic foresight for measuring top-to-bottom\nline performance,  diagnostics around major gaps, and enabling the right \ndecision-making.",
                #     "image": {
                #         "url": "https://staging.redseer.com/wp-content/uploads/2025/06/Rectangle-3.png",
                #         "id": 88119,
                #         "alt": "",
                #         "source": "library",
                #     },
                # },
                content = {
                    "name": service_data["name"],
                    "_id": "d8124" + service_data["id"],
                    "description": service_data.get("content", ""),
                    "image": {
                        "url": f'https://staging.redseer.com/wp-content/uploads/{service_data.get("image_url", "")}',
                        "id": service_data.get("image_id", ""),
                        "alt": "",
                        "source": "library",
                    },
                    "talk_to_us_link": {
                        "url": "",
                        "is_external": "",
                        "nofollow": "",
                        "custom_attributes": "",
                    },
                    "case_study_link": {
                        "url": "",
                        "is_external": "",
                        "nofollow": "",
                        "custom_attributes": "",
                    },
                }
                services_content.append(content)
        return services_content
