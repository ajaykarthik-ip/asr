import json


class ExpertSectionCreator:
    def __init__(self, sector_data, wp_runner):
        self.sector_data = sector_data
        self.wp_runner = wp_runner
        self.expert_ids = {}
        self.load_expert_data_from_csv()
        self.load_experts_from_wp()

    def get_sector_data_directory(self, row):
        # Get the directory path for the sector data based on the level
        if row["level"] == "L1":
            return f"redseer-sector-data/{row['sector']}"
        elif row["level"] == "L2":
            return f"redseer-sector-data/{row['sector']}/{row['subsector']}"
        elif row["level"] == "L3":
            return f"redseer-sector-data/{row['sector']}/{row['subsector']}/{row['category']}"
        return None

    def load_expert_data_from_csv(self):
        # Iterate through every sector starting with L3
        # If an L3 sector has no experts, get them from the parent L2 sector
        # An L2 sector will always have experts
        # An L1 sector may not have experts. Get them as a set of all L2 experts under it
        unique_experts = set()
        # CSV data is already loaded into sector_data, so we don't need to read it again
        # We are only going to refine the data based on the rules above
        # This may require three passes through the data
        # First pass: Collect experts for L3 sectors
        l3_experts = {}
        l2_sectors = {}
        l1_sectors = {}

        for row in self.sector_data:
            if row.level == "L3":
                key = (row.sector, row.subsector, row.category)
                if row.experts:
                    l3_experts[key] = set(row.experts)
                else:
                    l3_experts[key] = set()
            elif row.level == "L2":
                key = (row.sector, row.subsector)
                if row.experts:
                    l2_sectors[key] = set(row.experts)
                else:
                    l2_sectors[key] = set()
            elif row.level == "L1":
                key = row.sector
                if row.experts:
                    l1_sectors[key] = set(row.experts)
                else:
                    l1_sectors[key] = set()

        # Second pass: Fill in missing L3 experts from parent L2
        for key in l3_experts:
            sector, subsector, category = key
            if not l3_experts[key]:  # If L3 has no experts
                parent_key = (sector, subsector)
                if parent_key in l2_sectors:
                    l3_experts[key] = l2_sectors[parent_key].copy()

        # Third pass: Ensure L1 sectors have all experts from child L2s
        for key in l1_sectors:
            sector = key
            # Find all L2 sectors under this L1
            for l2_key in l2_sectors:
                l2_sector, l2_subsector = l2_key
                if l2_sector == sector:
                    l1_sectors[sector].update(l2_sectors[l2_key])

        # Update the original sector_data objects with processed experts
        for row in self.sector_data:
            if row.level == "L3":
                key = (row.sector, row.subsector, row.category)
                if key in l3_experts:
                    row.experts = list(l3_experts[key])
            elif row.level == "L2":
                key = (row.sector, row.subsector)
                if key in l2_sectors:
                    row.experts = list(l2_sectors[key])
            elif row.level == "L1":
                key = row.sector
                if key in l1_sectors:
                    row.experts = list(l1_sectors[key])

    def display_expert_data(self):
        # Display the expert data in a structured format
        for row in self.sector_data:
            level = row.level
            sector = row.sector
            subsector = row.subsector
            category = row.category
            # experts = ", ".join(row.experts) if row.experts else "No experts"
            experts = row.experts if row.experts else "❌ No experts"
            print(
                f"Level: {level}, Sector: {sector}, Subsector: {subsector}, Category: {category}, Experts: {experts}"
            )

    def load_experts_from_wp(self):
        # Get a list of all users from WordPress
        retval = self.wp_runner.run_wp_cli(
            "wp user list --format=json --fields=ID,user_login,display_name,user_email"
        )
        if retval:
            self.wp_users = json.loads(retval)

    def get_widget_code(self, sector):
        experts = sector.experts
        for expert in experts:
            if expert not in self.expert_ids:
                self.expert_ids[expert] = self.get_expert_id(expert)
        expert_ids = [
            str(self.expert_ids[expert])
            for expert in experts
            if expert in self.expert_ids
        ]
        return '[red_experts_widget user_ids="{}"]'.format(",".join(expert_ids))

    def get_expert_id(self, expert_name):
        """
        Get the WordPress user ID for a given expert name.
        If the expert is not found, return None.
        """
        for user in self.wp_users:
            expert_name_lower = expert_name.lower()
            if (
                expert_name_lower in user["display_name"].lower()
                or expert_name_lower in user["user_login"].lower()
            ):
                return user["ID"]
        print(f"❌ Expert '{expert_name}' not found in WordPress users.")
        return None


if __name__ == "__main__":
    from sectordataloader import load_sector_data

    sectors = load_sector_data("redseer-sector-pages.csv")
    expert_creator = ExpertSectionCreator(sectors)
    expert_creator.display_expert_data(sectors)
