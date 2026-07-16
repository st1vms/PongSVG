import base64
import logging

def get_base64_data_url(local_path: str) -> str:
    """Converts a local image file into a Base64 Data URL for standalone SVG inline rendering."""
    try:
        with open(local_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        ext = local_path.split(".")[-1].lower()
        mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
        return f"data:{mime};base64,{encoded_string}"
    except Exception as e:
        logging.error(f"Failed to convert image to Base64: {e}")
        return ""
