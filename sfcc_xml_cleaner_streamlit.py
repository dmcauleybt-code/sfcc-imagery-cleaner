import streamlit as st
import xml.etree.ElementTree as ET
from io import BytesIO
import csv

st.title("SFCC Imagery XML Cleaner — CSV Mode")

st.markdown("""
Upload your `images.csv` and your XML file. The CSV should have a header row called `Images`, 
with one filename per row (e.g. `2001231835_07.jpg`).
""")

csv_file = st.file_uploader("Upload images.csv", type=["csv"])
xml_file = st.file_uploader("Upload XML File", type=["xml"])

if csv_file and xml_file:
    # --- Read filenames from CSV ---
    csv_content = csv_file.read().decode("utf-8").splitlines()
    reader = csv.DictReader(csv_content)
    filenames_to_delete = set()
    for row in reader:
        fname = row.get("Images", "").strip()
        if fname:
            filenames_to_delete.add(fname)

    st.info(f"Found **{len(filenames_to_delete)}** image(s) in CSV to delete.")
    with st.expander("View images to be deleted"):
        for f in sorted(filenames_to_delete):
            st.text(f)

    # --- Parse XML ---
    tree = ET.parse(xml_file)
    root = tree.getroot()

    NS = "http://www.demandware.com/xml/impex/catalog/2006-10-31"
    namespace = {"ns": NS}

    # Output filename
    output_name = st.text_input("Output filename (without extension):", "Imagery_Result")

    if st.button("Generate Cleaned XML"):
        def should_delete(path):
            filename = path.split("/")[-1].split("?")[0]
            return filename in filenames_to_delete

        # Build clean output XML
        ET.register_namespace('', NS)
        new_catalog = ET.Element(f"{{{NS}}}catalog", {"catalog-id": "bta-master-catalog"})

        removed_count = 0

        for product in root.findall("ns:product", namespace):
            new_product = ET.SubElement(new_catalog, f"{{{NS}}}product", {
                "product-id": product.attrib["product-id"]
            })
            images_node = ET.SubElement(new_product, f"{{{NS}}}images")

            for img_group in product.findall("ns:images/ns:image-group", namespace):
                new_group = ET.SubElement(images_node, f"{{{NS}}}image-group", dict(img_group.attrib))

                for variation in img_group.findall("ns:variation", namespace):
                    ET.SubElement(new_group, f"{{{NS}}}variation", dict(variation.attrib))

                for img in img_group.findall("ns:image", namespace):
                    path = img.attrib.get("path", "")
                    if should_delete(path):
                        removed_count += 1
                    else:
                        ET.SubElement(new_group, f"{{{NS}}}image", {"path": path})

        # Write output
        xml_bytes = BytesIO()
        ET.ElementTree(new_catalog).write(xml_bytes, encoding="utf-8", xml_declaration=True)
        xml_bytes.seek(0)

        st.download_button(
            label="Download Cleaned XML",
            data=xml_bytes.getvalue(),
            file_name=f"{output_name}.xml",
            mime="application/xml"
        )

        st.success(f"Done! Removed **{removed_count}** image reference(s) from the XML.")
