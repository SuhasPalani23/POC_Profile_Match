from flask import Blueprint, request, jsonify, send_file
from models.user import User
from routes.auth import token_required
from services.ats_service import ATSService
from services.vector_service import VectorService
from services.websocket_service import ws_service
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId
from config import Config
import gridfs
import tempfile
import os
import io
import threading

profile_bp = Blueprint("profile", __name__)
ats_service = ATSService()
vector_service = VectorService()

# GridFS — same MongoDB the rest of the app uses
_client = MongoClient(Config.MONGODB_URI)
_db = _client[Config.DB_NAME]
fs = gridfs.GridFS(_db)

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ------------------------------------------------------------------
# Background: push updated vector to Pinecone
# ------------------------------------------------------------------

def _upsert_user_vector_bg(user_id: str):
    try:
        user = User.find_by_id(user_id)
        if user:
            ok = vector_service.upsert_user(user)
            status = "completed" if ok else "failed"
        else:
            status = "failed"
        ws_service.emit_vector_update(user_id, status)
    except Exception as e:
        print(f"[profile] Vector upsert error: {e}")
        ws_service.emit_vector_update(user_id, "failed")


def _start_vector_upsert(user_id: str):
    t = threading.Thread(target=_upsert_user_vector_bg, args=(user_id,), daemon=True)
    t.start()


# ------------------------------------------------------------------
# GET /profile/me
# ------------------------------------------------------------------

@profile_bp.route("/me", methods=["GET"])
@token_required
def get_profile(current_user):
    current_user.pop("password", None)
    return jsonify({"user": current_user}), 200


# ------------------------------------------------------------------
# PUT /profile/update
# ------------------------------------------------------------------

@profile_bp.route("/update", methods=["PUT"])
@token_required
def update_profile(current_user):
    data = request.get_json()

    allowed = [
        "name", "bio", "skills", "linkedin",
        "professional_title", "experience_years", "location",
    ]
    update_fields = {k: data[k] for k in allowed if k in data}

    if "experience_years" in update_fields:
        update_fields["experience_years"] = int(update_fields["experience_years"])

    if not update_fields:
        return jsonify({"error": "No valid fields to update"}), 400

    success = User.update_profile(current_user["_id"], update_fields)
    if not success:
        return jsonify({"error": "Failed to update profile"}), 500

    updated_user = User.find_by_id(current_user["_id"])
    updated_user.pop("password", None)

    _start_vector_upsert(current_user["_id"])

    ws_service.emit_profile_update(current_user["_id"], {
        "message": "Profile updated successfully",
        "updated_fields": list(update_fields.keys()),
    })

    return jsonify({
        "message": "Profile updated successfully",
        "user": updated_user,
        "vector_update_initiated": True,
    }), 200


# ------------------------------------------------------------------
# POST /profile/upload-resume
# ------------------------------------------------------------------

