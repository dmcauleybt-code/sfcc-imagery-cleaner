import streamlit as st
import xml.etree.ElementTree as ET
from io import BytesIO

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
        options=image_paths
    )

    # Bulk delete options
    st.subheader("Bulk Delete Options")
    suffixes = sorted({p.split("_")[-1].split(".")[0] for p in image_paths})
    bulk_delete = st.multiselect(
        "Delete all images ending with these suffixes (e.g., _02, _03, _99):",
        options=suffixes
    )

    # Process deletion
    if st.button("Generate Cleaned XML"):
        to_delete = set(selected_images)

        # Add bulk deletions
        for suf in bulk_delete:
            for p in image_paths:
                if p.endswith(f"{suf}.jpg") or f"{suf}." in p:
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
            # Convert XML to downloadable bytes
            xml_bytes = BytesIO()
            tree.write(xml_bytes, encoding="utf-8", xml_declaration=True)
            xml_bytes.seek(0)

            st.download_button(
                label="Download Cleaned XML",
                data=xml_bytes,
                file_name=f"{output_name}.xml",
                mime="application/xml"
            )

            st.success("Your cleaned XML is ready to download.")
