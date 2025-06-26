import json
from jsonpath_ng.ext import parse


class JSONUpdator:
    def __init__(self, json_data):
        self.json_data = json_data

    def update_json(self, selector, new_value, allow_multiple_matches=False):
        """
        The selector is a JSONPath string that specifies the path to the value to be updated.
        The new_value is the value to set at that path.
        """
        jsonpath_expr = parse(selector)
        matches = jsonpath_expr.find(self.json_data)

        if not matches:
            raise ValueError(f"No matches found for selector: {selector}")

        if len(matches) > 1 and not allow_multiple_matches:
            raise ValueError(
                f"Multiple matches found for selector: {selector}. Set allow_multiple_matches=True to update all."
            )
        for match in matches:
            print(f"Updating match: {match.full_path}")
            match.full_path.update(self.json_data, new_value)
        return self.json_data


if __name__ == "__main__":
    # L1 test file
    # test_file = "./redseer-sector-data/Consumer/elementor_data.json"
    # L2 test file
    test_file = "./redseer-sector-data/B2B/Automotive and Mobility/elementor_data.json"
    selectors_to_check = [
        ["$[0].elements[0].elements[0].settings.editor", "New Value"],
    ]
    with open(test_file, "r") as file:
        sample_json = file.read()
        sample_json = json.loads(sample_json)
    updator = JSONUpdator(sample_json)
    for selector, new_value in selectors_to_check:
        print(f"Updating selector: {selector} with value: {new_value}")
        updator.update_json(selector, new_value)
    import pprint

    pprint.pprint(sample_json)
