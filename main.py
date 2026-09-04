from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io

# Turn off the security limit for massive large-format graphics
Image.MAX_IMAGE_PIXELS = None 

app = FastAPI(title="DesignerScripts Pre-Flight API")

# Allow the frontend widget to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/v1/preflight/analyze")
async def analyze_artwork(
    file: UploadFile = File(...),
    target_width_inches: float = Form(...),
    target_height_inches: float = Form(...)
):
    # Read the image file into memory
    image_data = await file.read()
    img = Image.open(io.BytesIO(image_data))
    
    # Calculate Effective PPI based on pixel width divided by physical width
    effective_ppi = img.width / target_width_inches
    
    # Dynamic logic: determine minimum required PPI based on the longest dimension
    max_dim = max(target_width_inches, target_height_inches)
    if max_dim <= 24:
        min_required_ppi = 150
    elif max_dim <= 72:
        min_required_ppi = 100
    else:
        min_required_ppi = 72
        
    # Apply the 5% tolerance margin
    tolerance_ppi = min_required_ppi * 0.95
    
    is_print_ready = True
    warnings = []
    
    # Check the resolution against the thresholds
    if effective_ppi >= min_required_ppi:
        pass 
    elif effective_ppi >= tolerance_ppi:
        warnings.append(f"Informative Note: Your file is at {int(effective_ppi)} PPI. This is slightly below our strict {min_required_ppi} PPI standard, but within acceptable printing margins.")
    else:
        is_print_ready = False
        warnings.append(f"Resolution too low ({int(effective_ppi)} PPI). Minimum {min_required_ppi} PPI required for this print size.")
        
    # Check color space
    if img.mode not in ['CMYK', 'L']:
        warnings.append("Color Space Warning: File is not CMYK. Bright or neon colors may print duller than they appear on screen.")
        
    return {
        "report_card": {
            "is_print_ready": is_print_ready,
            "effective_ppi": int(effective_ppi),
            "warnings": warnings
        }
    }

# Mock endpoints for the upsell actions
@app.post("/v1/preflight/optimize")
async def optimize(file: UploadFile = File(...)):
    return {"status": "success", "message": "Image successfully upscaled and optimized for print."}

@app.post("/v1/preflight/manual-queue")
async def queue(file: UploadFile = File(...)):
    return {"status": "success", "message": "Artwork routed to the prepress design team."}

@app.post("/v1/preflight/waiver")
async def waiver(file: UploadFile = File(...)):
    return {"status": "success", "message": "Digital waiver recorded. Proceeding with print as-is."}