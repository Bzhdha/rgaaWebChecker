
from PIL import Image
import io

def simulate_daltonism(image_bytes, mode):
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img = img.convert('L').convert('RGB')  # À remplacer par un vrai filtre
    output = io.BytesIO()
    img.save(output, format='PNG')
    return output.getvalue()
