import streamlit as st
import xml.etree.ElementTree as ET
from io import BytesIO
import re

st.title("SFCC Imagery XML Cleaner")

uploaded_file = st.file_uploader("Upload XML File", type=["xml"])

if uploaded_file:
    # Parse XML
    tree = ET.parse(uploaded_file)
    root = tree.getroot()

    NS = "http://www.demandware.com/xml/impex/catalog/2006-10-31"
    namespace = {"ns": NS}

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

    # Bulk delete by index (_01, _02, _03)
    st.subheader("Bulk Delete by Image Index (e.g. _01, _02, _03)")

    indices = set()
    for p in image_paths:
        filename = p.split("/")[-1].split("?")[0]
        match = re.search(r"_(\d+)\.jpg$", filename)
        if match:
            indices.add(f"_{match.group(1)}")

    bulk_indices = st.multiselect(
        "Delete all images with these indices:",
        options=sorted(indices)
    )

    # Output filename
    output_name = st.text_input("Output filename (without extension):", "Imagery_Result")

    if st.button("Generate Cleaned XML"):
        # Build deletion list
        to_delete = set(selected_images)

        for p in image_paths:
            filename = p.split("/")[-1].split("?")[0]
            for idx in bulk_indices:
                if filename.endswith(f"{idx}.jpg"):
                    to_delete.add(p)

        # -------------------------------
        # BUILD CLEAN OUTPUT XML
        # -------------------------------
        ET.register_namespace('', NS)
        new_catalog = ET.Element(f"{{{NS}}}catalog", {"catalog-id": "bta-master-catalog"})

        for product in root.findall("ns:product", namespace):
            new_product = ET.SubElement(new_catalog, f"{{{NS}}}product", {
                "product-id": product.attrib["product-id"]
            })

            images_node = ET.SubElement(new_product, f"{{{NS}}}images")

            for img_group in product.findall("ns:images/ns:image-group", namespace):
                new_group = ET.SubElement(images_node, f"{{{NS}}}image-group", {
                    "view-type": img_group.attrib["view-type"]
                })

                for img in img_group.findall("ns:image", namespace):
                    if img.attrib.get("path") not in to_delete:
                        ET.SubElement(new_group, f"{{{NS}}}image", {
                            "path": img.attrib["path"]
                        })

        # -------------------------------
        # WRITE CLEAN XML (NO .xsl / .bin ISSUES)
        # -------------------------------
        xml_bytes = BytesIO()
        ET.ElementTree(new_catalog).write(xml_bytes, encoding="utf-8", xml_declaration=True)
        xml_bytes.seek(0)

        st.download_button(
            label="Download Cleaned XML",
            data=xml_bytes.getvalue(),
            file_name=f"{output_name}.xml",
            mime="application/xml"
        )

        st.success("Your cleaned XML is ready to download.")
