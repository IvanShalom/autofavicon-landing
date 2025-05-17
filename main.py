from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from PIL import Image
import io, zipfile

app = FastAPI()

sizes = [16, 32, 48, 64, 128, 180, 192, 256, 512]

def resize_and_save(img: Image.Image) -> dict:
    buffer_dict = {}
    for size in sizes:
        resized = img.resize((size, size), Image.LANCZOS)
        buf = io.BytesIO()
        resized.save(buf, format="PNG")
        buffer_dict[f"icon_{size}x{size}.png"] = buf.getvalue()
    return buffer_dict

def generate_favicon_ico(img: Image.Image) -> bytes:
    # Pillow может делать ICO из сразу нескольких размеров!
    buf = io.BytesIO()
    sizes_ico = [(16,16), (32,32), (48,48)]
    img.save(buf, format="ICO", sizes=sizes_ico)
    return buf.getvalue()

@app.post("/favicon")
async def create_favicon(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read())).convert("RGBA")
    files = resize_and_save(image)
    files["favicon.ico"] = generate_favicon_ico(image)

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)

    zip_buf.seek(0)
    return StreamingResponse(zip_buf, media_type="application/zip",
                             headers={"Content-Disposition": "attachment; filename=favicon.zip"})
