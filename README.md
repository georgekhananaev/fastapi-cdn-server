# FastApi CDN Server
This FastAPI application serves as an efficient image caching and resizing server. It allows users to cache images from external URLs, automatically resizing them into three predefined sizes (small, medium, and large). The application integrates Redis, a powerful in-memory database, to manage the caching mechanism effectively.

Upon receiving a request with a URL, the server fetches the image, processes it, and stores resized versions in a local cache directory. It also tracks the last access time of each file using Redis, employing a key-value pair for quick lookup. The system is designed to automatically delete files that have not been accessed for a certain number of days, ensuring efficient use of storage space.

The application also provides flexibility in handling images that already exist in the cache. Users can choose whether to overwrite these images or leave them as they are, based on a boolean parameter in the request. All of these features are exposed through a simple and intuitive API, making it easy to integrate with web applications, content management systems, or any platform that requires dynamic image resizing and caching.

## Getting Started (Manual Installation)

1. **Clone the repository or copy the FastAPI code into a directory.**

    ```bash
    git clone https://github.com/your/repo.git
    cd fastapi-cdn-server
    ```

2. **Create a `.env` file in the same directory as the FastAPI code with the following content:**

    ```plaintext
    bearer_secret_key=your_bearer_secret_key
    swagger_ui_username=your_swagger_ui_username
    swagger_ui_password=your_swagger_ui_password
    ```

3. **Install <a href="https://redis.io/download/" target="_blank">Redis</a> or <a href="https://www.dragonflydb.io/" target="_blank">Dragonfly</a>, server for caching.**

4. **Install the required Python packages using pip:**

    ```bash
    pip install -r requirements.txt
    ```

5. **Run the FastAPI server using uvicorn:**

    ```bash
    uvicorn app:main --host 0.0.0.0 --port 8080 --reload
    ```

## Automatic Installation (Docker)

1. **Build the Docker images:**

    ```bash
    docker-compose build --no-cache
    ```

2. **Run the Docker containers:**

    ```bash
    docker-compose up
    ```
   or 
	```bash
    docker-compose up -d
    ```
## Implementations
**Check the folder usage-examples with frontend demos**
- Added a React example.

## Notes

- The server is configured to use Redis for caching, otherwise files will be stored locally.

- Adjust the CORS settings in the FastAPI code (`origins` variable) if needed.

- Other settings can be configured by editing config.py

- The server will automatically clear expired files from the cache.

- Swagger UI URL: http://localhost:8000/docs

## Contributing

If you'd like to contribute to this project, please let me know.

## License

This project is licensed under the [MIT License](LICENSE).


