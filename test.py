import requests

# URL of your FastAPI server (assuming it's running locally)
url = "http://127.0.0.1:8000/get-posts/{post_type}"

# Set the post_type, offset_upper, and offset_lower parameters
post_type = "articles"  # Example post type (could be 'guides', 'tutorials', etc.)
offset_upper = 100      # Upper limit for pagination
offset_lower = 0        # Lower limit for pagination

# Format the URL with the specific post_type
formatted_url = url.format(post_type=post_type)

# Send a GET request to the FastAPI endpoint with query parameters
response = requests.get(formatted_url, params={'offset_upper': offset_upper, 'offset_lower': offset_lower})

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Print the response data (the list of posts)
    print("Response Data:", response.json())
else:
    # Print an error message if the request failed
    print(f"Request failed with status code: {response.status_code}")
