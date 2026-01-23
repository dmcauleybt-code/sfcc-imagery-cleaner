import streamlit as st
import xml.etree.ElementTree as ET
from io import BytesIO
import re

st.title("SFCC Imagery XML Cleaner")

st.write("Upload an SFCC XML file and choose which images to remove.")

uploaded_file = st.file_uploader("Upload XML File", type=["xml"])

if uploaded_file:
    tree = ET.parse(uploaded_file)
    root = tree.getroot()

    namespace = {"ns": "http://www.demandware.com/xml/impex/catalog/2006-10-31"}

    # Collect all image paths
    image_paths = []
    for product in root.findall("ns:product", namespace):
        for img_group in product.findall("ns:images/ns:image-group", namespace):
            for img in img_group.findall("ns:image", namespace):
                path = img.attrib.get("path")
                if path:
                    image_paths.append(path)

    st.subheader("Select Images to Delete")

    # Individual image selection
    selected_images = st.multiselect(
        "Choose individual images to delete:",
        options=sorted(set(image_paths))
    )

    # ---- Bulk delete by filename index (_01, _02, _03, etc.) ----
    st.subheader("Bulk Delete by Image Index (e.g. _01, _02, _03)")

    # Extract indices from filenames like 2000365659_01.jpg?$pdp_zoom$
    indices = set()
    for p in image_paths:
        filename = p.split("/")[-1]          # e.g. 2000365659_01.jpg?$pdp_zoom$
        filename = filename.split("?")[0]    # e.g. 2000365659_01.jpg
        match = re.search(r"_(\d+)\.jpg$", filename)
        if match:
            indices.add(f"_{match.group(1)}")

    indices = sorted(indices)

    bulk_indices = st.multiselect(
        "Delete all images with these indices:",
        options=indices,
        help="For example, selecting _02 will delete all images whose filename ends in _02.jpg"
    )

    if st.button("Generate Cleaned XML"):
        to_delete = set(selected_images)

        # Add bulk deletions based on index (_01, _02, etc.)
        for p in image_paths:
            filename = p.split("/")[-1]          # e.g. 2000365659_01.jpg?$pdp_zoom$
            filename_no_query = filename.split("?")[0]  # e.g. 2000365659_01.jpg

            for idx in bulk_indices:
                # idx is like "_01" → we want filenames ending with "_01.jpg"
                if filename_no_query.endswith(f"{idx}.jpg"):
                    to_delete.add(p)

        # Remove images from XML
        for product in root.findall("ns:product", namespace):
            for img_group in product.findall("ns:images/ns:image-group", namespace):
                for img in list(img_group.findall("ns:image", namespace)):
                    if img.attrib.get("path") in to_delete:
                        img_group.remove(img)

        # Ask for output filename
        output_name = st.text_input("Enter output filename (without extension):", "Imagery_Result")

        if output_name:
            xml_bytes = BytesIO()
            tree.write(xml_bytes, encoding="utf-8", xml_declaration=True)
            xml_bytes.seek(0)

            st.download_button(
                label="Download Cleaned XML",
                data=xml_bytes.getvalue(),
                file_name=f"{output_name}.xml",
                mime="application/xml"
            )

            st.success("Your cleaned XML is ready to download.")