@profile_bp.route("/upload-resume", methods=["POST"])
@token_required
def upload_resume(current_user):
    """
    Upload flow:
    1. Read file bytes from request
    2. Delete old GridFS file if exists
    3. Store new file in GridFS (MongoDB) → file_id
    4. Write bytes to temp file for parsing
    5. Gemini LLM analysis: skills, experience, summary
    6. Store resume_text + file_id on user document in MongoDB
    7. Upsert Pinecone vector in background (includes resume_text)
    8. Delete temp file

    The file binary lives in MongoDB GridFS — shared across
    every developer and every server using the same database.
    """
    if "resume" not in request.files:
        return jsonify({"error": "No resume file provided"}), 400

    file = request.files["resume"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF and DOCX files are allowed"}), 400

    # Check size (10MB limit)
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > 10 * 1024 * 1024:
        return jsonify({"error": "File size must be less than 10MB"}), 400

    filename = secure_filename(f"{current_user['_id']}_{file.filename}")
    content_type = file.content_type or "application/octet-stream"
    file_bytes = file.read()

    # Delete previous GridFS file so we don't accumulate old resumes
    old_file_id = current_user.get("resume_file_id")
    if old_file_id:
        try:
            fs.delete(ObjectId(old_file_id))
            print(f"[profile] Deleted old GridFS file {old_file_id}")
        except Exception as e:
            print(f"[profile] Could not delete old GridFS file: {e}")

    # Store in GridFS
    file_id = fs.put(
        file_bytes,
        filename=filename,
        content_type=content_type,
        user_id=str(current_user["_id"]),
    )
    print(f"[profile] Stored resume in GridFS with id: {file_id}")

    # Write to temp file for parsing (temp file is local, deleted right after)
    suffix = ".pdf" if filename.lower().endswith(".pdf") else ".docx"
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        # Full LLM analysis via Gemini
        analysis = ats_service.comprehensive_profile_analysis(current_user, tmp_path)

    except Exception as e:
        return jsonify({"error": f"Failed to analyse resume: {str(e)}"}), 500

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # Update user document in MongoDB
    update_data = {
        "resume_file_id": str(file_id),
        "resume": filename,          # display name only
        "resume_parsed": True,
        "resume_text": analysis.get("resume_text", ""),  # full text for ATS + Pinecone
    }

    if analysis.get("merged_skills"):
        update_data["skills"] = analysis["merged_skills"]

    extracted_exp = (
        analysis.get("ai_insights", {}).get("experience_years", 0)
        or analysis.get("resume_analysis", {}).get("estimated_experience", 0)
    )
    if extracted_exp and extracted_exp > current_user.get("experience_years", 0):
        update_data["experience_years"] = extracted_exp

    User.update_profile(current_user["_id"], update_data)

    # Pinecone upsert in background (vector now includes full resume text)
    _start_vector_upsert(current_user["_id"])

    updated_user = User.find_by_id(current_user["_id"])
    updated_user.pop("password", None)

    return jsonify({
        "message": "Resume uploaded and analysed successfully",
        "analysis": analysis,
        "user": updated_user,
        "vector_update_initiated": True,
    }), 200


# ------------------------------------------------------------------
# GET /profile/resume/<user_id>
# ------------------------------------------------------------------

@profile_bp.route("/resume/<user_id>", methods=["GET"])
@token_required
def get_resume(current_user, user_id):
    """
    Serve a user's resume file directly from GridFS.
    Works on any developer's machine — file is in MongoDB, not local disk.
    Founders can use this to download candidate resumes.
    """
    target_user = User.find_by_id(user_id)
    if not target_user:
        return jsonify({"error": "User not found"}), 404

    file_id = target_user.get("resume_file_id")
    if not file_id:
        return jsonify({"error": "No resume uploaded for this user"}), 404

    try:
        grid_out = fs.get(ObjectId(file_id))
        return send_file(
            io.BytesIO(grid_out.read()),
            mimetype=grid_out.content_type or "application/pdf",
            download_name=grid_out.filename,
            as_attachment=True,
        )
    except gridfs.errors.NoFile:
        return jsonify({"error": "Resume file not found in storage"}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve resume: {str(e)}"}), 500


# ------------------------------------------------------------------
# DELETE /profile/delete-resume
# ------------------------------------------------------------------

@profile_bp.route("/delete-resume", methods=["DELETE"])
@token_required
def delete_resume(current_user):
    """
    Delete resume from GridFS and clear all resume fields on the user doc.
    Re-indexes in Pinecone so the vector no longer reflects resume content.
    """
    if not current_user.get("resume_file_id") and not current_user.get("resume"):
        return jsonify({"error": "No resume to delete"}), 404

    file_id = current_user.get("resume_file_id")
    if file_id:
        try:
            fs.delete(ObjectId(file_id))
            print(f"[profile] Deleted GridFS file {file_id}")
        except Exception as e:
            print(f"[profile] GridFS delete error: {e}")

    User.update_profile(current_user["_id"], {
        "resume": "",
        "resume_file_id": None,
        "resume_parsed": False,
        "resume_text": "",
    })

    _start_vector_upsert(current_user["_id"])

    return jsonify({
        "message": "Resume deleted successfully",
        "vector_update_initiated": True,
    }), 200


# ------------------------------------------------------------------
# GET /profile/ats-score/<project_id>
# ------------------------------------------------------------------

@profile_bp.route("/ats-score/<project_id>", methods=["GET"])
@token_required
def calculate_ats_score(current_user, project_id):
    """
    LLM-driven ATS score against a project.

    Reads only from MongoDB fields — no file I/O, no GridFS read needed here.
    resume_text was stored in MongoDB at upload time so it is always available
    regardless of which developer's machine is handling this request.
    """
    from models.project import Project

    project = Project.find_by_id(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    user_text_parts = [
        f"Name: {current_user.get('name', '')}",
        f"Title: {current_user.get('professional_title', '')}",
        f"Bio: {current_user.get('bio', '')}",
        f"Skills: {', '.join(current_user.get('skills', []))}",
        f"Experience: {current_user.get('experience_years', 0)} years",
        f"Location: {current_user.get('location', '')}",
    ]

    if current_user.get("resume_text"):
        user_text_parts.append(f"Resume:\n{current_user['resume_text'][:3000]}")

    candidate_text = "\n".join(filter(None, user_text_parts))

    score_data = ats_service.calculate_ats_score(candidate_text, project["description"])
    tips = ats_service.generate_profile_optimization_tips(candidate_text, project["description"])

    result = {
        "project_id": project_id,
        "project_title": project["title"],
        "ats_score": score_data,
        "optimization_tips": tips,
    }

    ws_service.emit_ats_score_update(current_user["_id"], result)
    return jsonify(result), 200


# ------------------------------------------------------------------
# POST /profile/analyze-resume
# ------------------------------------------------------------------

@profile_bp.route("/analyze-resume", methods=["POST"])
@token_required
def analyze_current_resume(current_user):
    """
    Re-run LLM analysis on the stored resume.
    Reads from GridFS first (shared), falls back to stored resume_text.
    """
    file_id = current_user.get("resume_file_id")
    resume_text_stored = current_user.get("resume_text", "")

    if not file_id and not resume_text_stored:
        return jsonify({"error": "No resume uploaded"}), 404

    tmp_path = None
    try:
        if file_id:
            try:
                grid_out = fs.get(ObjectId(file_id))
                file_bytes = grid_out.read()
                filename = grid_out.filename or "resume.pdf"
                suffix = ".pdf" if filename.lower().endswith(".pdf") else ".docx"

                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name

                analysis = ats_service.comprehensive_profile_analysis(current_user, tmp_path)

            except gridfs.errors.NoFile:
                # GridFS file gone but text is in MongoDB — use it
                if not resume_text_stored:
                    return jsonify({"error": "Resume file not found in storage"}), 404
                ai_insights = ats_service.analyze_resume_with_ai(resume_text_stored)
                analysis = {"ai_insights": ai_insights, "resume_text": resume_text_stored}
        else:
            ai_insights = ats_service.analyze_resume_with_ai(resume_text_stored)
            analysis = {"ai_insights": ai_insights, "resume_text": resume_text_stored}

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return jsonify({
        "message": "Resume analysed successfully",
        "analysis": analysis,
    }), 200


# ------------------------------------------------------------------
# POST /profile/skills-suggestions
# ------------------------------------------------------------------

@profile_bp.route("/skills-suggestions", methods=["POST"])
@token_required
def get_skills_suggestions(current_user):
    """LLM-powered skill gap suggestions based on current profile."""
    data = request.get_json()
    target_role = data.get("target_role", current_user.get("professional_title", ""))

    prompt = f"""
Based on this professional profile, suggest 10-15 relevant skills to add.

Current profile:
- Name: {current_user.get('name', '')}
- Bio: {current_user.get('bio', '')}
- Current Skills: {', '.join(current_user.get('skills', []))}
- Experience: {current_user.get('experience_years', 0)} years
- Target Role: {target_role}

Consider industry trends, complementary skills, and gaps common for this career path.

Respond ONLY with valid JSON — no markdown fences:
{{
    "suggested_skills": ["skill1", "skill2", ...],
    "reasoning": "brief explanation"
}}
"""
    try:
        response = ats_service.gemini_service.client.models.generate_content(
            model=ats_service.gemini_service.model,
            contents=prompt,
        )
        result = ats_service.gemini_service._extract_json(response.text)
        return jsonify(result if result else {"suggested_skills": []}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500