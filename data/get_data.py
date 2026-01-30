import kagglehub

# Download latest version
path = kagglehub.dataset_download("mlvprasad/indian-unicorn-startups-2023-june-updated")

print("Path to dataset files:", path)