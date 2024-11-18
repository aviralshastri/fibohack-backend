from functions import generate_unique_filename, generate_unique_folder, add_new_post_mysql,get_thumbnail, update_post_mysql,delete_post_mysql,get_post_mysql
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import mimetypes
from typing import Dict, Optional
import os
import json
import logging
import shutil
import base64


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

        thumbnail_id = generate_unique_filename(thumbnails_dir)
        thumbnail_path = os.path.join(thumbnails_dir, thumbnail_id)
        logger.info(f"Saving thumbnail to: {thumbnail_path}")
        
        try:
            thumbnail_content = await thumbnail.read()
            with open(thumbnail_path+"."+thumbnail.filename.split(".")[1], "wb") as f:
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
    
    if field not in ["banner", "thumbnails", "video", "markdown"]:
        if value is None:
            raise HTTPException(status_code=400, detail="Value is required for non-file fields")
        update_post_mysql(post_id=post_id, post_type=post_type, key=field, value=value)
        return {"message": f"Updated {field} successfully"}
    
    elif banner or thumbnail or markdown or video :
        base_dir = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
        
        if field == "thumbnails" and thumbnail:
            thumbnail_filename = get_thumbnail(post_id=post_id, post_type=post_type)
            if not thumbnail_filename:
                raise HTTPException(status_code=404, detail="Existing thumbnail not found in database")
            
            thumbnails_dir = os.path.join(base_dir, "thumbnails")
            os.makedirs(thumbnails_dir, exist_ok=True)

            new_ext = os.path.splitext(thumbnail.filename)[1]
            if not new_ext:
                content_type = thumbnail.content_type
                ext = mimetypes.guess_extension(content_type)
                new_ext = ext if ext else '.unknown'
            
            new_filename = f"{thumbnail_filename}{new_ext}"
            new_file_path = os.path.join(thumbnails_dir, new_filename)
            
            try:
                for file in os.listdir(thumbnails_dir):
                    if file.startswith(f"{thumbnail_filename}."):
                        os.remove(os.path.join(thumbnails_dir, file))
                
                with open(new_file_path, "wb") as buffer:
                    shutil.copyfileobj(thumbnail.file, buffer)
                
                update_post_mysql(
                    post_id=post_id,
                    post_type=post_type,
                )
                
                return {
                    "message": "Thumbnail updated successfully",
                    "filename": new_filename
                }
                
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error updating thumbnail: {str(e)}"
                )
                
        elif field == "banner" and banner:
            banner_dir = os.path.join(base_dir, post_type, post_id)
            os.makedirs(banner_dir, exist_ok=True)
            
            try:
                new_ext = os.path.splitext(banner.filename)[1]
                if not new_ext:
                    content_type = banner.content_type
                    ext = mimetypes.guess_extension(content_type)
                    new_ext = ext if ext else '.unknown'
                
                for file in os.listdir(banner_dir):
                    if file.startswith("banner."):
                        os.remove(os.path.join(banner_dir, file))
                
                new_filename = f"banner{new_ext}"
                new_file_path = os.path.join(banner_dir, new_filename)
                
                with open(new_file_path, "wb") as buffer:
                    shutil.copyfileobj(banner.file, buffer)
                
                update_post_mysql(
                    post_id=post_id,
                    post_type=post_type,
                )
                
                return {
                    "message": "Banner updated successfully",
                    "filename": new_filename
                }
                
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error updating banner: {str(e)}"
                )
                
        elif field == "video" and video:
            video_dir = os.path.join(base_dir, post_type, post_id)
            os.makedirs(video_dir, exist_ok=True)
            
            try:
                new_ext = os.path.splitext(video.filename)[1]
                if not new_ext:
                    content_type = video.content_type
                    ext = mimetypes.guess_extension(content_type)
                    new_ext = ext if ext else '.unknown'
                
                for file in os.listdir(video_dir):
                    if file.startswith("video."):
                        os.remove(os.path.join(video_dir, file))
                
                new_filename = f"video{new_ext}"
                new_file_path = os.path.join(video_dir, new_filename)
                
                with open(new_file_path, "wb") as buffer:
                    shutil.copyfileobj(video.file, buffer)
                
                update_post_mysql(
                    post_id=post_id,
                    post_type=post_type,
                )
                
                return {
                    "message": "Video updated successfully",
                    "filename": new_filename
                }
                
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error updating video: {str(e)}"
                )
                
        elif field == "markdown" and markdown:
            markdown_dir = os.path.join(base_dir, post_type, post_id)
            os.makedirs(markdown_dir, exist_ok=True)
            
            try:
                new_ext = os.path.splitext(markdown.filename)[1]
                if not new_ext:
                    content_type = markdown.content_type
                    ext = mimetypes.guess_extension(content_type)
                    new_ext = ext if ext else '.md'
                
                for file in os.listdir(markdown_dir):
                    if file.startswith("markdown."):
                        os.remove(os.path.join(markdown_dir, file))

                new_filename = f"markdown{new_ext}"
                new_file_path = os.path.join(markdown_dir, new_filename)
                
                with open(new_file_path, "wb") as buffer:
                    shutil.copyfileobj(markdown.file, buffer)
                    
                update_post_mysql(
                    post_id=post_id,
                    post_type=post_type,
                )
                
                return {
                    "message": "Markdown updated successfully",
                    "filename": new_filename
                }
                
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error updating markdown: {str(e)}"
                )
        else:
            raise HTTPException(status_code=400, detail="Invalid field or missing file")
        
    else:
        raise HTTPException(status_code=400, detail=f"No {field} file provided")


