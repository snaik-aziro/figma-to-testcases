import json

from app.services.figma_client import FigmaClient  # <-- UPDATE THIS

# create object
obj = FigmaClient()

# load your JSON file
with open("filter_components.json") as f:
    data = json.load(f)

screens = data.get("screens", [])

for screen in screens:
    components = screen.get("components", [])

    #print("\n--- BEFORE FILTER ---")
    #print("Total components:", len(components))

    filtered = obj._filter_components_by_relevance(components)

    before_count = len(components)
    after_count = len(filtered)
    print(f"[FILTER SUMMARY] Before: {before_count} | After: {after_count} | Removed: {before_count - after_count}")


    #print("\n--- AFTER FILTER ---")
    #print("Remaining components:", len(filtered))

    print("\n--- KEPT COMPONENTS ---")
    for comp in filtered:
        print("-", comp.get("name"))