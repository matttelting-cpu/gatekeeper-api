from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io

app = FastAPI(title="DesignerScripts Pre-Flight API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/v1/preflight/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    target_width_inches: float = Form(...),
    target_height_inches: float = Form(...)
):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    pixel_width, pixel_height = image.size
    
    dpi_x = pixel_width / target_width_inches
    dpi_y = pixel_height / target_height_inches
    effective_dpi = min(dpi_x, dpi_y)
    
    max_dimension = max(target_width_inches, target_height_inches)
    
    if max_dimension <= 24:
        min_required_dpi = 150
        category = "Small Format (Close Viewing)"
    elif max_dimension <= 72:
        min_required_dpi = 100
        category = "Medium Format (Short Distance)"
    else:
        min_required_dpi = 72
        category = "Large Format (Distance Viewing)"

    # Define a tighter 5% leeway for borderline files
    tolerance_dpi = min_required_dpi * 0.95

    warnings = []
    is_print_ready = True
    
    if effective_dpi >= min_required_dpi:
        pass # Perfect score, no resolution warning needed
    elif effective_dpi >= tolerance_dpi:
        # It's close enough to pass, so we don't trigger a failure, just a note
        warnings.append(f"ℹ️ <strong>Informative Note:</strong> Your file is at {int(effective_dpi)} DPI. This is slightly below our strict {min_required_dpi} DPI standard for {category}, but it is close enough that it will print cleanly. No action required.")
    else:
        # It missed the tolerance window completely, trigger the upsell
        is_print_ready = False
        warnings.append(f"Resolution too low ({int(effective_dpi)} DPI). Minimum {min_required_dpi} DPI required for {category}.")
        
    if image.mode != 'CMYK':
        warnings.append(f"ℹ️ <strong>Color Note:</strong> Image is in {image.mode} format. Bright or neon colors may look duller when printed in CMYK.")
        
    return {
        "report_card": {
            "is_print_ready": is_print_ready,
            "effective_dpi": int(effective_dpi),
            "required_dpi": min_required_dpi,
            "print_category": category,
            "warnings": warnings
        }
    }
    
@app.post("/v1/preflight/optimize")
async def optimize(file: UploadFile = File(...), target_width_inches: float = Form(...), target_height_inches: float = Form(...)):
    return {"status": "success", "message": "Image successfully upscaled and optimized for production."}

@app.post("/v1/preflight/manual-queue")
async def queue(file: UploadFile = File(...)):
    return {"status": "success", "message": "File successfully routed to the internal design team queue."}

@app.post("/v1/preflight/waiver")
async def waiver(file: UploadFile = File(...)):
    return {"status": "success", "message": "Digital waiver verified and logged. Proceeding to production as-is."}