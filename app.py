"""
MVP Generator Web App

FastAPI web application that accepts job descriptions and generates MVPs.
"""
import io
import zipfile
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from src.agents.architect.graph import run_architect_session
from src.agents.dev_team.graph import run_dev_team_v2

app = FastAPI(title="MVP Generator", version="1.0.0")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobDescriptionRequest(BaseModel):
    """Request model for MVP generation"""
    job_description: str
    project_name: Optional[str] = "Generated MVP"


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main web interface"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MVP Generator - From Job Description to Code</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }

            .container {
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                overflow: hidden;
            }

            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }

            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
            }

            .header p {
                font-size: 1.1rem;
                opacity: 0.9;
            }

            .content {
                padding: 40px;
            }

            label {
                display: block;
                font-weight: 600;
                margin-bottom: 10px;
                color: #333;
                font-size: 1.1rem;
            }

            textarea {
                width: 100%;
                min-height: 300px;
                padding: 15px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                font-family: 'Courier New', monospace;
                font-size: 0.95rem;
                resize: vertical;
                transition: border-color 0.3s;
            }

            textarea:focus {
                outline: none;
                border-color: #667eea;
            }

            input[type="text"] {
                width: 100%;
                padding: 12px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                font-size: 1rem;
                margin-bottom: 20px;
                transition: border-color 0.3s;
            }

            input[type="text"]:focus {
                outline: none;
                border-color: #667eea;
            }

            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 40px;
                font-size: 1.1rem;
                font-weight: 600;
                border-radius: 10px;
                cursor: pointer;
                width: 100%;
                margin-top: 20px;
                transition: transform 0.2s, box-shadow 0.2s;
            }

            button:hover:not(:disabled) {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
            }

            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }

            .loading {
                display: none;
                text-align: center;
                padding: 20px;
                color: #667eea;
                font-weight: 600;
            }

            .loading.active {
                display: block;
            }

            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            .error {
                background: #fee;
                border: 2px solid #fcc;
                color: #c33;
                padding: 15px;
                border-radius: 10px;
                margin-top: 20px;
                display: none;
            }

            .error.active {
                display: block;
            }

            .example {
                background: #f8f9fa;
                border-left: 4px solid #667eea;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
                font-size: 0.95rem;
            }

            .example-title {
                font-weight: 600;
                color: #667eea;
                margin-bottom: 8px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 MVP Generator</h1>
                <p>Paste a job description, get a complete MVP codebase</p>
            </div>

            <div class="content">
                <div class="example">
                    <div class="example-title">💡 How it works:</div>
                    1. Paste a job description or project requirement<br>
                    2. Our AI architect creates a Technical Design Document<br>
                    3. Development agents generate production-ready code<br>
                    4. Download your complete MVP as a ZIP file
                </div>

                <form id="mvpForm">
                    <label for="projectName">Project Name (optional)</label>
                    <input
                        type="text"
                        id="projectName"
                        name="projectName"
                        placeholder="e.g., Task Manager App"
                    >

                    <label for="jobDescription">Job Description / Project Requirements</label>
                    <textarea
                        id="jobDescription"
                        name="jobDescription"
                        placeholder="Paste the job description here...

Example:
We need a simple e-commerce platform with:
- Product listing and search
- Shopping cart functionality
- User authentication
- Payment integration
- Admin dashboard

Budget: $500-1000
Tech: React + Python/FastAPI
"
                        required
                    ></textarea>

                    <button type="submit" id="generateBtn">
                        Generate MVP
                    </button>
                </form>

                <div id="loading" class="loading">
                    <div class="spinner"></div>
                    <p>Generating your MVP... This may take 2-3 minutes</p>
                    <p style="font-size: 0.9rem; color: #666; margin-top: 10px;">
                        Creating technical design → Generating code → Packaging files
                    </p>
                </div>

                <div id="error" class="error"></div>
            </div>
        </div>

        <script>
            document.getElementById('mvpForm').addEventListener('submit', async (e) => {
                e.preventDefault();

                const jobDescription = document.getElementById('jobDescription').value;
                const projectName = document.getElementById('projectName').value || 'Generated MVP';
                const loadingEl = document.getElementById('loading');
                const errorEl = document.getElementById('error');
                const generateBtn = document.getElementById('generateBtn');

                // Show loading state
                loadingEl.classList.add('active');
                errorEl.classList.remove('active');
                generateBtn.disabled = true;
                generateBtn.textContent = 'Generating...';

                try {
                    const response = await fetch('/generate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            job_description: jobDescription,
                            project_name: projectName
                        })
                    });

                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Failed to generate MVP');
                    }

                    // Download the ZIP file
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `${projectName.replace(/\s+/g, '-')}-mvp.zip`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);

                    // Reset form
                    document.getElementById('mvpForm').reset();

                } catch (error) {
                    errorEl.textContent = `Error: ${error.message}`;
                    errorEl.classList.add('active');
                } finally {
                    loadingEl.classList.remove('active');
                    generateBtn.disabled = false;
                    generateBtn.textContent = 'Generate MVP';
                }
            });
        </script>
    </body>
    </html>
    """


@app.post("/generate")
async def generate_mvp(request: JobDescriptionRequest):
    """
    Generate an MVP from a job description.

    Process:
    1. Run architect to create TDD
    2. Run dev_team to generate code
    3. Package everything as a ZIP
    4. Return ZIP for download
    """
    try:
        # Create a temporary directory for this generation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            print(f"[MVP Generator] Starting generation for: {request.project_name}")

            # Step 1: Generate TDD with architect
            print("[1/3] Running architect to create Technical Design Document...")
            architect_state = run_architect_session(
                goal=request.job_description,
                is_job_description=True
            )

            tdd_content = architect_state['design_document']
            project_title = architect_state.get('project_title', request.project_name)
            project_type = architect_state.get('project_type', 'web_app')  # Get project type from architect
            
            print(f"[Architect] Detected project type: {project_type}")

            # Save TDD to temp file
            tdd_file = temp_path / "technical_design.md"
            with open(tdd_file, 'w', encoding='utf-8') as f:
                f.write("# Technical Design Document\n\n")
                f.write(f"**Project:** {project_title}\n\n")
                f.write(tdd_content)

            print(f"[2/3] TDD created ({len(tdd_content)} chars)")

            # Step 2: Generate code with dev_team
            print("[2/3] Running dev_team to generate code...")
            output_dir = temp_path / "generated_project"

            # Pass project_type to dev_team
            result = run_dev_team_v2(
                tdd_content=tdd_content,
                output_directory=str(output_dir),
                implementation_phase=1,
                feature_request=request.job_description[:500],  # Pass original job description as context
                project_type=project_type  # Pass detected project type
            )

            print(f"[3/3] Generated {result.get('files_written', 0)} files")

            # Step 3: Create ZIP file
            print("[3/3] Packaging files as ZIP...")
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add TDD
                zip_file.writestr('TECHNICAL_DESIGN.md', tdd_content)

                # Add all generated files
                if output_dir.exists():
                    for file_path in output_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = str(file_path.relative_to(output_dir))
                            zip_file.write(file_path, arcname)

            # Reset buffer position
            zip_buffer.seek(0)

            print("[MVP Generator] ✅ Complete! Sending ZIP file...")

            # Return ZIP file for download
            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename={project_title.replace(' ', '-')}-mvp.zip"
                }
            )

    except Exception as e:
        print(f"[MVP Generator] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "MVP Generator"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )