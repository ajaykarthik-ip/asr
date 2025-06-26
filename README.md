# Redseer Automation Project

Redseer's new website has around 40 pages for various sectors, subsectors and categories that they consult in. Each one has a page built using one of three Elementor templates. The createsectorpages.py script aims to automate the creation and maintenance of these pages using this strategy:

- The three pages for each type were created using Elementor.
- The path, title and type of each of the 40 odd pages is defined in a CSV file.
- We use Fabric to connect to the server and clone these pages to the path specified in the CSV.
- A directory synced using Google Drive maintains data for each of these pages in hierarchical directories. Each directory contains content in text files and images named using conventions. Example: hero.txt contains the hero banner text, hero.jpg contains the hero banner image and so on.
- We pull Elementor data for the page using WP CLI and patch it with the content found in the directories and update the page.

This automation saves time since we don't have to deal with Elementor's UI to make these edits. It also allows us to update the base templates and recreate the pages at any point to apply global fixes on the pages without having to copy changes manually across 40 odd pages.
