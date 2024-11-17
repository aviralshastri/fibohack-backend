from functions import generate_unique_filename, generate_unique_folder, add_new_post_mysql, create_folder,update_post_mysql,delete_post
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional
import os
import json
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def ensure_upload_dirs(post_type):
    """Create necessary upload directories if they don't exist"""
    
    if post_type=="articles":
        base_dir = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
        thumbnails_dir = os.path.join(base_dir, "thumbnails")
        articles_dir = os.path.join(base_dir, "articles")
        
        os.makedirs(thumbnails_dir, exist_ok=True)
        os.makedirs(articles_dir, exist_ok=True)
        
        return base_dir, thumbnails_dir, articles_dir
    
    elif post_type=="guides":
        base_dir = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
        thumbnails_dir = os.path.join(base_dir, "thumbnails")
        guides_dir = os.path.join(base_dir, "guides")
        
        os.makedirs(thumbnails_dir, exist_ok=True)
        os.makedirs(guides_dir, exist_ok=True)
        
        return base_dir, thumbnails_dir, guides_dir
    
    elif post_type=="tutorials":
        base_dir = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
        thumbnails_dir = os.path.join(base_dir, "thumbnails")
        tutorials_dir = os.path.join(base_dir, "tutorials")
        
        os.makedirs(thumbnails_dir, exist_ok=True)
        os.makedirs(tutorials_dir, exist_ok=True)
        
        return base_dir, thumbnails_dir, tutorials_dir

@app.post("/upload-post/{post_type}")
async def upload_post(
    post_type: str,
    thumbnail: UploadFile = File(...),
    markdown: UploadFile = File(...),
    text_data: str = Form(...),
    banner: UploadFile = File(None),
    video: UploadFile = File(None)
):
    """
    Unified handler for uploading different types of posts (articles, guides, tutorials)
    """
    valid_post_types = {"articles", "guides", "tutorials"}
    if post_type not in valid_post_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid post type. Must be one of: {', '.join(valid_post_types)}"
        )

    try:
        base_dir, thumbnails_dir, content_dir = ensure_upload_dirs(post_type)
        logger.info(f"Upload directories created/verified at {base_dir}")

        try:
            text_data_dict = json.loads(text_data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            raise HTTPException(status_code=422, detail="Invalid JSON format in text_data")

        required_fields = ['title', 'description', 'author']
        for field in required_fields:
            if field not in text_data_dict:
                raise HTTPException(status_code=422, detail=f"Missing required field: {field}")

        if post_type in ["articles", "guides"] and not banner:
            raise HTTPException(status_code=400, detail="Banner image is required for articles and guides")
        if post_type == "tutorials" and not video:
            raise HTTPException(status_code=400, detail="Video file is required for tutorials")

        unique_folder_name = generate_unique_folder(content_dir)
        post_folder_path = os.path.join(content_dir, unique_folder_name)
        os.makedirs(post_folder_path, exist_ok=True)
        logger.info(f"Created post folder: {post_folder_path}")

        thumbnail_id = generate_unique_filename(thumbnails_dir, thumbnail.filename)
        thumbnail_path = os.path.join(thumbnails_dir, thumbnail_id)
        logger.info(f"Saving thumbnail to: {thumbnail_path}")
        
        try:
            thumbnail_content = await thumbnail.read()
            with open(thumbnail_path, "wb") as f:
                f.write(thumbnail_content)
            logger.info(f"Thumbnail saved successfully: {len(thumbnail_content)} bytes")
        except Exception as e:
            logger.error(f"Error saving thumbnail: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error saving thumbnail: {str(e)}")

        media_path = None
        if post_type in ["articles", "guides"] and banner:
            banner_ext = os.path.splitext(banner.filename)[1]
            media_filename = f"banner{banner_ext}"
            media_path = os.path.join(post_folder_path, media_filename)
            media_content = await banner.read()
            media_type = "banner"
        elif post_type == "tutorials" and video:
            video_ext = os.path.splitext(video.filename)[1]
            media_filename = f"video{video_ext}"
            media_path = os.path.join(post_folder_path, media_filename)
            media_content = await video.read()
            media_type = "video"

        if media_path:
            try:
                with open(media_path, "wb") as f:
                    f.write(media_content)
                logger.info(f"{media_type.capitalize()} saved successfully: {len(media_content)} bytes")
            except Exception as e:
                logger.error(f"Error saving {media_type}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error saving {media_type}: {str(e)}")

        markdown_path = os.path.join(post_folder_path, "markdown.md")
        logger.info(f"Saving markdown to: {markdown_path}")
        
        try:
            markdown_content = await markdown.read()
            with open(markdown_path, "wb") as f:
                f.write(markdown_content)
            logger.info(f"Markdown saved successfully: {len(markdown_content)} bytes")
        except Exception as e:
            logger.error(f"Error saving markdown: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error saving markdown: {str(e)}")

        try:
            add_new_post_mysql(
                title=text_data_dict["title"],
                thumbnail=thumbnail_id,
                description=text_data_dict["description"],
                author=text_data_dict["author"],
                id=unique_folder_name,
                post_type=post_type
            )
            logger.info(f"{post_type.capitalize()} added to database successfully")
        except Exception as e:
            logger.error(f"Error adding {post_type} to database: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        response = {
            "message": f"{post_type.capitalize()} uploaded successfully",
            f"{post_type}_id": unique_folder_name,
            "paths": {
                "thumbnail": thumbnail_path,
                "markdown": markdown_path
            }
        }
        
        if media_path:
            response["paths"][media_type] = media_path

        return response

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
    
@app.post("/update-post/{post_type}/{field}/{post_id}")
async def update_post(
    post_type: str,
    field: str,
    post_id: str,
    value: Optional[str] = None,
    thumbnail: Optional[UploadFile] = File(None),
    banner: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    markdown: Optional[UploadFile] = File(None)
):
    print(f"Post type received: {post_type}")
    
    if field not in ["banner", "thumbnail", "video", "markdown"]:
        if value is None:
            raise HTTPException(status_code=400, detail="Value is required for non-file fields")
        update_post_mysql(post_id=post_id, post_type=post_type, key=field, value=value)
        return {"message": f"Updated {field} successfully"}
    
    # Handle file uploads
    file_mapping = {
        "thumbnail": thumbnail,
        "banner": banner,
        "markdown": markdown,
        "video": video
    }
    
    uploaded_file = file_mapping.get(field)
    if uploaded_file is None:
        raise HTTPException(status_code=400, detail=f"No {field} file provided")
        
    # Process the file
    try:
        # Here you would add your file processing logic
        print(f"{field.capitalize()} received")
        return {"message": f"{field.capitalize()} received", "post_type": post_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing {field}: {str(e)}")
