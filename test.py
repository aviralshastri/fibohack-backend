import requests
import os

def test_update_post_thumbnail():
    print("\nTesting thumbnail upload...")
    print("-" * 50)
    
    # Note the hyphen instead of underscore in the URL
    url = "http://localhost:8000/update-post/thumn/thumbnail/gafdsaerw"
    
    test_file_path = "web_tester.html"
    if not os.path.exists(test_file_path):
        print(f"Error: {test_file_path} not found in the current directory!")
        return
    
    try:
        with open(test_file_path, "rb") as thumb_file:
            files = {
                "thumbnail": (test_file_path, thumb_file, "text/html")  # Updated MIME type
            }
            
            # Send POST request with the file
            response = requests.post(url, files=files)
            
            print(f"Status Code: {response.status_code}")
            print("Response:", end=" ")
            try:
                print(response.json())
            except requests.exceptions.JSONDecodeError:
                print(response.text)
            
            if response.status_code == 200:
                print("Thumbnail test completed successfully! ✅")
            else:
                print("Thumbnail test failed! ❌")
                
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure your FastAPI server is running.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    print("Running tests for update_post endpoint...")
    test_update_post_thumbnail()