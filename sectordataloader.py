import csv


class SectorData:
    def __init__(
        self, sector, slug, level, subsector=None, category=None, experts=None
    ):
        self.sector = sector
        self.slug = slug
        self.level = level
        self.subsector = subsector
        self.category = category
        if experts:
            self.experts = experts
        else:
            # Initialize experts as an empty list if not provided
            # This allows for easy appending later
            self.experts = []

    def get_data_directory(self):
        # Get the directory path for the sector data based on the level
        if self.level == "L1":
            return f"redseer-sector-data/{self.sector}"
        elif self.level == "L2":
            return f"redseer-sector-data/{self.sector}/{self.subsector}"
        elif self.level == "L3":
            return f"redseer-sector-data/{self.sector}/{self.subsector}/{self.category}"
        return None

    # Make this a property so that it can be accessed as sector_data.name
    @property
    def name(self):
        """Get the name of the sector, subsector, or category based on the level."""
        if self.level == "L1":
            return self.sector
        elif self.level == "L2":
            return self.subsector
        elif self.level == "L3":
            return self.category
        return None

    def __repr__(self):
        return f"SectorData(sector={self.sector}, slug={self.slug}, level={self.level}, subsector={self.subsector}, category={self.category})"

    # Support key based access to the properties so that old code
    # that uses sector_data["sector"] still works
    def __getitem__(self, key):
        if key == "sector":
            return self.sector
        elif key == "slug":
            return self.slug
        elif key == "level":
            return self.level
        elif key == "subsector":
            return self.subsector
        elif key == "category":
            return self.category
        else:
            raise KeyError(f"Invalid key: {key}")

    # Add a get method too
    def get(self, key, default=None):
        """Get the value of the specified key, or return default if not found."""
        try:
            retval = self[key]
            if retval is None:
                return default
            else:
                return retval
        except KeyError:
            return default


def load_sector_data(sector_file):
    # Load the sector data from a CSV file of this format:
    # sector,level,subsector,category,url
    # sector has the name of the sector (L1)
    # level is one of L1, L2, L3
    # subsector is the name of the subsector (for L2 and L3)
    # category is the name of the category (for L3)
    # url is the slug of the page to be created
    sector_data = []
    with open(sector_file, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            sector_data.append(row)
    validated_data = []
    for row in sector_data:
        level = row["level"]
        experts = [x.strip() for x in row.get("experts", "").split(",") if x.strip()]
        # Validate the levels to ensure we have
        # the correct hierarchy
        if level not in ["L1", "L2", "L3"]:
            raise ValueError(f"Invalid level {level} in row: {row}")
        page_url = row["url"]
        page_slug = page_url.split("/")[-1]  # Extract slug from URL
        if level == "L1":
            # Ensure the sector and URL exist
            sector_name = row["sector"]
            if not sector_name or not page_slug:
                raise ValueError(f"Sector or URL missing in row: {row}")
            validated_data.append(
                SectorData(
                    sector=sector_name, slug=page_slug, level=level, experts=experts
                )
            )
        elif level == "L2":
            sector_name = row["sector"]
            subsector_name = row["subsector"]
            if not sector_name or not subsector_name or not page_slug:
                raise ValueError(f"Sector, Subsector or URL missing in row: {row}")
            validated_data.append(
                SectorData(
                    sector=sector_name,
                    slug=page_slug,
                    level=level,
                    subsector=subsector_name,
                    experts=experts,
                )
            )
        elif level == "L3":
            sector_name = row["sector"]
            subsector_name = row["subsector"]
            category_name = row["category"]
            if (
                not sector_name
                or not subsector_name
                or not category_name
                or not page_slug
            ):
                raise ValueError(
                    f"Sector, Subsector, Category or URL missing in row: {row}"
                )
            validated_data.append(
                SectorData(
                    sector=sector_name,
                    subsector=subsector_name,
                    category=category_name,
                    slug=page_slug,
                    level=level,
                    experts=experts,
                )
            )
    return validated_data


if __name__ == "__main__":
    # Example usage
    sector_file = "redseer-sector-pages.csv"  # Replace with your actual file path
    try:
        sectors = load_sector_data(sector_file)
        for sector in sectors:
            link_text = sector.name
            print(
                sector["level"],
                sector["sector"],
                link_text,
                f'<li><a href="/industries/{sector["slug"]}/">{link_text}</a></li>',
            )
    except ValueError as e:
        print(f"Error loading sector data: {e}")