@app.delete("/delete-post/{post_type}/{post_id}")
async def delete_post(
    post_id: str,
    post_type: str
):
    if not post_id:
        return {"error": "Post ID is required"}
    if not post_type:
        return {"error": "Post type is required"}
    
    try:
        base_dir = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
        main_dir = os.path.join(base_dir, post_type)
        thumbnail_id = get_thumbnail(post_id=post_id, post_type=post_type)
        if thumbnail_id:
            thumbnail_dir = os.path.join(base_dir, "thumbnails")
            for file in os.listdir(thumbnail_dir):
                if os.path.splitext(file)[0] == thumbnail_id:
                    file_path = os.path.join(thumbnail_dir, file)
                    os.remove(file_path)
                    print(f"Deleted thumbnail file: {file_path}")
                    break
        post_dir = os.path.join(main_dir, post_id)
        if os.path.exists(post_dir) and os.path.isdir(post_dir):
            shutil.rmtree(post_dir)
            print(f"Deleted folder: {post_dir}")
        
        delete_post_mysql(post_id=post_id,thumbnail_id=thumbnail_id,post_type=post_type)
        
        return {"status": "Success", "message": "Post and related resources deleted"}
    
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "Error", "message": str(e)}
    

@app.get("/get-posts/{post_type}")
async def get_posts(post_type: str, offset_upper: int, offset_lower: int):
    def remove_key_from_dict_list(dict_list, key_to_remove):
        return [{key: value for key, value in d.items() if key != key_to_remove} for d in dict_list]
    
    data = get_post_mysql(post_type=post_type, offset_lower=offset_lower, offset_upper=offset_upper)
    
    base_dir = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
    thumbnail_dir = os.path.join(base_dir, "thumbnails")
    
    column_names = ['id', 'description', 'title', 'thumbnail', 'author', 'created_at', 'updated_at']
    
    structured_data = []
    for row in data:
        post_dict = {column_names[i]: row[i] for i in range(len(column_names))}
        
        post_dict['thumbnail_file'] = None
        if post_dict['thumbnail']:
            thumbnail_prefix = post_dict['thumbnail']
            thumbnail_files = os.listdir(thumbnail_dir)
            matching_file = next(
                (f for f in thumbnail_files if f.startswith(thumbnail_prefix)),
                None
            )
            if matching_file:
                # Read and encode the thumbnail file
                file_path = os.path.join(thumbnail_dir, matching_file)
                try:
                    with open(file_path, 'rb') as file:
                        file_content = file.read()
                        # Convert binary data to base64 string
                        base64_encoded = base64.b64encode(file_content).decode('utf-8')
                        # Add file type information for proper frontend handling
                        file_extension = os.path.splitext(matching_file)[1].lower()
                        mime_type = {
                            '.jpg': 'image/jpeg',
                            '.jpeg': 'image/jpeg',
                            '.png': 'image/png',
                            '.gif': 'image/gif'
                        }.get(file_extension, 'application/octet-stream')
                        
                        post_dict['thumbnail_file'] = {
                            'data': base64_encoded,
                            'mime_type': mime_type,
                            'filename': matching_file
                        }
                except Exception as e:
                    print(f"Error reading thumbnail file: {e}")
                    post_dict['thumbnail_file'] = None
        
        structured_data.append(post_dict)
    
    structured_data = remove_key_from_dict_list(structured_data, "thumbnail")
    return structured_data