from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io, zipfile

app = FastAPI()

# Включаем CORS для всех (для MVP; можно потом ограничить до домена фронта)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    buf = io.BytesIO()
    img.save(buf, format='ICO', sizes=[(s, s) for s in [16, 32, 48, 64, 128, 256]])
    return buf.getvalue()

@app.post("/favicon")
async def create_favicon(file: UploadFile = File(...)):
    contents = await file.read()
    img = Image.open(io.BytesIO(contents)).convert("RGBA")

    # генерим все размеры PNG + ICO
    files = resize_and_save(img)
    files["favicon.ico"] = generate_favicon_ico(img)

    # кладём в ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for fname, data in files.items():
            zip_file.writestr(fname, data)
    zip_buffer.seek(0)
    return StreamingResponse(zip_buffer, media_type="application/zip", headers={
        "Content-Disposition": "attachment; filename=favicon.zip"
    })
